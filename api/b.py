from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ----------------------------
# إعداد التوكن
# ----------------------------
BOT_TOKEN = "8415187777:AAHF_UB5_h0iGiCD7-LuDE9BOHNw8mqtaIs"

# ----------------------------
# أوامر البوت
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("بوت شغال ✅")

# ----------------------------
# تشغيل البوت
# ----------------------------
def main():
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()

    # إضافة الهاندلر للأمر /start
    app.add_handler(CommandHandler("start", start))

    # تشغيل البوت
    print("🔹 البوت شغال الآن...")
    app.run_polling()

# ----------------------------
# نقطة البداية
# ----------------------------
if __name__ == "__main__":
    main()
