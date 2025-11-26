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
    user_id = update.effective_user.id if update.effective_user else None
    chat_id = update.effective_chat.id if update.effective_chat else None
    update_id = update.update_id
    print(f"[DEBUG] start() called: update_id={update_id}, user_id={user_id}, chat_id={chat_id}")
    
    # Check consent first
    has_consent = await check_consent(update, context)
    if not has_consent:
        print(f"[DEBUG] User {user_id} has no consent, returning END")
        return ConversationHandler.END
    
    # Show welcome message
    await show_welcome_message(update, context)
    print(f"[DEBUG] User {user_id} started conversation, returning WAITING_PHONE")
    return WAITING_PHONE


async def start_after_consent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Активирует ConversationHandler после принятия согласия через callback"""
    from src.infrastructure.database.repositories import UserRepository
    from src.infrastructure.database.base import async_session_maker
    from src.core.entities.user import User
    from datetime import datetime
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    print(f"[DEBUG] start_after_consent: user_id={user_id}, username={username}")
    
    try:
        # Сохраняем согласие в БД
        async with async_session_maker() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_user_id(user_id)
            print(f"[DEBUG] start_after_consent: existing user={user is not None}, user_id={user.id if user else None}")
            
            if user:
                # Update existing user
                print(f"[DEBUG] start_after_consent: updating existing user id={user.id}")
                user.consent_given_at = datetime.utcnow()
                user.username = username
                await user_repo.update(user)
                print(f"[DEBUG] start_after_consent: user updated successfully")
            else:
                # Create new user
                print(f"[DEBUG] start_after_consent: creating new user")
                new_user = User(
                    user_id=user_id,
                    username=username,
                    consent_given_at=datetime.utcnow()
                )
                created_user = await user_repo.create(new_user)
                print(f"[DEBUG] start_after_consent: new user created with id={created_user.id}")
            
            await session.commit()
            print(f"[DEBUG] start_after_consent: session committed")
        
        # Показываем welcome message
        await update.callback_query.answer("✅ Согласие принято")
        await show_welcome_message(update, context)
        
        # Возвращаем состояние WAITING_PHONE, чтобы активировать ConversationHandler
        print(f"[DEBUG] start_after_consent: returning WAITING_PHONE")
        return WAITING_PHONE
        
    except Exception as e:
        print(f"[ERROR] start_after_consent: exception for user_id={user_id}: {e}")
        import traceback
        traceback.print_exc()
        try:
            await update.callback_query.answer("❌ Произошла ошибка. Попробуйте снова.", show_alert=True)
        except Exception:
            pass
        return ConversationHandler.END


async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает сообщения от пользователей, которые не находятся в conversation.
    Просит их отправить /start для начала работы.
    """
    user_id = update.effective_user.id if update.effective_user else None
    print(f"[DEBUG] handle_unknown_message() called for user_id={user_id}")
    
    # Проверяем согласие
    has_consent = await check_consent(update, context)
    if not has_consent:
        # Если согласия нет, check_consent уже показал сообщение с согласием
        print(f"[DEBUG] User {user_id} has no consent in handle_unknown_message")
        return
    
    # Если согласие есть, но пользователь не в conversation, просим отправить /start
    await update.message.reply_text(
        "👋 Для начала работы отправьте команду /start"
    )


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input"""
    user_id = update.effective_user.id if update.effective_user else None
    print(f"[DEBUG] handle_phone() called for user_id={user_id}, state={context.user_data.get('state', 'unknown')}")
    
    # Check consent
    has_consent = await check_consent(update, context)
    if not has_consent:
        print(f"[DEBUG] User {user_id} has no consent in handle_phone, returning END")
        return ConversationHandler.END
    
    user_id = update.effective_user.id
    
    # Получаем текст сообщения
    if not update.message or not update.message.text:
        return WAITING_PHONE
    
    phone_text = update.message.text.strip()
    
    # Rate limiting check
    try:
        redis_client = RedisClient()
        rate_key = f"rate_limit:{user_id}"
        count = await redis_client.increment(
            rate_key, ex=settings.rate_limit_window
        )
        print(f"[DEBUG] handle_phone: rate limit check for user_id={user_id}, count={count}")
        
        if count > settings.rate_limit_requests:
            print(f"[DEBUG] handle_phone: rate limit exceeded for user_id={user_id}")
            await update.message.reply_text(
                "⛔ Превышен лимит запросов. Попробуйте позже."
            )
            return ConversationHandler.END
    except Exception as redis_error:
        print(f"[WARNING] handle_phone: Redis error for user_id={user_id}: {redis_error}")
        # Continue without rate limiting if Redis is unavailable
        import traceback
        traceback.print_exc()
    
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
                    
                    result_text = f"""✅ ДАННЫЕ ИЗ БАЗЫ FL0

