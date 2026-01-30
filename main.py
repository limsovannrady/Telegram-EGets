import logging
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# Health check server for Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return # Disable logging for health check

def run_health_check():
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logging.info(f"Starting health check server on port {port}")
    server.serve_forever()

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
    if not update.message or not update.message.text:
        return

    # Only process messages from groups or supergroups
    if update.effective_chat.type not in ['group', 'supergroup']:
        return

    text = update.message.text
    
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
    # Start health check server in a background thread
    threading.Thread(target=run_health_check, daemon=True).start()

    # Initialize application with job_queue enabled
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add handler for text messages in groups
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(message_handler)
    
    print("Bot is starting...")
    application.run_polling()
