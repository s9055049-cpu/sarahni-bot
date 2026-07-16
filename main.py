
import telebot
import sqlite3
from telebot import types
import html

API_TOKEN = "8853538663:AAEoQFVkHudDpQG9xtjc2G4aca6Mbm93EqI"
ADMIN_ID = 8820368378

bot = telebot.TeleBot(API_TOKEN)


# =========================
# قاعدة البيانات
# =========================

def db():
    return sqlite3.connect("sarahni.db")


def init_db():

    conn = db()
    cur = conn.cursor()

    # المستخدمين
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT
    )
    """)

    # الجلسات النشطة
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        sender_id INTEGER PRIMARY KEY,
        target_id INTEGER
    )
    """)

    # الحظر
    cur.execute("""
    CREATE TABLE IF NOT EXISTS blocked (
        owner_id INTEGER,
        sender_id INTEGER,
        PRIMARY KEY(owner_id, sender_id)
    )
    """)

    # آخر مرسل لكل مستخدم
    cur.execute("""
    CREATE TABLE IF NOT EXISTS last_sender (
        owner_id INTEGER PRIMARY KEY,
        sender_id INTEGER
    )
    """)


    conn.commit()
    conn.close()



init_db()



# =========================
# حفظ المستخدم
# =========================

def save_user(message):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?, ?)",
        (
            message.chat.id,
            message.from_user.username,
            message.from_user.first_name
        )
    )

    conn.commit()
    conn.close()



# =========================
# بداية البوت
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    save_user(message)

    args = message.text.split()


    # دخول من رابط شخص
    if len(args) > 1:

        target = int(args[1])

        if target == message.chat.id:
            bot.send_message(
                message.chat.id,
                "❌ لا يمكنك إرسال رسالة لنفسك"
            )
            return


        conn = db()
        cur = conn.cursor()

        cur.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?,?)",
            (
                message.chat.id,
                target
            )
        )

        conn.commit()
        conn.close()


        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        keyboard.add(
            types.KeyboardButton(
                "⛔ إيقاف المصارحة"
            )
        )


        bot.send_message(
            message.chat.id,
            "✍️ تم فتح المصارحة\n"
            "أرسل رسائلك الآن بدون فتح الرابط مرة ثانية 🤫",
            reply_markup=keyboard
        )

        return



    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        types.KeyboardButton(
            "🔗 إنشاء رابط الصراحة الخاص بي"
        )
    )


    bot.send_message(
        message.chat.id,
        "🤖 أهلاً بك في بوت صارحني\n\n"
        "أنشئ رابطك واستقبل الرسائل بسرية 🔒",
        reply_markup=keyboard
    )



# =========================
# إنشاء الرابط
# =========================

@bot.message_handler(
    func=lambda m: m.text=="🔗 إنشاء رابط الصراحة الخاص بي"
)
def create_link(message):

    me = bot.get_me()

    link = (
        f"https://t.me/{me.username}"
        f"?start={message.chat.id}"
    )


    bot.send_message(
        message.chat.id,
        f"🔗 رابطك:\n\n<code>{link}</code>",
        parse_mode="HTML"
        # =========================
# إيقاف المصارحة
# =========================

@bot.message_handler(
    func=lambda m: m.text == "⛔ إيقاف المصارحة"
)
def stop_session(message):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM sessions WHERE sender_id=?",
        (message.chat.id,)
    )

    conn.commit()
    conn.close()


    bot.send_message(
        message.chat.id,
        "✅ تم إيقاف المصارحة",
        reply_markup=types.ReplyKeyboardRemove()
    )



# =========================
# استقبال الرسائل
# =========================

@bot.message_handler(func=lambda m: True)
def receive_message(message):

    sender_id = message.chat.id
    text = message.text


    conn = db()
    cur = conn.cursor()


    # معرفة إذا عنده جلسة
    cur.execute(
        "SELECT target_id FROM sessions WHERE sender_id=?",
        (sender_id,)
    )

    session = cur.fetchone()


    if not session:
        conn.close()
        return


    target_id = session[0]


    # فحص الحظر
    cur.execute(
        "SELECT * FROM blocked WHERE owner_id=? AND sender_id=?",
        (target_id, sender_id)
    )

    blocked = cur.fetchone()


    if blocked:

        conn.close()

        bot.send_message(
            sender_id,
            "❌ لا يمكنك إرسال رسائل لهذا الشخص"
        )

        return



    # حفظ آخر مرسل
    cur.execute(
        "INSERT OR REPLACE INTO last_sender VALUES (?,?)",
        (target_id, sender_id)
    )


    conn.commit()
    conn.close()



    # أزرار الحظر
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "🚫 حظر المرسل",
            callback_data=f"block_{sender_id}"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "✅ فك حظر آخر شخص",
            callback_data="unblock"
        )
    )


    # إرسال للمستلم بدون كشف الهوية
    bot.send_message(
        target_id,
        f"📥 رسالة صراحة جديدة:\n\n"
        f"💬 {html.escape(text)}",
        parse_mode="HTML",
        reply_markup=keyboard
    )



    # تقرير لك
    user = message.from_user

    report = (
        "🕵️ تقرير صراحة\n\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🔗 اليوزر: @{user.username if user.username else 'لا يوجد'}\n"
        f"🆔 الآيدي: {sender_id}\n\n"
        f"💬 الرسالة:\n{text}"
    )


    bot.send_message(
        ADMIN_ID,
        report
    )




# =========================
# أزرار الحظر
# =========================

@bot.callback_query_handler(
    func=lambda call: True
)
def buttons(call):

    data = call.data

    owner_id = call.message.chat.id



    # حظر شخص
    if data.startswith("block_"):

        sender_id = int(
            data.split("_")[1]
        )


        conn = db()
        cur = conn.cursor()


        cur.execute(
            "INSERT OR IGNORE INTO blocked VALUES (?,?)",
            (
                owner_id,
                sender_id
            )
        )


        conn.commit()
        conn.close()


        bot.answer_callback_query(
            call.id,
            "تم حظر المرسل 🚫"
        )



    # فك الحظر
    elif data == "unblock":


        conn = db()
        cur = conn.cursor()


        cur.execute(
            "SELECT sender_id FROM last_sender WHERE owner_id=?",
            (owner_id,)
        )

        last = cur.fetchone()



        if last:

            cur.execute(
                "DELETE FROM blocked WHERE owner_id=? AND sender_id=?",
                (
                    owner_id,
                    last[0]
                )
            )


            conn.commit()


            bot.answer_callback_query(
                call.id,
                "تم فك الحظر ✅"
            )

        else:

            bot.answer_callback_query(
                call.id,
                "لا يوجد شخص"
            )


        conn.close()



# =========================
# تشغيل البوت
# =========================

bot.remove_webhook()

print("البوت يعمل ✅")

bot.infinity_polling()
    )
