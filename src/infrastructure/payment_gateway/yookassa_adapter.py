import httpx
import base64
import hmac
import hashlib
from typing import Optional, Tuple
from src.core.interfaces.payment_gateway import IPaymentGateway
from src.config.settings import settings


class YooKassaAdapter(IPaymentGateway):
    BASE_URL = "https://api.yookassa.ru/v3"
    
    def __init__(self):
        self.shop_id = settings.yookassa_shop_id
        self.secret_key = settings.yookassa_secret_key
        self.webhook_secret = settings.webhook_secret
    
    def _get_auth_header(self) -> str:
        """Returns Basic Auth header for YooKassa API"""
        credentials = f"{self.shop_id}:{self.secret_key}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    async def create_payment(
        self, amount: float, description: str, metadata: dict
    ) -> Tuple[str, str]:
        """Creates payment in YooKassa and returns (payment_id, payment_url)"""
        url = f"{self.BASE_URL}/payments"
        
        payload = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": settings.webhook_url.replace("/webhook/yookassa", "/payment/success")
            },
            "capture": True,
            "description": description,
            "metadata": metadata
        }
        
        headers = {
            "Authorization": self._get_auth_header(),
            "Idempotence-Key": f"{metadata.get('user_id')}_{metadata.get('phone_number')}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            payment_id = data["id"]
            payment_url = data["confirmation"]["confirmation_url"]
            
            return payment_id, payment_url
    
    async def get_payment_url(self, payment_id: str) -> Optional[str]:
        """Gets payment URL from YooKassa"""
        url = f"{self.BASE_URL}/payments/{payment_id}"
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "pending":
                    return data.get("confirmation", {}).get("confirmation_url")
                return None
            except httpx.HTTPError:
                return None
    
    async def verify_webhook(
        self, payment_id: str, amount: float, metadata: dict
    ) -> bool:
        """
        Verifies webhook signature and payment data.
        In production, YooKassa sends webhook with signature in headers.
        For now, we verify by fetching payment status from API.
        """
        url = f"{self.BASE_URL}/payments/{payment_id}"
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Verify payment status and amount
                if data.get("status") != "succeeded":
                    return False
                
                payment_amount = float(data.get("amount", {}).get("value", 0))
                if abs(payment_amount - amount) > 0.01:  # Allow small floating point differences
                    return False
                
                # Verify metadata matches
                payment_metadata = data.get("metadata", {})
                if payment_metadata.get("user_id") != str(metadata.get("user_id")):
                    return False
                if payment_metadata.get("phone_number") != metadata.get("phone_number"):
                    return False
                
                return True
            except httpx.HTTPError:
                return False

