@echo off
REM ------------------- تشغيل API -------------------
echo 🔹 تشغيل Flask API...
start cmd /k "cd api && python -m venv venv && call venv\Scripts\activate && python app.py"

REM ------------------- تشغيل Telegram Bot -------------------
echo 🔹 تشغيل Telegram Bot...
start cmd /k "cd bot && python telegram_bot.py"

REM ------------------- تشغيل React Dashboard -------------------
echo 🔹 تشغيل React Dashboard...
start cmd /k "cd admin-dashboard && npm start"

echo ✅ كل الخدمات بدأت! تحقق من النوافذ الجديدة.
pause
