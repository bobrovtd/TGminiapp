import hashlib
import hmac
from urllib.parse import parse_qs, unquote
from typing import Optional
import logging

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware  # Для CORS, если фронтенд на другом домене
from pydantic import BaseModel, Field

# --- Конфигурация ---
# Замените на ваш Bot Token из @BotFather
BOT_TOKEN = "8326096575:AAGNO4Pey7_Wq5gMoDkqr8p6EGPcPBshCSg"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Mini App Backend")


# Настройка CORS (при необходимости)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], # В продакшене укажите конкретный origin вашего Mini App
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

class UserInfoResponse(BaseModel):
    """Модель ответа с информацией о пользователе."""
    ok: bool = True
    user: dict = Field(..., description="Информация о пользователе из initData")
    chat: Optional[dict] = Field(None, description="Информация о чате из initData (если доступна)")
    chat_type: Optional[str] = Field(None, description="Тип чата из initData")
    chat_instance: Optional[str] = Field(None,
                                         description="Идентификатор чат-экземпляра из initData")
    # Можно добавить другие поля из initData при необходимости


def validate_init_data(init_data: str, bot_token: str) -> bool:
    """
    Проверяет подпись initData, используя алгоритм HMAC-SHA256.
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    try:
        parsed_data = parse_qs(init_data, keep_blank_values=True)
        logger.debug(f"Parsed init_ {parsed_data}")

        # Извлекаем хэш и удаляем его из данных
        received_hash = parsed_data.pop('hash', [None])[0]
        if not received_hash:
            logger.warning("Hash not found in init_data")
            return False

        # Подготавливаем данные для проверки
        data_check_string_list = []
        for key, value_list in sorted(parsed_data.items()):
            if value_list:  # Учитываем только непустые значения
                # Декодируем URL-кодированные символы
                key_decoded = unquote(key)
                value_decoded = unquote(value_list[0]) if value_list else ''
                data_check_string_list.append(f"{key_decoded}={value_decoded}")

        data_check_string = '\n'.join(data_check_string_list)
        logger.debug(f"Data check string: {data_check_string}")

        # Создаем секретный ключ
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode(), hashlib.sha256
        ).digest()
        logger.debug(f"Secret key (first 8 bytes): {secret_key[:8].hex()}")

        # Вычисляем ожидаемый хэш
        expected_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        logger.debug(f"Received hash: {received_hash}")
        logger.debug(f"Expected hash: {expected_hash}")

        # Сравниваем хэши
        is_valid = hmac.compare_digest(received_hash, expected_hash)
        logger.info(f"InitData validation result: {is_valid}")
        return is_valid

    except Exception as e:
        logger.error(f"Error validating init_ {e}")
        return False


@app.post("/user-info", response_model=UserInfoResponse)
async def get_user_info(initData: str = Form(...)):
    """
    Эндпоинт для получения и проверки информации о пользователе из initData.

    Args:
        initData (str): Строка initData, полученная от Telegram Web App.

    Returns:
        UserInfoResponse: Информация о пользователе.

    Raises:
        HTTPException: Если подпись неверна или данные отсутствуют.
    """
    logger.info("Received request to /user-info")

    if not validate_init_data(initData, BOT_TOKEN):
        raise HTTPException(status_code=400, detail="Invalid initData signature")

    # Парсим initData после успешной проверки
    parsed_data = parse_qs(initData, keep_blank_values=True)

    # Извлекаем и парсим JSON-поля
    user_info = {}
    chat_info = None
    chat_type = parsed_data.get('chat_type', [None])[0]
    chat_instance = parsed_data.get('chat_instance', [None])[0]

    try:
        import json
        user_data_str = parsed_data.get('user', [None])[0]
        if user_data_str:
            user_info = json.loads(user_data_str)

        chat_data_str = parsed_data.get('chat', [None])[0]
        if chat_data_str:
            chat_info = json.loads(chat_data_str)

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing user/chat JSON from initData: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON in initData fields")

    if not user_info:
        raise HTTPException(status_code=400, detail="User data not found in initData")

    return UserInfoResponse(
        user=user_info,
        chat=chat_info,
        chat_type=chat_type,
        chat_instance=chat_instance
    )


# --- Простой HTML для тестирования ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Mini App Test</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script>
            async function fetchUserInfo() {
                const initData = window.Telegram.WebApp.initData;
                if (!initData) {
                    document.getElementById('result').innerText = 'initData not available. Open this page inside a Telegram Mini App.';
                    return;
                }
                
                try {
                    const response = await fetch('/user-info', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: `initData=${encodeURIComponent(initData)}`
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || 'Network response was not ok');
                    }
                    
                    const data = await response.json();
                    document.getElementById('result').innerText = JSON.stringify(data, null, 2);
                } catch (error) {
                    console.error('Error:', error);
                    document.getElementById('result').innerText = 'Error: ' + error.message;
                }
            }
            
            window.Telegram.WebApp.ready(); // Сообщаем Telegram, что приложение готово
        </script>
    </head>
    <body>
        <h1>Telegram Mini App Backend Test</h1>
        <button onclick="fetchUserInfo()">Get User Info</button>
        <pre id="result">Click the button to fetch user info from backend.</pre>
    </body>
    </html>
    """


# --- Запуск ---
# Используйте команду: uvicorn main:app --reload
# Или запустите этот скрипт напрямую:
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
