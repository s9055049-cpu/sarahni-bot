
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

TOKEN = "8682801321:AAH6D6o_A6-4JLhbLP5aNCOWoa4Afo0gv7k"
MY_ADMIN_ID = 8820368378

# قائمة المحظورين
blocked_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in blocked_users:
        await update.message.reply_text("عذراً، أنت محظور من استخدام هذا البوت.")
        return
        
    bot_username = context.bot.username
    args = context.args
    
    # إذا دخل عن طريق رابط شخص ثاني (صارحني)
    if args:
        try:
            target_id = int(args[0])
            if target_id == user_id:
                await update.message.reply_text("لا يمكنك إرسال صراحة لنفسك! 😅\n\nهذا هو رابطك الخاص:\nhttps://t.me/" + bot_username + "?start=" + str(user_id))
                return
                
            # حفظ الأيدي المستهدف مؤقتاً في المحادثة
            context.user_data['target_id'] = target_id
            await update.message.reply_text("أهلاً بك! اكتب رسالة الصراحة أو السرية الخاصة بك، وسأقوم بإرسالها للشخص فوراً 🥷✨")
            return
        except ValueError:
            pass

    # إذا دخل البوت بشكل عادي بدون رابط
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

    sender_username = f"@{sender.username}" if sender.username else "لا يوجد"
    sender_name = sender.first_name if sender.first_name else "مجهول"
    message_text = update.message.text

    # التحقق مما إذا كان يرسل صراحة لشخص معين عبر رابط
    target_id = context.user_data.get('target_id', MY_ADMIN_ID)

    # رد للمرسل
    await update.message.reply_text("تم إرسال صراحتك بنجاح 🥷✨")

    # إرسال الرسالة والتقرير الكامل للشخص المستهدف (أو لكِ إذا كانت موجهة لكِ)
    await context.bot.send_message(
        chat_id=target_id,
        text=f"💌 وصلت صراحة جديدة!\n\n"
             f"💬 النص:\n{message_text}\n\n"
             f"👤 معلومات المرسل:\n"
             f"- الاسم: {sender_name}\n"
             f"- الأيدي: `{sender_id}`\n"
             f"- اليوزر: {sender_username}",
        parse_mode="Markdown"
    )
    
    # مسح المستهدف المؤقت لكي لا تتخزن الرسالة بالغلط
    if 'target_id' in context.user_data:
        del context.user_data['target_id']

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("block", block_user))
    application.add_handler(CommandHandler("unblock", unblock_user))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)
