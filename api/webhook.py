import json
import asyncio
import os
import re
import logging
from flask import Flask, request, Response
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TARGET_GROUP_ID = int(os.environ.get('TARGET_GROUP_ID', '0'))

app = Flask(__name__)


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


def build_bot_app():
    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    bot_app.add_handler(CallbackQueryHandler(copy_callback, pattern=r'^copy_'))
    return bot_app


async def process_update(update_data: dict):
    bot_app = build_bot_app()
    async with bot_app:
        update = Update.de_json(update_data, bot_app.bot)
        await bot_app.process_update(update)


@app.route('/api/webhook', methods=['POST'])
def webhook():
    try:
        update_data = request.get_json(force=True)
        asyncio.run(process_update(update_data))
        return Response('OK', status=200)
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return Response('Error', status=500)


@app.route('/api/webhook', methods=['GET'])
def health():
    return Response('Webhook is active.', status=200)
