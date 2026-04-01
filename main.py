import logging
import os
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TARGET_GROUP_ID = int(os.environ.get('TARGET_GROUP_ID', '0'))
PORT = int(os.environ.get('PORT', '5000'))


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):
        pass


def run_health_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    logging.info(f"Health check server running on port {PORT}")
    server.serve_forever()


async def delete_msg(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    if job and job.chat_id and job.data:
        try:
            await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
            logging.info(f"Deleted message {job.data} from chat {job.chat_id}")
        except Exception as e:
            logging.error(f"Failed to delete message {job.data} from chat {job.chat_id}: {e}")

async def copy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    code = query.data.replace("copy_", "")
    await query.answer(f"កូដ {code} ត្រូវបានចម្លងទុក (ចុចឱ្យជាប់លើសារដើម្បីចម្លង)", show_alert=False)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"`{code}`",
        parse_mode='MarkdownV2'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        user = update.message.from_user
        is_bot = user.is_bot if user else False
        logging.info(f"Incoming message from: {'Bot' if is_bot else 'User'} (ID: {user.id if user else 'Unknown'})")
    
    if not update.message or not update.message.text:
        if update.channel_post and update.channel_post.text:
            text = update.channel_post.text
            effective_chat = update.channel_post.chat
        else:
            return
    else:
        text = update.message.text
        effective_chat = update.effective_chat

    if effective_chat.type not in ['group', 'supergroup', 'channel']:
        return
    
    if "E-GetS" in text and ("noreply@e-gets.com" in text or "លេខកូដផ្ទៀងផ្ទាត់" in text):
        match = re.search(r'\b(\d{6})\b', text)
        if match:
            code = match.group(1)
            
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            if email_match:
                extracted_email = email_match.group(0)
                if extracted_email == "noreply@e-gets.com":
                    all_emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
                    email = next((e for e in all_emails if e != "noreply@e-gets.com"), "មិនស្គាល់អ៊ីមែល")
                else:
                    email = extracted_email
            else:
                email = "មិនស្គាល់អ៊ីមែល"
            
            message_text = f"*📩 លេខកូដផ្ទៀងផ្ទាត់ E-GetS*\n\n{email}\n\n`{code}`"
            
            try:
                sent_message = await context.bot.send_message(
                    chat_id=TARGET_GROUP_ID, 
                    text=message_text,
                    parse_mode='Markdown'
                )
                
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
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    if not TOKEN:
        logging.warning("TELEGRAM_BOT_TOKEN is not set. Bot polling disabled. Health server still running.")
        import time
        while True:
            time.sleep(60)

    application = ApplicationBuilder().token(TOKEN).build()
    
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(message_handler)
    application.add_handler(CallbackQueryHandler(copy_callback, pattern=r'^copy_'))
    
    print("Bot is starting...")
    application.run_polling(allowed_updates=["message", "callback_query", "channel_post"])
