import datetime
import logging
import os
import re
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import MessageEntityType
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

TIKTOK_RE = re.compile(
    r"(?<![\w.-])((?:https?://)?(?:[\w-]+\.)*)tiktok\.com(/\S*)?",
    re.IGNORECASE,
)

KYIV_TZ = ZoneInfo("Europe/Kyiv")
REMINDER_TEXT = "Пара в сеня почалася, не забудьте зайти друзі"
REMINDER_TIME = datetime.time(14, 55, tzinfo=KYIV_TZ)
REMINDER_DAYS = (1, 3)  # PTB: 0 = неділя, тож 1 = понеділок, 3 = середа


def convert(url: str) -> str:
    return TIKTOK_RE.sub(lambda m: f"{m.group(1)}kktiktok.com{m.group(2) or ''}", url)


def extract_links(text: str) -> list[str]:
    return [m.group(0) for m in TIKTOK_RE.finditer(text)]


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None:
        return

    text = msg.text or msg.caption or ""
    links = extract_links(text)

    for entity in (msg.entities or msg.caption_entities or ()):
        if entity.type == MessageEntityType.TEXT_LINK and entity.url:
            links.extend(extract_links(entity.url))

    fixed = list(dict.fromkeys(convert(link) for link in links))
    if not fixed:
        return

    await msg.reply_text("\n".join(fixed))


async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=context.job.chat_id, text=REMINDER_TEXT)
    log.info("Reminder sent to %s", context.job.chat_id)


async def chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(f"chat_id: {update.effective_chat.id}")


def main() -> None:
    load_dotenv()
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit("BOT_TOKEN env variable is not set")

    app = Application.builder().token(token).build()
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.CAPTION) & ~filters.COMMAND & ~filters.UpdateType.EDITED,
            on_message,
        )
    )
    app.add_handler(CommandHandler("chatid", chat_id))

    group_chat_id = os.environ.get("GROUP_CHAT_ID")
    if group_chat_id:
        app.job_queue.run_daily(
            send_reminder,
            time=REMINDER_TIME,
            days=REMINDER_DAYS,
            chat_id=int(group_chat_id),
            name="lesson_reminder",
        )
        log.info("Reminder scheduled for chat %s", group_chat_id)
    else:
        log.warning("GROUP_CHAT_ID is not set, reminder disabled")

    log.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
