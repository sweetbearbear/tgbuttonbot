import os
import logging
from dotenv import load_dotenv
from telegram import (
    Bot,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext
)

# 加载本地 .env 文件中的环境变量
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.INFO
)

def parse_buttons(text: str):
    """从消息中解析正文和按钮"""
    if '---按钮---' not in text:
        return text.strip(), None
    content, button_part = text.split('---按钮---', 1)
    lines = button_part.strip().splitlines()
    buttons = []
    for line in lines:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) == 2:
            buttons.append([InlineKeyboardButton(parts[0], url=parts[1])])
    return content.strip(), InlineKeyboardMarkup(buttons) if buttons else None

def forward_to_channel(update: Update, context: CallbackContext):
    message = update.message
    text = message.caption or message.text or ""
    content, reply_markup = parse_buttons(text)

    if message.photo:
        context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=message.photo[-1].file_id,
            caption=content,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    elif message.video:
        context.bot.send_video(
            chat_id=CHANNEL_ID,
            video=message.video.file_id,
            caption=content,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    elif message.document:
        context.bot.send_document(
            chat_id=CHANNEL_ID,
            document=message.document.file_id,
            caption=content,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=content,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    logging.info(f"消息已发送到频道：{CHANNEL_ID}")

def main():
    if not TOKEN or not CHANNEL_ID:
        logging.error("请在 .env 文件中设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHANNEL_ID")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(
        Filters.text | Filters.photo | Filters.video | Filters.document,
        forward_to_channel
    ))

    logging.info("Bot 已启动，监听中...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
