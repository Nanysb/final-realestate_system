import json
import logging
import os
import signal
import sys
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# -------- Load Config --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config_bot.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CFG = json.load(f)

BOT_TOKEN = CFG["BOT_TOKEN"]
API = CFG["API_BASE_URL"].rstrip("/")
ADMIN_USER = CFG.get("ADMIN_USERNAME")
ADMIN_PASS = CFG.get("ADMIN_PASSWORD")
ADMIN_CHAT_IDS = CFG.get("ADMIN_CHAT_IDS", [])

# per-chat admin tokens
ADMIN_TOKENS = {}  # chat_id -> token

# -------- HTTP client --------
client = httpx.AsyncClient(timeout=15.0)

# -------- Logging --------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------- Helpers --------
def is_admin(chat_id):
    """التحقق إذا كان المستخدم أدمن"""
    return chat_id in ADMIN_CHAT_IDS

async def api_get(path, params=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = await client.get(f"{API}{path}", params=params, headers=headers)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"API GET Error: {e}")
        return {"ok": False, "error": str(e)}

async def api_post(path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = await client.post(f"{API}{path}", json=data or {}, headers=headers)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"API POST Error: {e}")
        return {"ok": False, "error": str(e)}

async def api_put(path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = await client.put(f"{API}{path}", json=data or {}, headers=headers)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"API PUT Error: {e}")
        return {"ok": False, "error": str(e)}

async def api_delete(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = await client.delete(f"{API}{path}", headers=headers)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"API DELETE Error: {e}")
        return {"ok": False, "error": str(e)}

# -------- Keyboards --------
async def companies_keyboard():
    data = await api_get("/companies")
    if not data.get("ok"):
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ خطأ في جلب البيانات", callback_data="noop")]])
    
    companies = data.get("data", [])
    buttons = [
        [InlineKeyboardButton(c["name"], callback_data=f"comp:{c['slug']}")]
        for c in companies
    ]
    return InlineKeyboardMarkup(buttons or [[InlineKeyboardButton("لا يوجد شركات", callback_data="noop")]])

async def projects_keyboard(company_slug: str):
    data = await api_get(f"/companies/{company_slug}")
    if not data.get("ok"):
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ خطأ في جلب البيانات", callback_data="back:companies")]])
    
    company = data.get("data", {})
    projects = company.get("projects", [])
    
    buttons = [
        [InlineKeyboardButton(p["title"], callback_data=f"proj:{company_slug}:{p['id']}")]
        for p in projects
    ]
    buttons.append([InlineKeyboardButton("⬅ رجوع", callback_data="back:companies")])
    return InlineKeyboardMarkup(buttons or [[InlineKeyboardButton("لا يوجد مشاريع", callback_data="back:companies")]])

async def units_keyboard(project_id: int, page: int = 1):
    data = await api_get("/units", params={"project_id": project_id})
    if not data.get("ok"):
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ خطأ في جلب البيانات", callback_data=f"back:projects")]])
    
    units = data.get("data", [])
    buttons = []
    for u in units:
        total_price = u.get('sqm', 0) * u.get('price_per_sqm', 0)
        label = f"{u['code']} | {u['sqm']}م² | {total_price:,} ج"
        buttons.append([InlineKeyboardButton(label, callback_data=f"unit:{u['id']}")])
    
    buttons.append([InlineKeyboardButton("⬅ رجوع", callback_data=f"back:projects")])
    return InlineKeyboardMarkup(buttons or [[InlineKeyboardButton("لا يوجد وحدات", callback_data=f"back:projects")]])

# -------- Commands --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "أهلاً بك 👋\nاختر الشركة لعرض المشاريع:",
        reply_markup=await companies_keyboard()
    )

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض chat_id الخاص بالمستخدم"""
    chat_id = update.effective_chat.id
    is_admin_user = is_admin(chat_id)
    
    message = f"🆔 Chat ID الخاص بك: `{chat_id}`\n"
    message += f"👤 حالة الأدمن: {'✅ أدمن' if is_admin_user else '❌ مستخدم عادي'}\n\n"
    message += "🔧 إذا كنت أدمن، أضف هذا الرقم إلى ADMIN_CHAT_IDS في config_bot.json"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def show_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض المشاريع المتاحة للجميع"""
    data = await api_get("/projects")
    if not data.get("ok"):
        await update.message.reply_text("❌ حدث خطأ في جلب المشاريع")
        return
    
    projects = data.get("data", [])
    
    if not projects:
        await update.message.reply_text("❌ لا توجد مشاريع متاحة حالياً")
        return

    message = "🏗️ *المشاريع المتاحة:*\n\n"
    for project in projects[:10]:
        message += f"🏢 *{project['title']}*\n"
        message += f"📍 {project.get('location', 'غير محدد')}\n"
        message += f"📊 الحالة: {project.get('status', 'نشط')}\n"
        message += "─" * 20 + "\n"

    await update.message.reply_text(message, parse_mode='Markdown')

