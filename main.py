from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.post("/webview")
async def show_init_data(request: Request):
    """
    Endpoint для Telegram WebApp.
    При запуске MiniApp Telegram отправляет POST-запрос с initData в теле.
    Просто выводим эти данные в html-странице.
    """
    data = await request.body()
    try:
        import json
        json_data = json.loads(data)
        pretty = json.dumps(json_data, ensure_ascii=False, indent=4)
        content = f"<pre>{pretty}</pre>"
    except Exception:
        content = f"<pre>{data.decode('utf-8', errors='replace')}</pre>"

    html = f"""
    <html>
        <head>
            <title>Telegram Init Data</title>
        </head>
        <body>
            <h2>Init Data пользователя:</h2>
            {content}
        </body>
    </html>
    """
    return HTMLResponse(content=html)
