import os
import requests

requests.post(
    f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendMessage",
    json={
        "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        "text": "ТЕСТ. Бот работает."
    }
)
