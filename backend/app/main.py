from fastapi import FastAPI, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from .dependencies import verify_telegram_authentication
from .config import settings

app = FastAPI(title="Telegram MiniApp Auth")
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

# Настройка CORS для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/auth/telegram")
async def telegram_auth_endpoint(init_data: str = Form(...)):
    user_data = verify_telegram_authentication(init_data)
    return {
        "status": "success",
        "user": {
            "id": user_data["id"],
            "first_name": user_data["first_name"],
            "username": user_data.get("username", ""),
            "language": user_data.get("language_code", "")
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "bot_token_configured": bool(settings.BOT_TOKEN)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=settings.DEBUG
    )