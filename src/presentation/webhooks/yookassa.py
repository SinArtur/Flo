from fastapi import APIRouter, Request, HTTPException
from telegram import Bot
from src.config.settings import settings
from src.infrastructure.utils.date_formatter import format_date_russian
from src.core.use_cases.verify_payment import VerifyPaymentUseCase
from src.infrastructure.database.repositories import PaymentRepository, RequestRepository
from src.infrastructure.payment_gateway import YooKassaAdapter
from src.core.use_cases.calculate_ovulation_date import CalculateOvulationDateUseCase

router = APIRouter(prefix="/webhook", tags=["webhooks"])


@router.post("/yookassa")
async def yookassa_webhook(request: Request):
    """Handle YooKassa payment webhook"""
    data = await request.json()
    
    event_type = data.get("event")
    if event_type != "payment.succeeded":
        return {"ok": True}
    
    payment_object = data.get("object", {})
    payment_id = payment_object.get("id")
    amount = float(payment_object.get("amount", {}).get("value", 0))
    metadata = payment_object.get("metadata", {})
    
    user_id = int(metadata.get("user_id", 0))
    phone_number = metadata.get("phone_number", "")
    
    if not user_id or not phone_number:
        raise HTTPException(status_code=400, detail="Invalid metadata")
    
    # Verify and process payment
    from src.infrastructure.database.base import async_session_maker
    async with async_session_maker() as session:
        payment_repo = PaymentRepository(session)
        request_repo = RequestRepository(session)
        
        payment_gateway = YooKassaAdapter()
        calculate_use_case = CalculateOvulationDateUseCase(request_repo)
        verify_use_case = VerifyPaymentUseCase(
            payment_repo, payment_gateway, calculate_use_case
        )
        
        is_verified, calculated_date = await verify_use_case.execute(
            payment_id, amount, metadata
        )
        
        if is_verified and calculated_date:
            # Send notification to user
            bot = Bot(token=settings.telegram_bot_token)
            date_str = format_date_russian(calculated_date)
            result_text = f"""✅ ОПЛАТА ПОДТВЕРЖДЕНА

📊 Данные из базы FL0:
Номер: {phone_number}
Следующая овуляция: {date_str}

🔄 Данные автоматически обновятся после этой даты"""
            
            try:
                await bot.send_message(chat_id=user_id, text=result_text)
            except Exception as e:
                # Log error but don't fail webhook
                print(f"Error sending message to user {user_id}: {e}")
    
    return {"ok": True}

