from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from telegram import Update
from telegram.ext import Application
from src.config.settings import settings
from src.infrastructure.telegram_bot.handlers import setup_handlers
from src.presentation.webhooks.yookassa import router as yookassa_router
import os

app = FastAPI(title="Flo Hack Bot")
app.include_router(yookassa_router)

# Mount static files for Web App
web_app_path = os.path.join(os.path.dirname(__file__), "..", "web_app")
if os.path.exists(web_app_path):
    app.mount("/webapp", StaticFiles(directory=web_app_path), name="webapp")

# Initialize Telegram bot
bot_application = Application.builder().token(settings.telegram_bot_token).build()
setup_handlers(bot_application)


@app.on_event("startup")
async def startup():
    """Initialize bot on startup"""
    await bot_application.initialize()
    await bot_application.start()
    await bot_application.updater.start_polling()


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
    await bot_application.process_update(update)
    return {"ok": True}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

