# start_all.py
import subprocess
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_DIR = os.path.join(BASE_DIR, "api")
BOT_DIR = os.path.join(BASE_DIR, "bot")
DASHBOARD_DIR = os.path.join(BASE_DIR, "admin-dashboard")

commands = [
    {"name":"Flask API", "cmd": "python -m api.app" if sys.platform.startswith("win") else "python3 -m api.app", "cwd": BASE_DIR},
    {"name":"Telegram Bot", "cmd": "python telegram_bot.py" if sys.platform.startswith("win") else "python3 telegram_bot.py", "cwd": BOT_DIR},
    {"name":"React Dashboard", "cmd": "npm start", "cwd": DASHBOARD_DIR}
]

for cmd in commands:
    print(f"🔹 تشغيل {cmd['name']}...")
    if sys.platform.startswith("win"):
        subprocess.Popen(f'start cmd /k "{cmd["cmd"]}"', shell=True, cwd=cmd["cwd"])
    else:
        subprocess.Popen(f'gnome-terminal -- bash -c "{cmd["cmd"]}; exec bash"', shell=True, cwd=cmd["cwd"])
    if cmd["name"] == "Flask API":
        time.sleep(5)

print("✅ كل الخدمات بدأت! تحقق من النوافذ الجديدة.")
