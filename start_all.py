# start_all.py
import subprocess
import os
import sys
import time


# بعد تشغيل الـ API
time.sleep(5)  # تنتظر 5 ثواني قبل تشغيل البوت

# ---------- مسارات المجلدات ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_DIR = os.path.join(BASE_DIR, "api")
BOT_DIR = os.path.join(BASE_DIR, "bot")
DASHBOARD_DIR = os.path.join(BASE_DIR, "admin-dashboard")

# ---------- أوامر التشغيل ----------
commands = [
    {
        "name": "Flask API",
        "cmd": f'python -m venv {os.path.join(API_DIR, "venv")} && '
               f'{os.path.join(API_DIR, "venv", "Scripts", "activate")} && '
               f'pip install -r requirements.txt && python app.py' if sys.platform.startswith("win") else
               f'python3 -m venv {os.path.join(API_DIR, "venv")} && '
               f'source {os.path.join(API_DIR, "venv", "bin", "activate")} && '
               f'pip install -r requirements.txt && python3 app.py',
        "cwd": API_DIR
    },
    {
        "name": "Telegram Bot",
        "cmd": "python telegram_bot.py" if sys.platform.startswith("win") else "python3 telegram_bot.py",
        "cwd": BOT_DIR
    },
    {
        "name": "React Dashboard",
        "cmd": "npm start",
        "cwd": DASHBOARD_DIR
    }
]

# ---------- تشغيل كل خدمة في نافذة مستقلة ----------
for cmd in commands:
    print(f"🔹 تشغيل {cmd['name']}...")
    if sys.platform.startswith("win"):
        # Windows
        subprocess.Popen(f'start cmd /k "{cmd["cmd"]}"', shell=True, cwd=cmd["cwd"])
    else:
        # Linux / MacOS
        subprocess.Popen(f'gnome-terminal -- bash -c "{cmd["cmd"]}; exec bash"', shell=True, cwd=cmd["cwd"])

print("✅ كل الخدمات بدأت! تحقق من النوافذ الجديدة.")
