import os

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()