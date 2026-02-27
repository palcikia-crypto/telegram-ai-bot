import json
import time
import os

QUEUE_FILE = "state/queue.json"

if not os.path.exists(QUEUE_FILE):
    with open(QUEUE_FILE, "w") as f:
        json.dump([], f)

with open(QUEUE_FILE, "r") as f:
    tasks = json.load(f)

tasks.append({
    "id": int(time.time()),
    "prompt": f"Привет, время {time.strftime('%H:%M')}",
    "processed": False
})

with open(QUEUE_FILE, "w") as f:
    json.dump(tasks, f, indent=2)

print("Task added.")
