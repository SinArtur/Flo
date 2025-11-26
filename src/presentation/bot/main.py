from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from telegram import Update
from telegram.ext import Application, ContextTypes
from src.config.settings import settings
from src.infrastructure.telegram_bot.handlers import setup_handlers
from src.presentation.webhooks.yookassa import router as yookassa_router
import os

app = FastAPI(title="FL0 Hack Bot")
app.include_router(yookassa_router)

# Mount static files for Web App
# Get absolute path to web_app directory
current_dir = os.path.dirname(os.path.abspath(__file__))
web_app_path = os.path.join(current_dir, "..", "web_app")
web_app_path = os.path.abspath(web_app_path)

if os.path.exists(web_app_path):
    app.mount("/webapp", StaticFiles(directory=web_app_path, html=True), name="webapp")
    print(f"Web App files mounted from: {web_app_path}")
else:
    print(f"WARNING: Web App directory not found at: {web_app_path}")

# Initialize Telegram bot
# Важно: concurrent_updates=True позволяет обрабатывать несколько обновлений параллельно
bot_application = Application.builder().token(settings.telegram_bot_token).concurrent_updates(True).build()
print(f"[DEBUG] Bot application created with token: {settings.telegram_bot_token[:10]}...")
setup_handlers(bot_application)
print("[DEBUG] Handlers setup completed")

# Add error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log the error and send a message to the user"""
    import traceback
    import sys
    
    error = context.error
    error_type = type(error).__name__
    error_message = str(error)
    
    # Get user info if available
    user_id = None
    if update and isinstance(update, Update) and update.effective_user:
        user_id = update.effective_user.id
    
    # Print detailed error information
    print(f"\n{'='*60}")
    print(f"[ERROR] Exception while handling an update")
    print(f"User ID: {user_id}")
    print(f"Error Type: {error_type}")
    print(f"Error Message: {error_message}")
    print(f"{'='*60}")
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stdout)
    print(f"{'='*60}\n")
    
    # Try to send error message to user
    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка при обработке вашего запроса. Попробуйте позже."
            )
        except Exception as send_error:
            print(f"[ERROR] Failed to send error message to user: {send_error}")

bot_application.add_error_handler(error_handler)


@app.on_event("startup")
async def startup():
    """Initialize bot on startup"""
    print("[DEBUG] Initializing bot...")
    
    # Test database connection
    try:
        from sqlalchemy import text
        from src.infrastructure.database.base import async_session_maker
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
            await session.commit()
        print("[DEBUG] Database connection OK")
    except Exception as db_error:
        print(f"[ERROR] Database connection failed: {db_error}")
        import traceback
        traceback.print_exc()
        # Don't fail startup, but log the error
    
    # Test Redis connection
    try:
        from src.infrastructure.redis import RedisClient
        redis_client = RedisClient()
        await redis_client.get("test")
        print("[DEBUG] Redis connection OK")
    except Exception as redis_error:
        print(f"[WARNING] Redis connection failed (will continue without rate limiting): {redis_error}")
    
    await bot_application.initialize()
    print("[DEBUG] Starting bot...")
    await bot_application.start()
    print("[DEBUG] Starting polling...")
    # Важно: drop_pending_updates=True очищает старые обновления при старте
    # concurrent_updates=True позволяет обрабатывать несколько обновлений параллельно
    await bot_application.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"]
    )
    print("[DEBUG] Bot is ready and polling for updates")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown bot on shutdown"""
    await bot_application.updater.stop()
    await bot_application.stop()
    await bot_application.shutdown()


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook"""
    data = await request.json()
    update = Update.de_json(data, bot_application.bot)
    user_id = update.effective_user.id if update.effective_user else None
    update_id = update.update_id
    print(f"[DEBUG] Webhook received update_id={update_id} from user_id={user_id}")
    await bot_application.process_update(update)
    print(f"[DEBUG] Webhook processed update_id={update_id} from user_id={user_id}")
    return {"ok": True}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/webapp/test")
async def webapp_test():
    """Test endpoint to check if webapp is accessible"""
    return {
        "status": "ok",
        "webapp_path": web_app_path,
        "exists": os.path.exists(web_app_path),
        "files": os.listdir(web_app_path) if os.path.exists(web_app_path) else []
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

