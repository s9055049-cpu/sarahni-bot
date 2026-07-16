
import telebot
import sqlite3

TOKEN = '8853538663:AAEoQFVkHudDpQG9xtjc2G4aca6Mbm93EqI'
bot = telebot.TeleBot(TOKEN)

# إعداد قاعدة البيانات
def init_db():
    conn = sqlite3.connect('sarahni.db')
    conn.execute('PRAGMA journal_mode=WAL') # لحل مشكلة القفل
    cursor = conn.cursor()
    # جدول للرسائل وجدول للمحظورين
    cursor.execute('CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, text TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS banned (user_id INTEGER PRIMARY KEY)')
    conn.commit()
    conn.close()

init_db()

# دالة للتحقق من الحظر
def is_banned(user_id):
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM banned WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً! أنا بوت الملاحظات. أرسل رسالتك وسأحفظها.")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    # هنا يمكنك إضافة فحص إذا كان صاحب البوت فقط من يستخدم الأمر
    parts = message.text.split()
    if len(parts) > 1:
        user_to_ban = parts[1]
        conn = sqlite3.connect('sarahni.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO banned (user_id) VALUES (?)', (user_to_ban,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"تم حظر المستخدم: {user_to_ban}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "عذراً، أنت محظور من استخدام البوت.")
        return
    
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO feedback (text) VALUES (?)', (message.text,))
    conn.commit()
    conn.close()
    bot.reply_to(message, "تم استلام رسالتك.")

bot.polling()
