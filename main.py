from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import urllib.parse
import hmac
import hashlib

app = FastAPI()

# Ваш токен бота Telegram
BOT_TOKEN = '7045210026:AAHC9-gvim_AGmCkLx2ZPoNHcR8v0ohXDMM'

def verify_init_data(init_data: str, bot_token: str) -> bool:
    """
    Проверяет подпись поля initData по алгоритму из документации
    https://core.telegram.org/bots/webapps#validating-data-received-via-web-apps
    """
    params = urllib.parse.parse_qs(init_data, strict_parsing=True)
    received_hash = params.pop("hash", [None])[0]
    if not received_hash:
        return False

    # Формируем проверочную строку
    check_list = []
    for key in sorted(params.keys()):
        check_list.append(f"{key}={params[key][0]}")
    data_check_string = "\n".join(check_list)

    # Секретный ключ — это SHA-256 от bot_token
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(computed_hash, received_hash)

@app.get("/", response_class=HTMLResponse)
async def index():
    """
    Отдаёт простую HTML-страницу, которая сразу же
    берёт window.Telegram.WebApp.initData и показывает его.
    """
    return """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Telegram Mini App</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
  <h2>Ваш initData:</h2>
  <pre id="data">Loading…</pre>
  <script>
    const initData = window.Telegram.WebApp.initData;
    fetch("/init", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ initData })
    })
    .then(r => r.json())
    .then(j => {
      document.getElementById("data").textContent = JSON.stringify(j, null, 2);
    })
    .catch(e => {
      document.getElementById("data").textContent = "Error: " + e;
    });
  </script>
</body>
</html>
"""

@app.post("/init")
async def init(request: Request):
    """
    Принимает JSON {"initData": "..."} и возвращает распарсенные данные
    после проверки подписи.
    """
    body = await request.json()
    init_data = body.get("initData")
    if not init_data:
        raise HTTPException(400, "initData is required")

    if not verify_init_data(init_data, BOT_TOKEN):
        raise HTTPException(403, "Invalid initData signature")

    parsed = urllib.parse.parse_qs(init_data)
    # преобразуем списки в строки
    clean = {k: v[0] for k, v in parsed.items()}
    return JSONResponse({"user_data": clean})
