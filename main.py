
import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# التوكن الخاص ببوتك والـ ID الخاص بكِ
TOKEN = "8682801321:AAH6D6o_A6-4JLhbLP5aNCOWoa4Afo0gv7k"
MY_ADMIN_ID = 8820368378  # الآي دي الخاص بكِ لاستقبال الرسائل أو التحكم

# إعداد خادم الـ Flask ليبقى البوت مستيقظاً على Render
app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل بكفاءة!"

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# دالة التعامل مع الرسائل الواردة لبوت الصراحة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        sender_id = update.message.from_user.id
        sender_username = update.message.from_user.username
        message_text = update.message.text

        # رد للمرسل بأن رسالته وصلت
        await update.message.reply_text("تم إرسال صراحتك بنجاح 🥷✨")

        # إعادة توجيه الرسالة لكِ على حسابك الشخصي باستخدام الـ ID الخاص بكِ
        forward_text = f"وصلتك صراحة جديدة! 💌\n\n- النص: {message_text}\n- ايدي المرسل: {sender_id}"
        if sender_username:
            forward_text += f"\n- اليوزر: @{sender_username}"
            
        await context.bot.send_message(chat_id=MY_ADMIN_ID, text=forward_text)

def main():
    # تشغيل خادم الـ Flask في خلفية مستقلة (Threading) حتى يعمل مع البت بصورة طبيعية
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # بناء تطبيق تليجرام بوت
    application = ApplicationBuilder().token(TOKEN).build()

    # إضافة مستقبل الرسائل النصية (ما عدا الأوامر مثل /start)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # بدء تشغيل البوت بنظام الـ Polling
    application.run_polling()

if __name__ == '__main__':
    main()
