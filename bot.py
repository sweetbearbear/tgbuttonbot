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

# —— 加载本地 .env 配置 ——
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# 日志配置
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def parse_buttons(text: str):
    """从消息中解析正文和按钮配置，并返回 (content, InlineKeyboardMarkup)"""
    if '---按钮---' not in text:
        return text.strip(), None
    content, btn_section = text.split('---按钮---', 1)
    rows = []
    for line in btn_section.strip().splitlines():
        if '|' in line:
            name, url = [p.strip() for p in line.split('|', 1)]
            rows.append([InlineKeyboardButton(name, url=url)])
    markup = InlineKeyboardMarkup(rows) if rows else None
    return content.strip(), markup


async def forward_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    raw = msg.caption or msg.text or ""
    content, markup = parse_buttons(raw)

    # 根据消息类型转发，并用 Markdown 渲染
    if msg.photo:
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=msg.photo[-1].file_id,
            caption=content,
            reply_markup=markup,
            parse_mode="Markdown",
        )
    elif msg.video:
        await context.bot.send_video(
            chat_id=CHANNEL_ID,
            video=msg.video.file_id,
            caption=content,
            reply_markup=markup,
            parse_mode="Markdown",
        )
    elif msg.document:
        await context.bot.send_document(
            chat_id=CHANNEL_ID,
            document=msg.document.file_id,
            caption=content,
            reply_markup=markup,
            parse_mode="Markdown",
        )
    else:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=content,
            reply_markup=markup,
            parse_mode="Markdown",
        )

    logging.info("已转发内容到频道：%s", CHANNEL_ID)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Bot 已启动！私聊我发送文字/图片/视频，并在正文后加 `---按钮---` 配置按钮吧。",
        parse_mode="Markdown",
    )


if __name__ == "__main__":
    if not TOKEN or not CHANNEL_ID:
        logging.error("请在 .env 中设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHANNEL_ID")
        exit(1)

    # 构建应用
    app = ApplicationBuilder().token(TOKEN).build()

    # 测试命令
    app.add_handler(CommandHandler("start", start))
    # 消息处理
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
