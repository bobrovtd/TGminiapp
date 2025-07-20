from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

# Установи библиотеку: pip install init-data-py
try:
    from init_data_py import InitData

    INIT_DATA_PY_AVAILABLE = True
except ImportError:
    INIT_DATA_PY_AVAILABLE = False
    print("Предупреждение: init-data-py не установлена. Используй: pip install init-data-py")

app = FastAPI(title="Telegram MiniApp Backend (Simplified)", version="1.0.0")

# CORS для разрешения запросов от Telegram
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://web.telegram.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация
BOT_TOKEN = "7045210026:AAHC9-gvim_AGmCkLx2ZPoNHcR8v0ohXDMM"


class UserInfoResponse(BaseModel):
    """Ответ с информацией о пользователе"""
    user_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = None
    auth_date: int
    chat_type: Optional[str] = None
    is_valid: bool


@app.get("/")
async def root():
    """Главная страница API"""
    return {
        "message": "Telegram MiniApp Backend API (Simplified)",
        "version": "1.0.0",
        "init_data_py_available": INIT_DATA_PY_AVAILABLE
    }


@app.post("/auth/simple", response_model=UserInfoResponse)
async def authenticate_user_simple(
        init_data_raw: str = Header(..., alias="x-telegram-init-data")
):
    """
    Упрощенная аутентификация с init-data-py
    """
    if not INIT_DATA_PY_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="init-data-py библиотека не установлена"
        )

    try:
        # Парсим и валидируем initData
        init_data = InitData.parse(init_data_raw)
        is_valid = init_data.validate(BOT_TOKEN, lifetime=3600)  # 1 час

        if not is_valid:
            raise HTTPException(
                status_code=401,
                detail="Невалидные данные Telegram"
            )

        # Проверяем наличие пользователя
        if not init_data.user:
            raise HTTPException(
                status_code=404,
                detail="Данные пользователя не найдены"
            )

        # Формируем ответ
        response = UserInfoResponse(
            user_id=init_data.user.id,
            first_name=init_data.user.first_name,
            last_name=init_data.user.last_name,
            username=init_data.user.username,
            language_code=init_data.user.language_code,
            is_premium=init_data.user.is_premium,
            auth_date=init_data.auth_date.timestamp() if init_data.auth_date else 0,
            chat_type=init_data.chat_type,
            is_valid=is_valid
        )

        return response

    except Exception as e:
        logging.error(f"Ошибка при обработке initData: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка обработки данных: {str(e)}"
        )


@app.get("/user/profile")
async def get_user_profile(
        init_data_raw: str = Header(..., alias="x-telegram-init-data")
):
    """
    Получение расширенного профиля пользователя
    """
    if not INIT_DATA_PY_AVAILABLE:
        # Fallback для случая без init-data-py
        return {"error": "init-data-py не установлена"}

    try:
        init_data = InitData.parse(init_data_raw)
        is_valid = init_data.validate(BOT_TOKEN, lifetime=3600)

        if not is_valid:
            raise HTTPException(status_code=401, detail="Невалидные данные")

        # Полная информация
        profile = {
            "user": {
                "id": init_data.user.id if init_data.user else None,
                "first_name": init_data.user.first_name if init_data.user else None,
                "last_name": init_data.user.last_name if init_data.user else None,
                "username": init_data.user.username if init_data.user else None,
                "language_code": init_data.user.language_code if init_data.user else None,
                "is_premium": init_data.user.is_premium if init_data.user else None,
                "allows_write_to_pm": init_data.user.allows_write_to_pm if init_data.user else None,
            },
            "session": {
                "auth_date": init_data.auth_date.isoformat() if init_data.auth_date else None,
                "query_id": init_data.query_id,
                "chat_type": init_data.chat_type,
                "chat_instance": init_data.chat_instance,
                "start_param": init_data.start_param,
            },
            "chat": {
                "id": init_data.chat.id if init_data.chat else None,
                "type": init_data.chat.type if init_data.chat else None,
                "title": init_data.chat.title if init_data.chat else None,
                "username": init_data.chat.username if init_data.chat else None,
            } if init_data.chat else None,
            "is_valid": is_valid
        }

        return profile

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
