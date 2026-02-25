import os
import json
import requests
import base64
from pathlib import Path
from cryptography.fernet import Fernet
import time

# Берём ключ для шифрования
secret = os.getenv("OPENROUTER_API_KEY").encode()[:32]
if len(secret) < 32:
    secret = secret + b'0' * (32 - len(secret))
key = Fernet(base64.urlsafe_b64encode(secret))

queue_file = Path("state/queue.enc")
results_file = Path("state/results.enc")

# Читаем очередь
tasks = []
if queue_file.exists() and queue_file.stat().st_size > 0:
    try:
        encrypted = queue_file.read_bytes()
        data = key.decrypt(encrypted)
        tasks = json.loads(data)
    except:
        tasks = []

if not tasks:
    print("Нет задач")
    # Создаем пустые файлы
    queue_file.write_bytes(key.encrypt(json.dumps([]).encode()))
    results_file.write_bytes(key.encrypt(json.dumps([]).encode()))
    exit()

results = []
updated_tasks = []

for task in tasks:
    if task.get("processed"):
        updated_tasks.append(task)
        continue

    success = False
    attempts = 0
    while not success and attempts < 3:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/your-repo",
                },
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": task["prompt"]}],
                },
                timeout=60
            )
            data = response.json()
            text = data["choices"][0]["message"]["content"]

            results.append({
                "id": task["id"],
                "result": text,
                "time": int(time.time())
            })

            task["processed"] = True
            success = True

        except:
            attempts += 1
            time.sleep(5)

    updated_tasks.append(task)

# Сохраняем очередь
queue_file.write_bytes(key.encrypt(json.dumps(updated_tasks).encode()))

# Сохраняем результаты
old_results = []
if results_file.exists() and results_file.stat().st_size > 0:
    try:
        data = key.decrypt(results_file.read_bytes())
        old_results = json.loads(data)
    except:
        old_results = []

all_results = old_results + results
results_file.write_bytes(key.encrypt(json.dumps(all_results).encode()))

# --- Отправка в Telegram ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text[:4000]}
        requests.post(url, data=data, timeout=10)
    except:
        pass

for r in results:
    send_telegram(f"✅ Task {r['id']} done:\n{r['result']}")
