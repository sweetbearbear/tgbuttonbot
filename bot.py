import os
import logging
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

# —— 加载配置 ——
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def parse_buttons(text: str):
    """解析正文和按钮配置"""
    if '---按钮---' not in text:
        return text.strip(), None
    content, btn_section = text.split('---按钮---', 1)
    rows = []
    for line in btn_section.strip().splitlines():
        if '|' in line:
            name, url = [p.strip() for p in line.split('|', 1)]
            rows.append([InlineKeyboardButton(name, url=url)])
    return content.strip(), InlineKeyboardMarkup(rows) if rows else None


async def forward_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    raw = msg.caption or msg.text or ""
    content, markup = parse_buttons(raw)

    if msg.photo:
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=msg.photo[-1].file_id,
            caption=content,
            reply_markup=markup,
            parse_mode="HTML",
        )
    elif msg.video:
        await context.bot.send_video(
            chat_id=CHANNEL_ID,
            video=msg.video.file_id,
            caption=content,
            reply_markup=markup,
            parse_mode="HTML",
        )
    elif msg.document:
        await context.bot.send_document(
            chat_id=CHANNEL_ID,
            document=msg.document.file_id,
            caption=content,
            reply_markup=markup,
            parse_mode="HTML",
        )
    else:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=content,
            reply_markup=markup,
            parse_mode="HTML",
        )

    logging.info("已转发内容到频道")


async def start(_: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=_.effective_chat.id,
        text="Bot 已启动！发送文字/图片/视频并在正文后加 `---按钮---` 配置按钮吧。",
        parse_mode="Markdown",
    )


if __name__ == "__main__":
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )
    # `/start` 测试指令
    app.add_handler(CommandHandler("start", start))
    # 任意消息转发
    app.add_handler(
        MessageHandler(
            filters.TEXT
            | filters.PHOTO
            | filters.VIDEO
            | filters.Document.ALL,
            forward_to_channel,
        )
    )
    logging.info("Bot 正在运行…")
    app.run_polling()
