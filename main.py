
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# التوكن الخاص ببوتك والـ ID الخاص بكِ
TOKEN = "8682801321:AAH6D6o_A6-4JLhbLP5aNCOWoa4Afo0gv7k"
MY_ADMIN_ID = 8820368378

# دالة التعامل مع الرسائل الواردة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        sender_id = update.message.from_user.id
        sender_username = update.message.from_user.username
        message_text = update.message.text

        # رد للمرسل بأن صراحته وصلت
        await update.message.reply_text("تم إرسال صراحتك بنجاح 🥷✨")

        # إعادة توجيه الرسالة لكِ على حسابك الشخصي
        forward_text = f"وصلتك صراحة جديدة! 💌\n\n- النص: {message_text}\n- ايدي المرسل: {sender_id}"
        if sender_username:
            forward_text += f"\n- اليوزر: @{sender_username}"
            
        await context.bot.send_message(chat_id=MY_ADMIN_ID, text=forward_text)

def main():
    # بناء تطبيق تليجرام بوت
    application = ApplicationBuilder().token(TOKEN).build()

    # إضافة مستقبل الرسائل النصية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # بدء تشغيل البوت مباشرة
    application.run_polling()

if __name__ == '__main__':
    main()
