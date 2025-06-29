
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, CallbackQueryHandler, ContextTypes, ConversationHandler
)

import os

TOKEN = os.getenv("TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

# Bosqichlar
SELECT_TYPE, GET_NAME, GET_MESSAGE = range(3)

# Admin kimga javob yozayotganini eslab turish uchun
user_data_store = {}

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Admin bo‘lsa, alohida salom
    if user_id == ADMIN_CHAT_ID:
        await update.message.reply_text("Assalomu alaykum, Direktor! bu bot orqali sizga murojaatlar keladi.")

    # Reply (quyi) menyu tugmalari
    reply_keyboard = [
        ["📝 Yangi murojaat", "ℹ️ Yordam"]
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    # Inline murojaat turlari
    keyboard = [
        [InlineKeyboardButton("📢 Shikoyat", callback_data='Shikoyat')],
        [InlineKeyboardButton("💡 Taklif", callback_data='Taklif')],
        [InlineKeyboardButton("❓ Savol", callback_data='Savol')],
        [InlineKeyboardButton("📝 Ariza", callback_data='Ariza')],
        [InlineKeyboardButton("📄 Rahbariyatga murojaat", callback_data='Direktorga murojaat')],
    ]

    await update.message.reply_text(
        "Salom! Iltimos, murojaat turini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # Reply menyuni ko‘rsatish
    
    return SELECT_TYPE

# Murojaat turi tanlangach
async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['type'] = query.data
    await query.message.reply_text("Iltimos, ismingiz va familiyangizni yozing:")
    return GET_NAME

# Ism familya bosqichi
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Endi murojaatingizni yozing:")
    return GET_MESSAGE

# Murojaat matnini yuborish
async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['message'] = update.message.text
    user = update.message.from_user
    chat_id = update.message.chat_id

    # Yuboruvchi havolasi
    profile_link = f'<a href="tg://user?id={chat_id}">{context.user_data["name"]}</a>'

    # Adminga yuboriladigan matn
    full_text = (
        f"📬 <b>Yangi murojaat!</b>\n\n"
        f"👤 <b>Ismi:</b> {context.user_data['name']}\n"
        f"🆔 <b>Telegram ID:</b> <code>{chat_id}</code>\n"
        f"🔗 <b>Profil havola:</b> {profile_link}\n"
        f"📌 <b>Murojaat turi:</b> {context.user_data['type']}\n"
        f"💬 <b>Username:</b> @{user.username if user.username else 'yo‘q'}\n\n"
        f"📝 <b>Murojaat matni:</b>\n{context.user_data['message']}"
    )

    # Adminga tugma: faqat "Javob yozish"
    keyboard = [
        [InlineKeyboardButton("✍️ Javob yozish", callback_data=f"reply:{chat_id}")]
    ]

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=full_text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("✅ Murojaatingiz yuborildi.")
    return ConversationHandler.END

# Admin "Javob yozish" tugmasini bosganda
async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, user_id = query.data.split(":")
    user_id = int(user_id)

    if action == "reply":
        await query.message.reply_text("✍️ Iltimos, foydalanuvchiga yuboriladigan javobni yozing:")
        user_data_store[query.from_user.id] = user_id

# Admin matn yuboradi — foydalanuvchiga yetkaziladi
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from_id = update.message.from_user.id
    if from_id in user_data_store:
        to_user = user_data_store.pop(from_id)
        await context.bot.send_message(
            chat_id=to_user,
            text=f"📩 Sizga kelgan javob:\n\n{update.message.text}"
        )
        await update.message.reply_text("✅ Javob foydalanuvchiga yuborildi.")
    else:
        await update.message.reply_text("⚠️ Siz hozir hech kimga javob yozish rejimida emassiz.")

# Cancel komandasi
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Murojaat bekor qilindi.")
    return ConversationHandler.END

# Botni ishga tushurish
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    # Muloqot bosqichlari
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_TYPE: [CallbackQueryHandler(select_type)],
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Qo‘shimcha handlerlar
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_admin_action, pattern='^reply:'))
    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(chat_id=ADMIN_CHAT_ID), handle_admin_reply))

    print("🤖 Murojaat bot ishga tushdi...")
    app.run_polling()
