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


async def start_after_consent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Активирует ConversationHandler после принятия согласия через callback"""
    from src.infrastructure.database.repositories import UserRepository
    from src.infrastructure.database.base import async_session_maker
    from src.core.entities.user import User
    from datetime import datetime
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    try:
        # Сохраняем согласие в БД
        async with async_session_maker() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_user_id(user_id)
            
            if user:
                # Update existing user
                user.consent_given_at = datetime.utcnow()
                user.username = username
                await user_repo.update(user)
            else:
                # Create new user
                new_user = User(
                    user_id=user_id,
                    username=username,
                    consent_given_at=datetime.utcnow()
                )
                await user_repo.create(new_user)
            
            await session.commit()
        
        # Показываем welcome message
        await update.callback_query.answer("✅ Согласие принято")
        await show_welcome_message(update, context)
        
        # Возвращаем состояние WAITING_PHONE, чтобы активировать ConversationHandler
        return WAITING_PHONE
        
    except Exception as e:
        print(f"Error in start_after_consent: {e}")
        import traceback
        traceback.print_exc()
        await update.callback_query.answer("❌ Произошла ошибка. Попробуйте снова.", show_alert=True)
        return ConversationHandler.END


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
    try:
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
            try:
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
            except Exception as payment_error:
                print(f"Error processing payment: {payment_error}")
                import traceback
                traceback.print_exc()
                await update.message.reply_text(
                    "❌ Произошла ошибка при создании платежа. Попробуйте позже."
                )
                return ConversationHandler.END
                
    except Exception as e:
        print(f"Error in handle_phone: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке запроса. Попробуйте позже."
        )
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END


def setup_handlers(application):
    """Setup all bot handlers"""
    # Conversation handler for main flow
    # Добавляем CallbackQueryHandler в entry_points, чтобы активировать ConversationHandler после согласия
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            # Обработчик для активации ConversationHandler после принятия согласия
            CallbackQueryHandler(start_after_consent, pattern="^accept_consent$")
        ],
        states={
            WAITING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)

