import hashlib
import hmac
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

def verify_telegram_auth(data: dict) -> bool:
    """
    Проверяет подпись Telegram WebApp.
    """
    check_hash = data.pop("hash", None)
    if not check_hash:
        return False

    data_check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(calculated_hash, check_hash)
