import datetime
import logging
import os
import re
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatMemberStatus, ChatType, MessageEntityType
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

# tiktok.com / instagram.com з будь-яким сабдоменом, але не вже виправлені kk*-посилання
LINK_RE = re.compile(
    r"(?<![\w.-])((?:https?://)?(?:[\w-]+\.)*)(tiktok|instagram)\.com(?![\w-]|\.[\w-])(/\S*)?",
    re.IGNORECASE,
)

KYIV_TZ = ZoneInfo("Europe/Kyiv")
REMINDER_TEXT = "Пара в сеня почалася, не забудьте зайти друзі"
REMINDER_TIME = datetime.time(14, 55, tzinfo=KYIV_TZ)
REMINDER_DAYS = (1, 3)  # PTB: 0 = неділя, тож 1 = понеділок, 3 = середа

IN_CHAT = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
    ChatMemberStatus.RESTRICTED,
}


def convert(url: str) -> str:
    return LINK_RE.sub(lambda m: f"{m.group(1)}kk{m.group(2)}.com{m.group(3) or ''}", url)


def extract_links(text: str) -> list[str]:
    return [m.group(0) for m in LINK_RE.finditer(text)]


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


async def on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cmu = update.my_chat_member
    if cmu.chat.type == ChatType.PRIVATE:
        return

    old, new = cmu.old_chat_member.status, cmu.new_chat_member.status
    if old not in IN_CHAT and new in IN_CHAT:
        action = "➕ Бота додали в групу"
    elif old in IN_CHAT and new not in IN_CHAT:
        action = "➖ Бота видалили з групи"
    elif new == ChatMemberStatus.ADMINISTRATOR and old != new:
        action = "⭐ Бота зробили адміном"
    elif old == ChatMemberStatus.ADMINISTRATOR and old != new:
        action = "Бота зняли з адміна"
    else:
        return

    who = cmu.from_user
    username = f" (@{who.username})" if who.username else ""
    text = (
        f"{action}\n"
        f"Хто: {who.full_name}{username}, id {who.id}\n"
        f"Група: {cmu.chat.title}, id {cmu.chat.id}"
    )
    log.info(text.replace("\n", " | "))

    admin_id = context.bot_data.get("admin_id")
    if admin_id:
        try:
            await context.bot.send_message(chat_id=admin_id, text=text)
        except TelegramError as e:
            log.warning("Can't notify admin %s: %s", admin_id, e)


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
    app.add_handler(ChatMemberHandler(on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))

    admin_id = os.environ.get("ADMIN_ID")
    if admin_id:
        app.bot_data["admin_id"] = int(admin_id)
    else:
        log.warning("ADMIN_ID is not set, join notifications go to logs only")

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
