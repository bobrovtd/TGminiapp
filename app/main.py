from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from auth import verify_telegram_auth

app = FastAPI()

# Подключаем папку static для отдачи index.html
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

@app.post("/auth/telegram")
async def telegram_auth_post(request: Request):
    """
    POST-запрос для авторизации пользователя через Telegram.
    """
    data = await request.json()
    if not verify_telegram_auth(data.copy()):
        raise HTTPException(status_code=400, detail="Invalid Telegram signature")

    return {
        "status": "ok",
        "message": f"Hello, {data.get('first_name', 'User')}!",
        "telegram_id": data.get("id"),
        "username": data.get("username"),
        "photo_url": data.get("photo_url")
    }