# -------- Callback Handler --------
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data.split(":")

    if data[0] == "comp":
        company_slug = data[1]
        await q.edit_message_text(
            f"📋 اختر المشروع:",
            reply_markup=await projects_keyboard(company_slug)
        )

    elif data[0] == "proj":
        company_slug, project_id = data[1], int(data[2])
        kb = await units_keyboard(project_id)
        await q.edit_message_text(
            f"🏠 اختر الوحدة:",
            reply_markup=kb
        )

    elif data[0] == "unit":
        unit_id = int(data[1])
        data = await api_get(f"/units/{unit_id}")
        if not data.get("ok"):
            await q.edit_message_text("❌ حدث خطأ في جلب بيانات الوحدة.")
            return
        
        unit = data["data"]
        total_price = unit.get('sqm', 0) * unit.get('price_per_sqm', 0)
        
        msg = (
            f"🏠 *{unit.get('title', 'وحدة سكنية')}*\n\n"
            f"🔢 الكود: {unit.get('code', 'N/A')}\n"
            f"📏 المساحة: {unit.get('sqm', 0)} م²\n"
            f"💰 السعر/م²: {unit.get('price_per_sqm', 0):,} جنيه\n"
            f"💵 السعر الإجمالي: {total_price:,} جنيه\n"
            f"🏢 الطابق: {unit.get('floor', 'غير محدد')}\n"
            f"🛏️ الغرف: {unit.get('bedrooms', 0)}\n"
            f"🚿 الحمامات: {unit.get('bathrooms', 0)}\n"
            f"📊 الحالة: {unit.get('status', 'غير معروف')}"
        )
        await q.edit_message_text(msg, parse_mode='Markdown')

    elif data[0] == "back":
        if data[1] == "companies":
            await q.edit_message_text(
                "🏢 اختر الشركة:",
                reply_markup=await companies_keyboard()
            )
        elif data[1] == "projects":
            company_slug = data[2] if len(data) > 2 else ""
            await q.edit_message_text(
                f"📋 مشاريع الشركة:",
                reply_markup=await projects_keyboard(company_slug)
            )

# -------- Admin Commands --------
async def adminlogin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ ليس لديك صلاحية الدخول كأدمن")
        return
    
    resp = await api_post("/auth/login", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    if not resp.get("ok"):
        await update.message.reply_text("فشل الدخول كأدمن.")
        return
        
    ADMIN_TOKENS[chat_id] = resp["access_token"]
    await update.message.reply_text("✅ تم تسجيل الدخول كأدمن لهذا الشات.")

async def add_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ مسموح للإدارة فقط")
        return

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
        u = resp["data"]
        await update.message.reply_text(f"✅ تمت إضافة وحدة: {u['code']} (ID={u['id']})")
    else:
        await update.message.reply_text(f"❌ فشل: {resp.get('error')}")

async def delete_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف وحدة: /delete_unit <unit_id>"""
    chat_id = update.effective_chat.id
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ مسموح للإدارة فقط")
        return

    try:
        unit_id = int(context.args[0])
    except:
        await update.message.reply_text("الاستخدام: /delete_unit <unit_id>")
        return

    token = ADMIN_TOKENS.get(chat_id)
    if not token:
        await update.message.reply_text("⚠️ لازم تعمل /adminlogin أولاً.")
        return

    resp = await api_delete(f"/units/{unit_id}", token=token)
    if resp.get("ok"):
        await update.message.reply_text(f"✅ تم حذف الوحدة رقم {unit_id}")
    else:
        await update.message.reply_text(f"❌ فشل: {resp.get('error')}")

async def list_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع المشاريع: /list_projects"""
    chat_id = update.effective_chat.id
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ مسموح للإدارة فقط")
        return

    data = await api_get("/projects")
    if not data.get("ok"):
        await update.message.reply_text("❌ خطأ في جلب المشاريع")
        return
    
    projects = data.get("data", [])
    
    if not projects:
        await update.message.reply_text("❌ لا يوجد مشاريع")
        return

    message = "📋 المشاريع المتاحة:\n\n"
    for p in projects:
        message += f"🏢 {p['title']} (ID: {p['id']})\n"
        message += f"📍 {p.get('location', 'لا يوجد موقع')}\n"
        message += f"🔗 Slug: {p.get('slug', 'لا يوجد')}\n"
        message += "─" * 30 + "\n"

    await update.message.reply_text(message)

async def create_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إنشاء مشروع جديد: /create_project <company_slug> <slug> <title>"""
    chat_id = update.effective_chat.id
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ مسموح للإدارة فقط")
        return

    if len(context.args) < 3:
        await update.message.reply_text("الاستخدام: /create_project <company_slug> <slug> <title>")
        return

    company_slug, slug, title = context.args[0], context.args[1], " ".join(context.args[2:])
    
    token = ADMIN_TOKENS.get(chat_id)
    if not token:
        await update.message.reply_text("⚠️ لازم تعمل /adminlogin أولاً.")
        return

    resp = await api_post("/projects", token=token, data={
        "company_slug": company_slug,
        "slug": slug,
        "title": title
    })
    
    if resp.get("ok"):
        await update.message.reply_text(f"✅ تم إنشاء المشروع: {title}")
    else:
        await update.message.reply_text(f"❌ فشل: {resp.get('error')}")

# -------- Main --------
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", myid))
    application.add_handler(CommandHandler("projects", show_projects))
    application.add_handler(CommandHandler("adminlogin", adminlogin))
    application.add_handler(CommandHandler("add_unit", add_unit))
    application.add_handler(CommandHandler("delete_unit", delete_unit))
    application.add_handler(CommandHandler("list_projects", list_projects))
    application.add_handler(CommandHandler("create_project", create_project))
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Run
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
