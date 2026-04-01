import json
import asyncio
import os
import re
import logging
from http.server import BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TARGET_GROUP_ID = int(os.environ.get('TARGET_GROUP_ID', '0'))


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
                await context.bot.send_message(
                    chat_id=TARGET_GROUP_ID,
                    text=message_text,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logging.error(f"Error sending message to target group: {e}")
        return


def build_app():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(copy_callback, pattern=r'^copy_'))
    return app


async def process_update(update_data: dict):
    app = build_app()
    async with app:
        update = Update.de_json(update_data, app.bot)
        await app.process_update(update)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            update_data = json.loads(body)
            asyncio.run(process_update(update_data))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        except Exception as e:
            logging.error(f"Webhook error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Error')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Webhook is active.')

    def log_message(self, format, *args):
        pass
