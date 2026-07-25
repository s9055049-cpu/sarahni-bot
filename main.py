
import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# التوكن الخاص ببوتك والـ ID الخاص بكِ
TOKEN = "8682801321:AAH6D6o_A6-4JLhbLP5aNCOWoa4Afo0gv7k"
MY_ADMIN_ID = 8820368378

# 1. إنشاء سيرفر فلاسك وهمي عشان نرضي رندر والبورتات
app = Flask('')

@app.route('/')
def home():
    return "البوت شغال 100%!"

def run_flask():
    # رندر بيعطيني رقم بورت تلقائي، بنقرأه وبنفتح عليه
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# 2. دالة استقبال وصناعة رسائل الصراحة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        sender_id = update.message.from_user.id
        sender_username = update.message.from_user.username
        message_text = update.message.text

        # رد للمرسل
        await update.message.reply_text("تم إرسال صراحتك بنجاح 🥷✨")

        # إعادة توجيه الرسالة لكِ
        forward_text = f"وصلتك صراحة جديدة! 💌\n\n- النص: {message_text}\n- ايدي المرسل: {sender_id}"
        if sender_username:
            forward_text += f"\n- اليوزر: @{sender_username}"
            
        await context.bot.send_message(chat_id=MY_ADMIN_ID, text=forward_text)

def main():
    # تشغيل سيرفر الفلاسك في الخلفية عشان يفتح البورت وما يعطي رندر إيرور
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # بناء تطبيق تليجرام بوت
    application = ApplicationBuilder().token(TOKEN).build()

    # إضافة مستقبل الرسائل
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # تشغيل البوت
    application.run_polling()

if __name__ == '__main__':
    main()
