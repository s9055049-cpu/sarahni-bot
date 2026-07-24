
import telebot
import sqlite3
from flask import Flask
from threading import Thread

# 1. إعداد Flask لتمويه Render ومنع إغلاق البوت
app = Flask('')
@app.route('/')
def home():
    return "البوت يعمل!"

def run():
    app.run(host='0.0.0.0', port=8080)

# 2. إعداد البوت مع التوكن الخاص بكِ
TOKEN = '8682801321:AAH6D6o_A6-4JLhbLP5aNCOWoa4Afo0gv7k' 
bot = telebot.TeleBot(TOKEN)

# 3. إعداد قاعدة البيانات وجداول الرسائل والحظر
def init_db():
    conn = sqlite3.connect('sarahni.db')
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            text TEXT,
            user_id INTEGER,
            username TEXT
        )
    ''')
    cursor.execute('CREATE TABLE IF NOT EXISTS banned (user_id INTEGER PRIMARY KEY)')
    conn.commit()
    conn.close()

init_db()

# 4. دالة التحقق من الحظر
def is_banned(user_id):
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM banned WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك في بوت الملاحظات!")

@bot.message_handler(commands=['ban'])
def ban_user(message):
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
        bot.reply_to(message, "عذراً، أنت محظور.")
        return
    
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # التحقق من وجود يوزر أو كتابة "لا يوجد يوزر"
    if username:
        username_display = f"@{username}"
    else:
        username_display = "لا يوجد يوزر"

    # حفظ الرسالة مع اليوزر والآي دي في قاعدة البيانات
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO feedback (text, user_id, username) VALUES (?, ?, ?)', 
                   (message.text, user_id, username_display))
    conn.commit()
    conn.close()

    bot.reply_to(message, "تم استلام رسالتك بنجاح.")
    
    # لطباعة معلومات الشخص مباشرة في الـ Logs على Render لرؤيتها بوضوح
    print(f"رسالة جديدة! الاسم: {first_name} | اليوزر: {username_display} | الـ ID: {user_id} | النص: {message.text}")

# 5. تشغيل الخادم والبوت معاً
if __name__ == '__main__':
    Thread(target=run).start()
    bot.infinity_polling()
