
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = "8682801321:AAH6D6o_A6-4JLhbLP5aNCOWoa4Afo0gv7k"
MY_ADMIN_ID = 8820368378

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        sender_id = update.message.from_user.id
        sender_username = update.message.from_user.username
        message_text = update.message.text

        await update.message.reply_text("تم إرسال صراحتك بنجاح 🥷✨")

        forward_text = f"وصلتك صراحة جديدة! 💌\n\n- النص: {message_text}\n- ايدي المرسل: {sender_id}"
        if sender_username:
            forward_text += f"\n- اليوزر: @{sender_username}"
            
        await context.bot.send_message(chat_id=MY_ADMIN_ID, text=forward_text)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
