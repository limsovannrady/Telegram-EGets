import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TARGET_GROUP_ID = int(os.environ.get('TARGET_GROUP_ID', '0'))

async def delete_msg(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    if job and job.chat_id and job.data:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)

async def copy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    code = query.data.replace("copy_", "")
    # Using MarkdownV2 style for copyable text in answer might not work as expected for automatic clipboard
    # Telegram API doesn't support direct "copy to clipboard" via button click for security.
    # The best way is to show a message that is easy to copy or a notification.
    await query.answer(f"កូដ {code} ត្រូវបានចម្លងទុក (ចុចឱ្យជាប់លើសារដើម្បីចម្លង)", show_alert=False)
    # We can also send a new message with just the code which is easy to tap-to-copy
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"`{code}`",
        parse_mode='MarkdownV2'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Log incoming message source for debugging
    if update.message:
        user = update.message.from_user
        is_bot = user.is_bot if user else False
        logging.info(f"Incoming message from: {'Bot' if is_bot else 'User'} (ID: {user.id if user else 'Unknown'})")
    
    # We must explicitly allow messages from bots. 
    # By default, some filters might exclude them, but here we process the update directly.
    if not update.message or not update.message.text:
        # Check if it's a channel post or other type if needed
        if update.channel_post and update.channel_post.text:
            text = update.channel_post.text
            effective_chat = update.channel_post.chat
        else:
            return
    else:
        text = update.message.text
        effective_chat = update.effective_chat

    # Only process messages from groups, supergroups or channels
    if effective_chat.type not in ['group', 'supergroup', 'channel']:
        return
    
    # Check if the message contains the specific content
    # We look for the key parts of the message: E-GetS and the code
    if "E-GetS" in text and ("noreply@e-gets.com" in text or "លេខកូដផ្ទៀងផ្ទាត់" in text):
        # Use regex to find the 6-digit code
        match = re.search(r'\b(\d{6})\b', text)
        if match:
            code = match.group(1)
            
            # Extract email if present
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            if email_match:
                extracted_email = email_match.group(0)
                # If the extracted email is the noreply one, we try to find another one or mark as unknown
                if extracted_email == "noreply@e-gets.com":
                    # Look for second email
                    all_emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
                    email = next((e for e in all_emails if e != "noreply@e-gets.com"), "មិនស្គាល់អ៊ីមែល")
                else:
                    email = extracted_email
            else:
                email = "មិនស្គាល់អ៊ីមែល"
            
            message_text = f"*📩 លេខកូដផ្ទៀងផ្ទាត់ E-GetS*\n\n{email}\n\n`{code}`"
            
            # Send to the specific group ID
            try:
                sent_message = await context.bot.send_message(
                    chat_id=TARGET_GROUP_ID, 
                    text=message_text,
                    parse_mode='Markdown'
                )
                
                # Schedule deletion after 60 seconds
                if context.job_queue:
                    context.job_queue.run_once(
                        delete_msg,
                        60,
                        chat_id=TARGET_GROUP_ID,
                        data=sent_message.message_id
                    )
            except Exception as e:
                logging.error(f"Error sending message to target group: {e}")
        return

if __name__ == '__main__':
    # Initialize application with job_queue enabled
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add handler for text messages in groups (including from other bots)
    # Using filters.ALL to ensure we capture messages from other bots
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    # Important: To receive messages from other bots, the bot must be an admin 
    # and privacy mode must be disabled via BotFather.
    application.add_handler(message_handler)
    
    print("Bot is starting...")
    # By default run_polling() gets common updates. 
    # To be sure we get everything, we can specify allowed_updates.
    application.run_polling(allowed_updates=["message", "callback_query", "channel_post"])
