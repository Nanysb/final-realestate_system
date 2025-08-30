import json
import asyncio
import httpx
from functools import partial
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import ApplicationBuilder
import os, json
# -------- Load Config --------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # فولدر هذا الملف
CONFIG_PATH = os.path.join(BASE_DIR, "config_bot.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CFG = json.load(f)

BOT_TOKEN = CFG["BOT_TOKEN"]
API = CFG["API_BASE_URL"].rstrip("/")
ADMIN_USER = CFG.get("ADMIN_USERNAME")
ADMIN_PASS = CFG.get("ADMIN_PASSWORD")

# per-chat admin tokens (MVP)
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

async def api_put(path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = await client.put(f"{API}{path}", json=data or {}, headers=headers)
    return r.json()

async def api_delete(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = await client.delete(f"{API}{path}", headers=headers)
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

async def units_keyboard(project_id: int, page: int = 1):
    data = await api_get("/units", params={"project_id": project_id, "page": page, "limit": 10})
    units = data.get("units", [])
    buttons = []
    for u in units:
        label = f"{u['code']} | {u['sqm']}م² | دور {u['floor']} | إجمالي {u['total_price']}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"unit:{u['id']}")])
    buttons.append([InlineKeyboardButton("⬅ رجوع", callback_data=f"back:projects")])
    return InlineKeyboardMarkup(buttons or [[InlineKeyboardButton("لا يوجد وحدات", callback_data=f"back:projects")]])

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

    elif data[0] == "proj":
        company_slug, project_id = data[1], int(data[2])
        kb = await units_keyboard(project_id)
        await q.edit_message_text(
            f"الوحدات المتاحة في المشروع {project_id}",
            reply_markup=kb
        )

    elif data[0] == "unit":
        unit_id = int(data[1])
        u = await api_get(f"/units/{unit_id}")
        if not u.get("ok"):
            await q.edit_message_text("حدث خطأ في جلب بيانات الوحدة.")
            return
        unit = u["unit"]
        msg = (
            f"📌 كود: {unit['code']}\n"
            f"المساحة: {unit['sqm']} م²\n"
            f"الدور: {unit['floor']}\n"
            f"سعر المتر: {unit['price_per_sqm']} جنيه\n"
            f"الإجمالي: {unit['total_price']} جنيه\n"
            f"الحالة: {unit['status']}"
        )
        await q.edit_message_text(msg)

    elif data[0] == "back":
        if data[1] == "companies":
            await q.edit_message_text(
                "اختر الشركة:",
                reply_markup=await companies_keyboard()
            )
        elif data[1] == "projects":
            # ما عندناش state للشركة هنا، نرجّع لقائمة الشركات
            await q.edit_message_text(
                "اختر الشركة:",
                reply_markup=await companies_keyboard()
            )

# -------- Admin Quick Login (MVP) --------
async def adminlogin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # هنستخدم بيانات من config كحساب الخدمة
    resp = await api_post("/auth/login", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    if not resp.get("ok"):
        await update.message.reply_text("فشل الدخول كأدمن.")
        return
    ADMIN_TOKENS[chat_id] = resp["access_token"]
    await update.message.reply_text("✅ تم تسجيل الدخول كأدمن لهذا الشات.")

# /add_unit project_id code sqm price_per_sqm floor
async def add_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    token = ADMIN_TOKENS.get(chat_id)
    if not token:
        await update.message.reply_text("⚠️ لازم تعمل /adminlogin أولاً.")
        return

    try:
        project_id = int(context.args[0])
        code = context.args[1]
        sqm = float(context.args[2])
        price_per_sqm = int(context.args[3])
        floor = context.args[4]
    except:
        await update.message.reply_text("الاستخدام: /add_unit <project_id> <code> <sqm> <price_per_sqm> <floor>")
        return

    resp = await api_post("/units", token=token, data={
        "project_id": project_id,
        "code": code,
        "sqm": sqm,
        "price_per_sqm": price_per_sqm,
        "floor": floor
    })
    if resp.get("ok"):
        u = resp["unit"]
        await update.message.reply_text(f"✅ تمت إضافة وحدة: {u['code']} (ID={u['id']})")
    else:
        await update.message.reply_text(f"❌ فشل: {resp.get('error')}")

async def stop_client(app: Application):
    await client.aclose()
    await app.stop()

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("adminlogin", adminlogin))
    application.add_handler(CommandHandler("add_unit", add_unit))
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Run
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
