from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes
from datetime import datetime
from typing import Optional
import os
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
    """Показывает сообщение с согласием и отправляет файл с политикой"""
    # Путь к файлу с политикой
    current_dir = os.path.dirname(os.path.abspath(__file__))
    policy_file_path = os.path.join(
        current_dir, "..", "..", "presentation", "web_app", "privacy_policy.txt"
    )
    policy_file_path = os.path.abspath(policy_file_path)
    
    # Создаем клавиатуру только с кнопкой "Продолжить"
    keyboard = [
        [InlineKeyboardButton("✅ Продолжить", callback_data="accept_consent")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    consent_text = """🔐 Подтверждение условий использования

Для использования бота необходимо:
• Быть старше 18 лет
• Ознакомиться с Политикой конфиденциальности

📄 Политика конфиденциальности отправлена файлом выше.

Нажимая "✅ Продолжить", вы подтверждаете, что:
• Вам исполнилось 18 лет
• Вы ознакомились с Политикой конфиденциальности
• Вы согласны с условиями использования"""
    
    # Отправляем файл с политикой
    if os.path.exists(policy_file_path):
        try:
            with open(policy_file_path, 'rb') as policy_file:
                if update.message:
                    await update.message.reply_document(
                        document=InputFile(policy_file, filename="Политика_конфиденциальности.txt"),
                        caption="📄 Политика конфиденциальности"
                    )
                    await update.message.reply_text(consent_text, reply_markup=reply_markup)
                elif update.callback_query:
                    await update.callback_query.message.reply_document(
                        document=InputFile(policy_file, filename="Политика_конфиденциальности.txt"),
                        caption="📄 Политика конфиденциальности"
                    )
                    await update.callback_query.message.reply_text(consent_text, reply_markup=reply_markup)
                    await update.callback_query.answer()
        except Exception as e:
            print(f"Error sending policy file: {e}")
            # Fallback - отправляем только текст
            if update.message:
                await update.message.reply_text(consent_text, reply_markup=reply_markup)
            elif update.callback_query:
                await update.callback_query.message.reply_text(consent_text, reply_markup=reply_markup)
                await update.callback_query.answer()
    else:
        print(f"Policy file not found at: {policy_file_path}")
        # Fallback - отправляем только текст
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