📞 Номер: {phone_number}
📅 Следующая овуляция: {format_date_russian(calculated_date)}

🔄 Данные автоматически обновятся после этой даты"""
                    
                    await update.message.reply_text(result_text)
                    return ConversationHandler.END
            
            # No payment or expired, request payment
            try:
                print(f"[DEBUG] handle_phone: attempting to create payment for user_id={user_id}, phone={phone_number}")
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
                print(f"[DEBUG] handle_phone: payment created successfully for user_id={user_id}")
                return ConversationHandler.END
            except ValueError as config_error:
                # Configuration error - payment system not set up
                print(f"[ERROR] handle_phone: Payment system not configured: {config_error}")
                await update.message.reply_text(
                    "❌ Платежная система не настроена. Обратитесь к администратору."
                )
                return ConversationHandler.END
            except Exception as payment_error:
                print(f"[ERROR] handle_phone: Error processing payment for user_id={user_id}: {payment_error}")
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


async def log_all_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логирует все входящие обновления для отладки"""
    user_id = update.effective_user.id if update.effective_user else None
    chat_id = update.effective_chat.id if update.effective_chat else None
    update_id = update.update_id
    
    # Определяем тип обновления
    update_type = "unknown"
    text_preview = ""
    if update.message:
        update_type = "message"
        text_preview = update.message.text[:50] if update.message.text else 'no text'
    elif update.callback_query:
        update_type = "callback_query"
        text_preview = update.callback_query.data or 'no data'
    elif update.edited_message:
        update_type = "edited_message"
    
    print(f"[UPDATE] update_id={update_id}, user_id={user_id}, chat_id={chat_id}, type={update_type}, text='{text_preview}'")
    # Возвращаем None, чтобы не блокировать обработку другими handlers
    return None

async def log_callback_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логирует callback queries"""
    user_id = update.effective_user.id if update.effective_user else None
    data = update.callback_query.data if update.callback_query else None
    print(f"[UPDATE] callback_query: user_id={user_id}, data={data}")
    return None

def setup_handlers(application):
    """Setup all bot handlers"""
    print("[DEBUG] Setting up handlers...")
    
    # Добавляем handlers для логирования всех обновлений (самый первый, с низким приоритетом)
    # Эти handlers будут вызываться для всех обновлений, но не будут их обрабатывать
    log_message_handler = MessageHandler(filters.ALL, log_all_updates)
    log_callback_handler = CallbackQueryHandler(log_callback_queries)
    application.add_handler(log_message_handler, group=-1)  # Группа -1 = самый низкий приоритет
    application.add_handler(log_callback_handler, group=-1)
    
    # Conversation handler for main flow
    # КРИТИЧЕСКИ ВАЖНО: per_user=True изолирует состояние для каждого пользователя
    # per_chat=False, так как для ботов достаточно изоляции по пользователю
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            # Обработчик для активации ConversationHandler после принятия согласия через callback
            CallbackQueryHandler(start_after_consent, pattern="^accept_consent$"),
        ],
        states={
            WAITING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        # КРИТИЧЕСКИ ВАЖНО: per_user=True обеспечивает изоляцию состояний для каждого пользователя
        # Это позволяет нескольким пользователям работать одновременно
        per_user=True,
        per_chat=False,  # Для ботов достаточно изоляции по пользователю
        per_message=False,
        conversation_timeout=None,
        name="main_conversation",  # Явное имя для отладки
    )
    
    # Handler для сообщений от пользователей вне conversation
    # Обрабатывает только текстовые сообщения (не команды), которые не были обработаны ConversationHandler
    unknown_message_handler = MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_unknown_message
    )
    
    # ConversationHandler должен быть добавлен в группу 0 (по умолчанию)
    application.add_handler(conv_handler, group=0)
    # Затем добавляем unknown_message_handler в группу 1 - он будет обрабатывать только те сообщения,
    # которые не были обработаны ConversationHandler (т.е. от пользователей вне conversation)
    application.add_handler(unknown_message_handler, group=1)
    
    print(f"[DEBUG] Handlers setup complete. Total handlers: {len(application.handlers[0])}")

