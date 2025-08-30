import os
import json
import asyncio
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# -------- Load Config --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config_bot.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CFG = json.load(f)

BOT_TOKEN = CFG["BOT_TOKEN"]
API = CFG["API_BASE_URL"].rstrip("/")
ADMIN_USER = CFG.get("ADMIN_USERNAME")
ADMIN_PASS = CFG.get("ADMIN_PASSWORD")

# per-chat admin tokens
ADMIN_TOKENS = {}  # chat_id -> token

# -------- HTTP client --------
client = httpx.AsyncClient(timeout=15.0)

# -------- Helpers --------
async def api_get(path, params=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = await client.get(f"{API}{path}", params=params, headers=headers)
    return r.json()

async def api_post(path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = await client.post(f"{API}{path}", json=data or {}, headers=headers)
    return r.json()

# -------- Commands --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك 👋\nاختر الشركة لعرض المشاريع:",
        reply_markup=await companies_keyboard()
    )

async def companies_keyboard():
    data = await api_get("/companies")
    companies = data.get("companies", [])
    buttons = [
        [InlineKeyboardButton(c["name"], callback_data=f"comp:{c['slug']}")]
        for c in companies
    ]
    return InlineKeyboardMarkup(buttons or [[InlineKeyboardButton("لا يوجد شركات", callback_data="noop")]])

async def projects_keyboard(company_slug: str):
    data = await api_get("/projects", params={"company_slug": company_slug})
    projects = data.get("projects", [])
    buttons = [
        [InlineKeyboardButton(p["title"], callback_data=f"proj:{company_slug}:{p['id']}")]
        for p in projects
    ]
    buttons.append([InlineKeyboardButton("⬅ رجوع", callback_data="back:companies")])
    return InlineKeyboardMarkup(buttons or [[InlineKeyboardButton("لا يوجد مشاريع", callback_data=f"back:companies")]])

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data.split(":")
    if data[0] == "comp":
        company_slug = data[1]
        await q.edit_message_text(
            f"مشاريع شركة: {company_slug}",
            reply_markup=await projects_keyboard(company_slug)
        )
    elif data[0] == "back" and data[1] == "companies":
        await q.edit_message_text(
            "اختر الشركة:",
            reply_markup=await companies_keyboard()
        )

# -------- Admin Login --------
async def adminlogin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    resp = await api_post("/auth/login", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    if not resp.get("ok"):
        await update.message.reply_text("فشل الدخول كأدمن.")
        return
    ADMIN_TOKENS[chat_id] = resp["access_token"]
    await update.message.reply_text("✅ تم تسجيل الدخول كأدمن لهذا الشات.")

# -------- Main Function --------
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adminlogin", adminlogin))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("🤖 البوت شغال الآن...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
