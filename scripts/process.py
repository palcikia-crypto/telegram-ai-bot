import json
import os
import requests
import time

QUEUE_FILE = "state/queue.json"
INTERVAL = 15   # проверка каждые 15 секунд
DURATION = 120  # цикл на 2 минуты

# Создаём файл, если нет
if not os.path.exists(QUEUE_FILE):
    with open(QUEUE_FILE, "w") as f:
        json.dump([], f)

start = time.time()
while time.time() - start < DURATION:
    with open(QUEUE_FILE, "r") as f:
        tasks = json.load(f)

    updated = False
    for task in tasks:
        if not task.get("processed"):
            # OpenRouter
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": task["prompt"]}]
                }
            )
            data = response.json()
            if "choices" not in data:
                continue
            result = data["choices"][0]["message"]["content"]

            # Telegram
            requests.post(
                f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/sendMessage",
                json={"chat_id": os.getenv("TELEGRAM_CHAT_ID"), "text": result}
            )

            task["processed"] = True
            updated = True

    if updated:
        with open(QUEUE_FILE, "w") as f:
            json.dump(tasks, f, indent=2)

    time.sleep(INTERVAL)
