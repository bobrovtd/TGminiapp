import hashlib
import hmac
import json
import time
from urllib.parse import unquote

from fastapi import HTTPException
from .config import settings

def parse_init_data(init_data: str) -> dict:
    return {
        key: value
        for key, value in (
            item.split("=", 1) 
            for item in init_data.split("&")
        )
    }

def verify_telegram_authentication(init_data: str) -> dict:
    parsed_data = parse_init_data(init_data)
    
    # Проверка обязательных полей
    if "hash" not in parsed_data or "user" not in parsed_data:
        raise HTTPException(400, "Invalid init data")
    
    # Проверка времени жизни данных
    if time.time() - int(parsed_data["auth_date"]) > 600:
        raise HTTPException(401, "Authentication expired")
    
    # Проверка подписи
    if not check_signature(parsed_data, settings.BOT_TOKEN):
        raise HTTPException(401, "Invalid signature")
    
    # Извлечение данных пользователя
    try:
        return json.loads(unquote(parsed_data["user"]))
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid user data")

def check_signature(data: dict, bot_token: str) -> bool:
    received_hash = data["hash"]
    data_copy = {k: v for k, v in data.items() if k != "hash"}
    
    # Формирование строки для проверки
    data_check_string = "\n".join(
        f"{key}={value}" 
        for key, value in sorted(data_copy.items())
    )
    
    # Генерация секретного ключа
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256
    ).digest()
    
    # Расчет ожидаемого хеша
    expected_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Безопасное сравнение хешей
    return hmac.compare_digest(received_hash, expected_hash)