
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

# 2. إعداد البوت والتوكن الخاص بكِ
TOKEN = '8682801321:AAH6D6o_A6-4JLhbLP5aNCOWoa4Afo0gv7k' 
bot = telebot.TeleBot(TOKEN)

# الـ ID الخاص بكِ لتصلكِ الإشعارات فوراً
ADMIN_ID = 8820368378

# 3. إعداد قاعدة البيانات
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

def is_banned(user_id):
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM banned WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك في بوت الملاحظات والرسائل السرية!")

# أمر خاص بكِ لمشاهدة جميع الرسائل المحفوظة
@bot.message_handler(commands=['show'])
def show_messages(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, username, text FROM feedback')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        bot.reply_to(message, "لا توجد رسائل مخزنة حتى الآن.")
        return

    response = "📩 **جميع الرسائل المستلمة:**\n\n"
    for row in rows:
        response += f"🆔 **الآي دي:** `{row[1]}`\n👤 **اليوزر:** {row[2]}\n💬 **الرسالة:** {row[3]}\n-------------------\n"
    
    bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
        
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
    # إذا كنتِ أنتِ من ترسلين للبوت، فلا نحسبها رسالة واردة
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "أهلاً بكِ يا ملكة، هذه رسالتكِ الخاصة.")
        return

    if is_banned(message.from_user.id):
        bot.reply_to(message, "عذراً، أنت محظور.")
        return
    
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    username_display = f"@{username}" if username else "لا يوجد يوزر"

    # 1. حفظ الرسالة في قاعدة البيانات
    conn = sqlite3.connect('sarahni.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO feedback (text, user_id, username) VALUES (?, ?, ?)', 
                   (message.text, user_id, username_display))
    conn.commit()
    conn.close()

    # 2. الرد على الشخص الذي أرسل الرسالة
    bot.reply_to(message, "تم استلام رسالتك بنجاح.")

    # 3. إرسال الإشعار الفوري لكِ أنتِ شخصياً على الخاص
    admin_alert = f"📥 **رسالة جديدة!**\n\n👤 **الاسم:** {first_name}\n🏷️ **اليوزر:** {username_display}\n🆔 **الـ ID:** `{user_id}`\n💬 **النص:** {message.text}"
    try:
        bot.send_message(ADMIN_ID, admin_alert, parse_mode="Markdown")
    except Exception as e:
        print(f"خطأ في إرسال الإشعار للآدمن: {e}")

if __name__ == '__main__':
    Thread(target=run).start()
    bot.infinity_polling()
