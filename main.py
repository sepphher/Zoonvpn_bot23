from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from fastapi import FastAPI
import threading
import nest_asyncio
import asyncio
import uvicorn

# مراحل مکالمه
NAME, PHONE, SIM_TYPE, MAIN_MENU, FEEDBACK, SELECT_CONFIG_TYPE, SELECT_DURATION, SELECT_GIG = range(9)

# اطلاعات ادمین و گروه
admin_ids = [869171965, 7608339076]
admin_group_id = -1002740658219
user_data_store = {}

# منوی اصلی
main_menu_buttons = ReplyKeyboardMarkup([
    ["حساب کاربری من", "خرید کانفیگ جدید"],
    ["بررسی کانفینگ فعلی", "تست کانفینگ"],
    ["نقل و انتقادات", "ارتباط با پشتیبانی"],
    ["کانال ZONVPN"]
], resize_keyboard=True)

# هندلرها
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! نام و نام خانوادگی خود را وارد کنید:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id] = {"name": update.message.text}
    await update.message.reply_text("شماره تلفن خود را وارد کنید:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["phone"] = update.message.text
    await update.message.reply_text("نوع اینترنت (همراه اول، ایرانسل...):")
    return SIM_TYPE

async def get_sim_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data_store[uid]["sim"] = update.message.text
    info = user_data_store[uid]
    msg = f"👤 نام: {info['name']}\n📞 تلفن: {info['phone']}\n🌐 اینترنت: {info['sim']}"
    for admin in admin_ids:
        await context.bot.send_message(chat_id=admin, text=msg)
    await context.bot.send_message(chat_id=admin_group_id, text=msg)
    await update.message.reply_text("از منو یکی را انتخاب کنید:", reply_markup=main_menu_buttons)
    return MAIN_MENU

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text
    if txt == "نقل و انتقادات":
        await update.message.reply_text("لطفا نظر خود را ارسال کنید:")
        return FEEDBACK
    elif txt == "خرید کانفیگ جدید":
        await update.message.reply_text("نوع کانفینگ را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup([
            ["گیم"], ["استریم"], ["وب‌گردی"]
        ], resize_keyboard=True))
        return SELECT_CONFIG_TYPE
    elif txt == "کانال ZONVPN":
        await update.message.reply_text("عضویت در کانال: https://t.me/ZOONVPN")
    elif txt == "ارتباط با پشتیبانی":
        await update.message.reply_text("پشتیبانی: @ZOONVPN_SUPPORT")
    elif txt == "حساب کاربری من":
        info = user_data_store.get(update.effective_user.id, {})
        await update.message.reply_text(f"👤 {info.get('name', '-')}\n📞 {info.get('phone', '-')}")
        return MAIN_MENU
    return MAIN_MENU

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"📩 انتقاد از {update.effective_user.full_name}:\n{update.message.text}"
    for admin in admin_ids:
        await context.bot.send_message(admin, msg)
    await update.message.reply_text("✅ ارسال شد.", reply_markup=main_menu_buttons)
    return MAIN_MENU

async def handle_config_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['type'] = update.message.text
    await update.message.reply_text("مدت زمان:", reply_markup=ReplyKeyboardMarkup([
        ["1 ماهه"], ["3 ماهه"], ["6 ماهه"]
    ], resize_keyboard=True))
    return SELECT_DURATION

async def handle_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['duration'] = update.message.text
    await update.message.reply_text("حجم کانفینگ:", reply_markup=ReplyKeyboardMarkup([
        ["10گیگ"], ["30گیگ"], ["50گیگ"]
    ], resize_keyboard=True))
    return SELECT_GIG

async def handle_gig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gig = update.message.text
    info = context.user_data
    msg = f"🛒 سفارش:\nنوع: {info['type']}\nمدت: {info['duration']}\nحجم: {gig}"
    for admin in admin_ids:
        await context.bot.send_message(admin, msg)
    await update.message.reply_text("✅ ثبت شد", reply_markup=main_menu_buttons)
    return MAIN_MENU

# اجرای ربات و وب‌سرویس
def start_bot():
    app = ApplicationBuilder().token("توکن_خودت_را_اینجا_بذار").build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            SIM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sim_type)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
            FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback)],
            SELECT_CONFIG_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_config_type)],
            SELECT_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_duration)],
            SELECT_GIG: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gig)],
        },
        fallbacks=[]
    )
    app.add_handler(conv_handler)
    asyncio.run(app.run_polling())

# FastAPI برای باز شدن پورت
web_app = FastAPI()
@web_app.get("/")
def read_root():
    return {"message": "Bot is running!"}

if __name__ == "__main__":
    nest_asyncio.apply()
    threading.Thread(target=start_bot).start()
    uvicorn.run(web_app, host="0.0.0.0", port=10000)
