from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import hashlib
import hmac
import urllib.parse

load_dotenv()
app = FastAPI()

# Разрешаем CORS (для локальной разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В проде ограничьте!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

def check_init_data(init_data: str) -> dict:
    parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    hash_value = parsed.pop("hash", None)
    check_string = "\n".join([f"{k}={v}" for k, v in sorted(parsed.items())])
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    hmac_hash = hmac.new(secret_key, msg=check_string.encode(), digestmod=hashlib.sha256).hexdigest()
    if hmac_hash != hash_value:
        raise HTTPException(status_code=401, detail="Invalid signature")
    return parsed

@app.post("/auth")
async def auth(request: Request):
    data = await request.json()
    init_data = data.get("initData")
    try:
        user_data = check_init_data(init_data)
        return JSONResponse({"message": f"Добро пожаловать, {user_data.get('first_name', 'гость')}!"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
