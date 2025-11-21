from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from datetime import datetime
from typing import Optional
from src.infrastructure.database.repositories import UserRepository
from src.infrastructure.database.base import async_session_maker
from src.core.entities.user import User
from src.config.settings import settings


async def check_consent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Проверяет наличие согласия пользователя.
    Если согласия нет - показывает сообщение с согласием.
    Returns True if consent is given, False otherwise.
    """
    if not update.effective_user:
        return False
    
    user_id = update.effective_user.id
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_user_id(user_id)
        
        if not user or not user.consent_given_at:
            await show_consent_message(update, context, user_repo, user, user_id)
            return False
        
        return True


async def show_consent_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_repo: UserRepository,
    user: Optional[User],
    user_id: int
):
    """Показывает сообщение с согласием"""
    # Build Web App URL
    # Telegram Web App requires HTTPS URL (except for localhost in development)
    if settings.webhook_url:
        # Ensure URL doesn't have trailing slash
        base_url = settings.webhook_url.rstrip('/')
        web_app_url = f"{base_url}/webapp/privacy_policy.html"
    else:
        # Fallback - but this won't work in production Telegram Web App
        # Telegram requires HTTPS for Web Apps (except localhost)
        web_app_url = "http://localhost:8000/webapp/privacy_policy.html"
        print("WARNING: WEBHOOK_URL not set. Web App may not work in production!")
    
    # Create keyboard with Web App button and Continue button
    keyboard = [
        [InlineKeyboardButton(
            "📄 Ознакомиться с политикой",
            web_app=WebAppInfo(url=web_app_url)
        )],
        [InlineKeyboardButton("✅ Продолжить", callback_data="accept_consent")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    consent_text = """🔐 Подтверждение условий использования

Для использования бота необходимо:
• Быть старше 18 лет
• Ознакомиться с Политикой конфиденциальности

[📄 Ознакомиться с политикой] 
[✅ Продолжить]"""
    
    if update.message:
        await update.message.reply_text(consent_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(consent_text, reply_markup=reply_markup)
        await update.callback_query.answer()


async def handle_consent_acceptance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Обрабатывает принятие согласия"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
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
        
        # Show welcome message
        await update.callback_query.answer("✅ Согласие принято")
        await show_welcome_message(update, context)


async def show_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает приветственное сообщение после согласия"""
    welcome_text = """🎯 Добро пожаловать в закрытый сервис!

⚡ ДОСТУП К БАЗЕ FLO ОТКРЫТ
Узнай дату овуляции по номеру телефона
Данные обновляются в реальном времени

💳 Стоимость запроса: 50 руб.

Отправь номер телефона в формате:
+7XXXXXXXXXX"""
    
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(welcome_text)
        except Exception:
            # Если не удалось отредактировать, отправляем новое сообщение
            await update.callback_query.message.reply_text(welcome_text)
    elif update.message:
        await update.message.reply_text(welcome_text)

