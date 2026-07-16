
import telebot
import sqlite3
from telebot import types

# 1. الإعدادات
API_TOKEN = '8853538663:AAEoQFVkHudDpQG9xtjc2G4aca6Mbm93EqI'
ADMIN_ID = 8820368378
bot = telebot.TeleBot(API_TOKEN)

# 2. تهيئة قاعدة البيانات
def init_db():
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    # جدول المستخدمين
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, last_target_id INTEGER)''')
    # جدول الحظر
    cursor.execute('''CREATE TABLE IF NOT EXISTS blocks 
                      (blocker_id INTEGER, blocked_id INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# 3. التعامل مع أمر البداية
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    text = message.text.split()
    
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO users (user_id, username, full_name, last_target_id) VALUES (?, ?, ?, (SELECT last_target_id FROM users WHERE user_id = ?))', 
                   (chat_id, message.from_user.username, message.from_user.first_name, chat_id))
    
    if len(text) > 1:
        target_id = text[1]
        if str(target_id) == str(chat_id):
            bot.send_message(chat_id, "❌ لا يمكنك مصارحة نفسك!")
        else:
            cursor.execute('UPDATE users SET last_target_id = ? WHERE user_id = ?', (target_id, chat_id))
            bot.send_message(chat_id, "✅ تم تحديد الشخص! الآن كل رسالة ترسلها هنا ستصل إليه مباشرة. أكتب رسالتك:")
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔗 إنشاء رابط الصراحة الخاص بي"))
        bot.send_message(chat_id, "أهلاً بك! يمكنك الآن مراسلة من حددته سابقاً، أو إنشاء رابطك الخاص.", reply_markup=markup)
    
    conn.commit()
    conn.close()

# 4. معالجة الرسائل العادية
@bot.message_handler(func=lambda message: message.text != "🔗 إنشاء رابط الصراحة الخاص بي")
def handle_all_messages(message):
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    cursor.execute('SELECT last_target_id FROM users WHERE user_id = ?', (message.chat.id,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        send_sarahni_message(message, result[0])
    else:
        bot.send_message(message.chat.id, "لم تقم بتحديد شخص للمصارحة. يرجى الدخول عبر رابط الصراحة الخاص به أولاً.")

# 5. دالة إرسال الرسالة مع الحظر
def send_sarahni_message(message, target_id):
    sender_id = message.chat.id
    msg_text = message.text
    
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    # هل المرسل محظور؟
    cursor.execute('SELECT * FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (target_id, sender_id))
    if cursor.fetchone():
        bot.send_message(sender_id, "❌ لا يمكنك المراسلة، لقد قام هذا الشخص بحظرك.")
        conn.close()
        return
    conn.close()

    # أزرار التحكم
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚫 حظر المرسل", callback_data=f"block_{sender_id}"))
    markup.add(types.InlineKeyboardButton("✅ إلغاء الحظر", callback_data=f"unblock_{sender_id}"))

    try:
        bot.send_message(target_id, f"📥 **رسالة صراحة جديدة:**\n\n{msg_text}", parse_mode='Markdown', reply_markup=markup)
        bot.send_message(sender_id, "تم إرسال رسالتك بنجاح! 🤫")
    except:
        bot.send_message(sender_id, "❌ فشل الإرسال، ربما قام المستخدم بحظر البوت.")

# 6. معالجة الأزرار (الحظر وإلغاء الحظر)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    blocker_id = call.message.chat.id
    action, blocked_id = call.data.split('_')
    
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    if action == "block":
        cursor.execute('INSERT OR IGNORE INTO blocks VALUES (?, ?)', (blocker_id, blocked_id))
        bot.answer_callback_query(call.id, "🚫 تم الحظر!")
    elif action == "unblock":
        cursor.execute('DELETE FROM blocks WHERE blocker_id = ? AND blocked_id = ?', (blocker_id, blocked_id))
        bot.answer_callback_query(call.id, "✅ تم إلغاء الحظر!")
    conn.commit()
    conn.close()

@bot.message_handler(func=lambda message: message.text == "🔗 إنشاء رابط الصراحة الخاص بي")
def create_link(message):
    bot_info = bot.get_me()
    user_link = f"https://t.me/{bot_info.username}?start={message.chat.id}"
    bot.send_message(message.chat.id, f"الرابط الخاص بك:\n`{user_link}`", parse_mode='Markdown')

bot.remove_webhook()
bot.infinity_polling()
