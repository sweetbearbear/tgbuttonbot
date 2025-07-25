import os
import logging
from dotenv import load_dotenv
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

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
    return content.strip(), InlineKeyboardMarkup(rows) if rows else None


def md_to_html(text: str) -> str:
    """将常见 Markdown 格式转换为 HTML 格式供 Telegram 渲染"""
    # 转义 HTML 特殊字符
    text = (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))
    # 链接 [text](url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"<a href='\2'>\1</a>", text)
    # 粗体 *text*
    text = re.sub(r"\*(.*?)\*", r"<b>\1</b>", text)
    # 斜体 _text_
    text = re.sub(r"_(.*?)_", r"<i>\1</i>", text)
    return text

async def forward_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    raw = msg.caption or msg.text or ""
    content, markup = parse_buttons(raw)
    html_content = md_to_html(content)

    # 根据消息类型转发，使用 HTML 模式
    if msg.photo:
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=msg.photo[-1].file_id,
            caption=html_content,
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    elif msg.video:
        await context.bot.send_video(
            chat_id=CHANNEL_ID,
            video=msg.video.file_id,
            caption=html_content,
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    elif msg.document:
        await context.bot.send_document(
            chat_id=CHANNEL_ID,
            document=msg.document.file_id,
            caption=html_content,
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    else:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=html_content,
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    logging.info("已转发内容到频道：%s", CHANNEL_ID)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=("Bot 已启动！私聊我发送文字/图片/视频，支持简易 Markdown (*粗体* _斜体_ [链接](url)) "
              "并在正文后加 `---按钮---` 配置按钮。"),
        parse_mode=ParseMode.HTML,
    )

if __name__ == "__main__":
    if not TOKEN or not CHANNEL_ID:
        logging.error("请在 .env 中设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHANNEL_ID")
        exit(1)

    # 构建并运行应用
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL,
        forward_to_channel
    ))
    logging.info("Bot 正在运行…")
    app.run_polling()
