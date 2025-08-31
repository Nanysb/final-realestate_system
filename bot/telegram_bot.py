# bot/telegram_bot.py - الإصدار المصحح والمحدث
import json
import logging
import os
import asyncio
import signal
import sys
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config_bot.json")

# تحميل الإعدادات
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CFG = json.load(f)
except FileNotFoundError:
    print(f"❌ ملف الإعدادات {CONFIG_PATH} غير موجود")
    sys.exit(1)

BOT_TOKEN = CFG.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN غير موجود في ملف الإعدادات")
    sys.exit(1)

API = CFG.get("API_BASE_URL", "http://localhost:5000/api").rstrip("/")
ADMIN_USER = CFG.get("ADMIN_USERNAME")
ADMIN_PASS = CFG.get("ADMIN_PASSWORD")
ADMIN_CHAT_IDS = CFG.get("ADMIN_CHAT_IDS", [])

ADMIN_TOKENS = {}
client = httpx.AsyncClient(timeout=30.0)  # زيادة المهلة

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_admin(chat_id):
    return str(chat_id) in [str(cid) for cid in ADMIN_CHAT_IDS]

async def api_request(method, path, params=None, data=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if data and not (isinstance(data, dict) or isinstance(data, list)):
        headers["Content-Type"] = "application/json"
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                pass
    
    url = f"{API}{path}"
    
    try:
        if method == "GET":
            response = await client.get(url, params=params, headers=headers)
        elif method == "POST":
            response = await client.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = await client.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            return {"ok": False, "error": "Invalid method"}
        
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"API Request Error: {e}")
        return {"ok": False, "error": f"Request error: {str(e)}"}
    except httpx.HTTPStatusError as e:
        logger.error(f"API HTTP Error: {e.response.status_code} - {e.response.text}")
        return {"ok": False, "error": f"HTTP error: {e.response.status_code}"}
    except Exception as e:
        logger.error(f"API General Error: {e}")
        return {"ok": False, "error": f"General error: {str(e)}"}

async def api_get(path, params=None, token=None):
    return await api_request("GET", path, params=params, token=token)

async def api_post(path, data=None, token=None):
    return await api_request("POST", path, data=data, token=token)

async def api_put(path, data=None, token=None):
    return await api_request("PUT", path, data=data, token=token)

async def api_delete(path, token=None):
    return await api_request("DELETE", path, token=token)

async def companies_keyboard():
    try:
        data = await api_get("/companies")
        if not data or not data.get("ok"):
            logger.error("Failed to fetch companies: %s", data.get("error", "Unknown error"))
            return InlineKeyboardMarkup([[InlineKeyboardButton("❌ خطأ في جلب البيانات", callback_data="noop")]])
        
        companies = data.get("data", [])
        logger.info(f"Found {len(companies)} companies")
        
        buttons = [
            [InlineKeyboardButton(c.get("name", "Unknown"), callback_data=f"comp:{c.get('slug', '')}")]
            for c in companies
        ]
        return InlineKeyboardMarkup(buttons or [[InlineKeyboardButton("لا يوجد شركات", callback_data="noop")]])
    except Exception as e:
        logger.error(f"Error in companies_keyboard: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ خطأ في جلب البيانات", callback_data="noop")]])

async def projects_keyboard(company_slug: str):
    data = await api_get(f"/projects", params={"company_slug": company_slug})
    if not data or not data.get("ok"):
        logger.error("Failed to fetch projects for company %s: %s", company_slug, data.get("error", "Unknown error"))
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ خطأ في جلب البيانات", callback_data="back:companies")]])
    
    projects = data.get("data", [])
    
    buttons = [
        [InlineKeyboardButton(p.get("title", "Unknown"), callback_data=f"proj:{company_slug}:{p.get('id', '')}")]
        for p in projects
    ]
    buttons.append([InlineKeyboardButton("⬅ رجوع", callback_data="back:companies")])
    return InlineKeyboardMarkup(buttons or [[InlineKeyboardButton("لا يوجد مشاريع", callback_data="back:companies")]])

