import logging
import os
import re

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import MessageEntityType
from telegram.ext import Application, ContextTypes, MessageHandler, filters

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
    log.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
