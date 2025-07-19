from fastapi import FastAPI, Request, HTTPException
from auth import verify_telegram_auth

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Telegram Mini App Backend is running"}

@app.post("/auth/telegram")
async def telegram_auth(request: Request):
    """
    Эндпоинт для проверки подписи и возврата данных пользователя.
    """
    data = await request.json()
    if not verify_telegram_auth(data.copy()):
        raise HTTPException(status_code=400, detail="Invalid Telegram signature")

    # Возвращаем приветствие с данными пользователя
    return {
        "status": "ok",
        "message": f"Hello, {data.get('first_name', 'User')}!",
        "telegram_id": data.get("id"),
        "username": data.get("username"),
        "photo_url": data.get("photo_url")
    }