async def units_keyboard(project_id: int):
    data = await api_get("/units", params={"project_id": project_id})
    if not data or not data.get("ok"):
        logger.error("Failed to fetch units for project %s: %s", project_id, data.get("error", "Unknown error"))
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ خطأ في جلب البيانات", callback_data=f"back:projects")]])
    
    units = data.get("data", [])
    buttons = []
    for u in units:
        total_price = u.get('sqm', 0) * u.get('price_per_sqm', 0)
        label = f"{u.get('code', 'N/A')} | {u.get('sqm', 0)}م² | {total_price:,} ج"
        buttons.append([InlineKeyboardButton(label, callback_data=f"unit:{u.get('id', '')}")])
    
    buttons.append([InlineKeyboardButton("⬅ رجوع", callback_data=f"back:projects")])
    return InlineKeyboardMarkup(buttons or [[InlineKeyboardButton("لا يوجد وحدات", callback_data=f"back:projects")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "أهلاً بك 👋\nاختر الشركة لعرض المشاريع:",
        reply_markup=await companies_keyboard()
    )

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    is_admin_user = is_admin(chat_id)
    
    message = f"🆔 Chat ID الخاص بك: `{chat_id}`\n"
    message += f"👤 حالة الأدمن: {'✅ أدمن' if is_admin_user else '❌ مستخدم عادي'}\n\n"
    message += "🔧 إذا كنت أدمن، أضف هذا الرقم إلى ADMIN_CHAT_IDS في config_bot.json"
    
    await update.message.reply_text(message, parse_mode='Markdown')

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
        if not data or not data.get("ok"):
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
        
        # إضافة الصور إذا كانت متاحة
        images = unit.get('images', [])
        if images:
            # نرسل أول صورة كمثال
            try:
                image_url = f"{API}/uploads/{images[0]}"
                await context.bot.send_photo(
                    chat_id=q.message.chat_id,
                    photo=image_url,
                    caption=msg,
                    parse_mode='Markdown'
                )
                await q.delete_message()
            except Exception as e:
                logger.error(f"Error sending image: {e}")
                await q.edit_message_text(msg + f"\n\n❌ تعذر تحميل الصورة: {e}", parse_mode='Markdown')
        else:
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

async def adminlogin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ ليس لديك صلاحية الدخول كأدمن")
        return
    
    if not ADMIN_USER or not ADMIN_PASS:
        await update.message.reply_text("❌ إعدادات الأدمن غير مكتملة في config_bot.json")
        return
    
    resp = await api_post("/auth/login", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    if not resp or not resp.get("ok"):
        error_msg = resp.get("error", "Unknown error") if resp else "No response"
        await update.message.reply_text(f"فشل الدخول كأدمن: {error_msg}")
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
    
    if resp and resp.get("ok"):
        u = resp["data"]
        await update.message.reply_text(f"✅ تمت إضافة وحدة: {u.get('code', 'N/A')} (ID={u.get('id', 'N/A')})")
    else:
        error_msg = resp.get("error", "Unknown error") if resp else "No response"
        await update.message.reply_text(f"❌ فشل: {error_msg}")

async def delete_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if resp and resp.get("ok"):
        await update.message.reply_text(f"✅ تم حذف الوحدة رقم {unit_id}")
    else:
        error_msg = resp.get("error", "Unknown error") if resp else "No response"
        await update.message.reply_text(f"❌ فشل: {error_msg}")

async def list_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if not is_admin(chat_id):
        await update.message.reply_text("❌ مسموح للإدارة فقط")
        return

    data = await api_get("/projects")
    if not data or not data.get("ok"):
        await update.message.reply_text("❌ خطأ في جلب المشاريع")
        return
    
    projects = data.get("data", [])
    
    if not projects:
        await update.message.reply_text("❌ لا يوجد مشاريع")
        return

    message = "📋 المشاريع المتاحة:\n\n"
    for p in projects:
        message += f"🏢 {p.get('title', 'N/A')} (ID: {p.get('id', 'N/A')})\n"
        message += f"📍 {p.get('location', 'لا يوجد موقع')}\n"
        message += f"🔗 Slug: {p.get('slug', 'لا يوجد')}\n"
        message += "─" * 30 + "\n"

    await update.message.reply_text(message)

async def create_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    if resp and resp.get("ok"):
        await update.message.reply_text(f"✅ تم إنشاء المشروع: {title}")
    else:
        error_msg = resp.get("error", "Unknown error") if resp else "No response"
        await update.message.reply_text(f"❌ فشل: {error_msg}")

async def refresh_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر جديد لتحديث البيانات يدوياً"""
    chat_id = update.effective_chat.id
    await update.message.reply_text("🔄 جاري تحديث البيانات...")
    
    # إعادة تحميل الإعدادات
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            global CFG, ADMIN_CHAT_IDS
            CFG = json.load(f)
            ADMIN_CHAT_IDS = CFG.get("ADMIN_CHAT_IDS", [])
    except Exception as e:
        logger.error(f"Error reloading config: {e}")
    
    await update.message.reply_text("✅ تم تحديث البيانات والإعدادات")

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN غير موجود")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", myid))
    application.add_handler(CommandHandler("adminlogin", adminlogin))
    application.add_handler(CommandHandler("add_unit", add_unit))
    application.add_handler(CommandHandler("delete_unit", delete_unit))
    application.add_handler(CommandHandler("list_projects", list_projects))
    application.add_handler(CommandHandler("create_project", create_project))
    application.add_handler(CommandHandler("refresh", refresh_data))
    application.add_handler(CallbackQueryHandler(handle_callback))

    print("✅ البوت يعمل الآن...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()