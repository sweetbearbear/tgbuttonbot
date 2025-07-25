import os
import json
import logging
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# —— 加载本地 .env 配置 ——
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# 管理员与频道映射，格式为 JSON 字符串：{"<admin_user_id>": "@channel_username", ...}
try:
    ADMIN_CHANNEL_MAP = json.loads(os.getenv("ADMIN_CHANNEL_MAP", "{}"))
except json.JSONDecodeError:
    logging.error("ADMIN_CHANNEL_MAP 格式错误，应为如 {'12345678':'@mychannel'} 的 JSON 字符串")
    ADMIN_CHANNEL_MAP = {}

# 校验配置
if not TOKEN or not ADMIN_CHANNEL_MAP:
    logging.error("请在 .env 中设置 TELEGRAM_BOT_TOKEN 和 ADMIN_CHANNEL_MAP")
    exit(1)

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

async def forward_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    user_id = str(user.id)
    # 权限校验：检查是否为管理员
    if user_id not in ADMIN_CHANNEL_MAP:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ 你没有权限使用此 Bot",
            parse_mode=ParseMode.HTML
        )
        return

    # 获取该管理员绑定的频道
    channel_id = ADMIN_CHANNEL_MAP[user_id]

    msg = update.message
    raw = msg.caption or msg.text or ""
    content, markup = parse_buttons(raw)

    # 转发到指定频道，以 HTML 模式渲染内容
    if msg.photo:
        await context.bot.send_photo(
            chat_id=channel_id,
            photo=msg.photo[-1].file_id,
            caption=content,
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    elif msg.video:
        await context.bot.send_video(
            chat_id=channel_id,
            video=msg.video.file_id,
            caption=content,
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    elif msg.document:
        await context.bot.send_document(
            chat_id=channel_id,
            document=msg.document.file_id,
            caption=content,
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    else:
        await context.bot.send_message(
            chat_id=channel_id,
            text=content,
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    logging.info(f"用户 {user_id} 的消息已转发到频道 {channel_id}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "Bot 已启动！仅指定管理员可用。\n"
            "私聊我发送带 HTML 标签的内容，末尾加 `---按钮---` 配置按钮。"
        ),
        parse_mode=ParseMode.HTML,
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    # `/start` 用于测试和提示
    app.add_handler(CommandHandler("start", start))
    # 仅转发被授权管理员的消息
    app.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL,
        forward_to_channel
    ))

    logging.info("Bot 正在运行… 管理员映射：%s", ADMIN_CHANNEL_MAP)
    app.run_polling()
