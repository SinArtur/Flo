from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
)
from datetime import date
from src.core.entities.phone_number import PhoneNumber
from src.infrastructure.utils.date_formatter import format_date_russian
from src.core.entities.payment import PaymentStatus
from src.core.use_cases.calculate_ovulation_date import CalculateOvulationDateUseCase
from src.core.use_cases.process_payment import ProcessPaymentUseCase
from src.infrastructure.database.repositories import PaymentRepository, RequestRepository
from src.infrastructure.payment_gateway import YooKassaAdapter
from src.infrastructure.redis import RedisClient
from src.infrastructure.telegram_bot.consent_middleware import (
    check_consent,
    handle_consent_acceptance,
    show_welcome_message
)
from src.config.settings import settings

# Conversation states
WAITING_PHONE = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message - проверяет согласие перед показом"""
    # Check consent first
    has_consent = await check_consent(update, context)
    if not has_consent:
        return ConversationHandler.END
    
    # Show welcome message
    await show_welcome_message(update, context)
    return WAITING_PHONE


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input"""
    # Check consent
    has_consent = await check_consent(update, context)
    if not has_consent:
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    phone_text = update.message.text.strip()
    
    # Rate limiting check
    redis_client = RedisClient()
    rate_key = f"rate_limit:{user_id}"
    count = await redis_client.increment(
        rate_key, ex=settings.rate_limit_window
    )
    
    if count > settings.rate_limit_requests:
        await update.message.reply_text(
            "⛔ Превышен лимит запросов. Попробуйте позже."
        )
        return ConversationHandler.END
    
    # Validate phone number
    try:
        phone = PhoneNumber(phone_text)
        phone_number = phone.normalized()
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат номера.\n"
            "Используйте формат: +7XXXXXXXXXX"
        )
        return WAITING_PHONE
    
    # Get database session
    from src.infrastructure.database.base import async_session_maker
    async with async_session_maker() as session:
        payment_repo = PaymentRepository(session)
        request_repo = RequestRepository(session)
        
        # Check if user already has a successful payment for this phone
        existing_payment = await payment_repo.get_by_user_and_phone(
            user_id, phone_number, PaymentStatus.SUCCEEDED
        )
        
        if existing_payment:
            # Check if we have a request with valid date
            existing_request = await request_repo.get_by_user_and_phone(
                user_id, phone_number
            )
            
            if existing_request and existing_request.calculated_date:
                # Recalculate to check if date is still valid
                calculate_use_case = CalculateOvulationDateUseCase(request_repo)
                calculated_date, _ = await calculate_use_case.execute(
                    user_id, phone_number
                )
                
                result_text = f"""✅ ДАННЫЕ ИЗ БАЗЫ FLO

📞 Номер: {phone_number}
📅 Следующая овуляция: {format_date_russian(calculated_date)}

🔄 Данные автоматически обновятся после этой даты"""
                
                await update.message.reply_text(result_text)
                return ConversationHandler.END
        
        # No payment or expired, request payment
        payment_gateway = YooKassaAdapter()
        process_payment_use_case = ProcessPaymentUseCase(
            payment_repo, payment_gateway
        )
        
        payment, payment_url = await process_payment_use_case.execute(
            user_id, phone_number
        )
        
        keyboard = [
            [InlineKeyboardButton("💳 Оплатить", url=payment_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        payment_text = f"""📞 Получен номер: {phone_number}

⚠️ Для доступа к данным требуется оплата
Сумма: 50 руб.

Оплатите по ссылке ниже:"""
        
        await update.message.reply_text(
            payment_text, reply_markup=reply_markup
        )
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END


def setup_handlers(application):
    """Setup all bot handlers"""
    # Handler for consent acceptance
    application.add_handler(
        CallbackQueryHandler(handle_consent_acceptance, pattern="^accept_consent$")
    )
    
    # Conversation handler for main flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)

