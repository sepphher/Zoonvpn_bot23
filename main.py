from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from fastapi import FastAPI
import threading
import uvicorn
import asyncio
import nest_asyncio

# FastAPI app برای باز نگه داشتن پورت در Render
web_app = FastAPI()

@web_app.get("/")
def root():
    return {"status": "Bot is running"}

# مراحل
NAME, PHONE, SIM_TYPE, MAIN_MENU, FEEDBACK, BUY_CONFIG, SELECT_CONFIG_TYPE, SELECT_DURATION, SELECT_GIG = range(9)

user_data_store = {}
admin_ids = [869171965, 7608339076]
admin_group_id = -1002740658219

main_menu_buttons = ReplyKeyboardMarkup([
    ["حساب کاربری من", "خرید کانفیگ جدید"],
    ["بررسی کانفینگ فعلی", "تست کانفینگ"],
    ["نقل و انتقادات", "ارتباط با پشتیبانی"],
    ["کانال ZONVPN"]
], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام به زون شاپ خوش آمدید.\nلطفاً نام و نام خانوادگی خود را وارد کنید:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id] = {"name": update.message.text}
    await update.message.reply_text("شماره موبایل خود را وارد کنید:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_user.id]["phone"] = update.message.text
    await update.message.reply_text("نوع اینترنت خود را وارد کنید (مثلاً ایرانسل / همراه اول / مودم خانگی):")
    return SIM_TYPE

async def get_sim_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data_store[user.id]["sim"] = update.message.text
    info = user_data_store[user.id]
    msg = f"🔔 کاربر جدید:\n👤 نام: {info['name']}\n📱 شماره: {info['phone']}\n🌐 نوع اینترنت: {info['sim']}"
    for admin in admin_ids:
        await context.bot.send_message(admin, msg)
    await context.bot.send_message(chat_id=admin_group_id, text=msg)
    await update.message.reply_text("از منوی زیر گزینه‌ای را انتخاب کنید:", reply_markup=main_menu_buttons)
    return MAIN_MENU

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "نقل و انتقادات":
        await update.message.reply_text("لطفاً پیام خود را ارسال کنید:")
        return FEEDBACK
    elif text == "خرید کانفینگ جدید":
        await update.message.reply_text("نوع کانفینگ را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup([
            ["کانفینگ برای گیم"], ["کانفینگ اینستا و وب گردی"], ["کانفینگ استریم"]
        ], resize_keyboard=True))
        return SELECT_CONFIG_TYPE
    elif text == "کانال ZONVPN":
        await update.message.reply_text("کانال: https://t.me/ZOONVPN")
    elif text == "ارتباط با پشتیبانی":
        await update.message.reply_text("پشتیبانی: @ZOONVPN_SUPPORT")
    elif text == "حساب کاربری من":
        user = user_data_store.get(update.effective_user.id, {})
        name = user.get("name", "نامشخص")
        phone = user.get("phone", "نامشخص")
        await update.message.reply_text(f"👤 نام: {name}\n📱 شماره: {phone}\nبرای تغییر شماره جدید را ارسال کنید:")
        return PHONE
    return MAIN_MENU

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"📩 انتقاد/پیشنهاد از {update.effective_user.full_name}:\n{update.message.text}"
    for admin in admin_ids:
        await context.bot.send_message(admin, msg)
    await context.bot.send_message(chat_id=admin_group_id, text=msg)
    await update.message.reply_text("✅ پیام شما ارسال شد. از همراهی شما متشکریم.", reply_markup=main_menu_buttons)
    return MAIN_MENU

async def handle_config_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['config_type'] = update.message.text
    await update.message.reply_text("مدت اشتراک را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup([
        ["یک ماهه"], ["سه ماهه"], ["شش ماهه"]
    ], resize_keyboard=True))
    return SELECT_DURATION

async def handle_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['duration'] = update.message.text
    await update.message.reply_text("حجم اشتراک را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup([
        ["10گیگ"], ["30گیگ"], ["50گیگ"], ["80گیگ"], ["120گیگ"]
    ], resize_keyboard=True))
    return SELECT_GIG

async def handle_gig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gig = update.message.text
    info = context.user_data
    summary = f"🛒 سفارش جدید از {update.effective_user.full_name}:\n📦 نوع: {info['config_type']}\n⏳ مدت: {info['duration']}\n💾 حجم: {gig}"
    for admin in admin_ids:
        await context.bot.send_message(admin, summary)
    await context.bot.send_message(chat_id=admin_group_id, text=summary)
    await update.message.reply_text("✅ درخواست ثبت شد. پس از تایید، کانفیگ ارسال می‌شود.", reply_markup=main_menu_buttons)
    return MAIN_MENU

def start_bot():
    app = ApplicationBuilder().token("7941595925:AAFTGXlI7Eco3prvsLcWYQb4oAkEq548F4w").build()

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
            SELECT_GIG: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gig)]
        },
        fallbacks=[]
    )
    app.add_handler(conv_handler)

    nest_asyncio.apply()
    asyncio.run(app.run_polling())

threading.Thread(target=start_bot).start()

if __name__ == "__main__":
    uvicorn.run(web_app, host="0.0.0.0", port=10000)