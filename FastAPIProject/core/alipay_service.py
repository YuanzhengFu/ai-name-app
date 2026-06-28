import base64
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

from settings import (
    ALIPAY_APP_ID,
    ALIPAY_GATEWAY,
    ALIPAY_PRIVATE_KEY_PATH,
    ALIPAY_PUBLIC_KEY_PATH,
    BASE_DIR,
    PAYMENT_PUBLIC_BASE_URL,
    PAYMENT_RETURN_URL,
)


ALIPAY_STATUS_SUCCESS = {"TRADE_SUCCESS", "TRADE_FINISHED"}
ALIPAY_STATUS_PROCESSING = {"WAIT_BUYER_PAY"}
ALIPAY_STATUS_FAILED = {"TRADE_CLOSED"}


class AlipayService:
    def __init__(self):
        self.app_id = ALIPAY_APP_ID
        self.gateway = ALIPAY_GATEWAY
        self.private_key_path = ALIPAY_PRIVATE_KEY_PATH
        self.public_key_path = ALIPAY_PUBLIC_KEY_PATH

    def build_pay_url(
        self,
        *,
        out_trade_no: str,
        subject: str,
        total_amount: str,
        pay_scene: str = "page",
    ) -> str:
        if pay_scene not in {"page", "wap"}:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Unsupported alipay pay_scene")

        method = "alipay.trade.page.pay" if pay_scene == "page" else "alipay.trade.wap.pay"
        product_code = "FAST_INSTANT_TRADE_PAY" if pay_scene == "page" else "QUICK_WAP_WAY"
        params = self._base_params(method)
        params["notify_url"] = self._notify_url()
        return_url = PAYMENT_RETURN_URL or PAYMENT_PUBLIC_BASE_URL
        if return_url:
            params["return_url"] = return_url
        params["biz_content"] = json.dumps(
            {
                "out_trade_no": out_trade_no,
                "product_code": product_code,
                "total_amount": total_amount,
                "subject": subject[:256],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        params["sign"] = self._sign(params)
        return f"{self.gateway}?{urlencode(params)}"

    async def query_trade(self, out_trade_no: str) -> dict:
        params = self._base_params("alipay.trade.query")
        params["biz_content"] = json.dumps(
            {"out_trade_no": out_trade_no},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        params["sign"] = self._sign(params)
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(self.gateway, params=params)
        response.raise_for_status()
        payload = response.json()
        return payload.get("alipay_trade_query_response", {})

    def verify_notify(self, data: dict[str, str]) -> bool:
        sign = data.get("sign", "")
        sign_type = data.get("sign_type", "")
        if sign_type and sign_type != "RSA2":
            return False
        content = self._content_to_sign({key: value for key, value in data.items() if key not in {"sign", "sign_type"}})
        public_key = self._load_public_key()
        try:
            public_key.verify(
                base64.b64decode(sign),
                content.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except (InvalidSignature, ValueError):
            return False
        return True

    def _base_params(self, method: str) -> dict[str, str]:
        if not self.app_id:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Missing ALIPAY_APP_ID")
        return {
            "app_id": self.app_id,
            "method": method,
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
        }

    def _notify_url(self) -> str:
        if not PAYMENT_PUBLIC_BASE_URL:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Missing PAYMENT_PUBLIC_BASE_URL")
        return f"{PAYMENT_PUBLIC_BASE_URL.rstrip('/')}/membership/payment/notify/alipay"

    def _sign(self, params: dict[str, str]) -> str:
        private_key = self._load_private_key()
        signature = private_key.sign(
            self._content_to_sign(params).encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("ascii")

    def _load_private_key(self):
        if not self.private_key_path:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Missing ALIPAY_PRIVATE_KEY_PATH")
        key_data = self._resolve_path(self.private_key_path).read_bytes()
        return serialization.load_pem_private_key(key_data, password=None)

    def _load_public_key(self):
        if not self.public_key_path:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Missing ALIPAY_PUBLIC_KEY_PATH")
        key_data = self._resolve_path(self.public_key_path).read_bytes()
        return serialization.load_pem_public_key(key_data)

    @staticmethod
    def _resolve_path(raw_path: str) -> Path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        return path.resolve()

    @staticmethod
    def _content_to_sign(params: dict[str, str]) -> str:
        return "&".join(
            f"{key}={params[key]}"
            for key in sorted(params)
            if params[key] is not None and params[key] != ""
        )
