# theBoysbot

Telegram-бот: слухає повідомлення в групі, і якщо хтось скинув TikTok- або Instagram-посилання
(`https://vt.tiktok.com/ZSbwWoaWA`), відповідає тим самим посиланням через `kktiktok.com`
(`https://vt.kktiktok.com/ZSbwWoaWA`, `instagram.com` → `kkinstagram.com`), щоб відео нормально вбудовувалося в Telegram.

Також щопонеділка і щосереди о 14:55 (Київ) пише в групу нагадування про пару.
Для цього потрібен config var `GROUP_CHAT_ID` — дізнатися його можна командою `/chatid` у групі.

## 1. Створити бота
1. У [@BotFather](https://t.me/BotFather): `/newbot` → отримати токен.
2. **Обов'язково** `/setprivacy` → вибрати бота → `Disable`.
   Інакше бот не бачитиме звичайні повідомлення в групі.
   (Якщо бот уже в групі, після зміни видаліть його й додайте знову.)
3. Додати бота в групу.

## 2. Локальний запуск
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # і вписати токен у .env
python bot.py
```

## 3. Деплой на Heroku
```bash
git init && git add . && git commit -m "init"
heroku create the-boys-bot
heroku config:set BOT_TOKEN=xxx
heroku config:set GROUP_CHAT_ID=-100xxxxxxxxxx
git push heroku main
heroku ps:scale web=0 worker=1
heroku logs --tail
```
Бот працює через polling, тому потрібен **worker**-дайно, а не web (див. `Procfile`).

## Сповіщення, хто додав бота
Коли бота додають/видаляють з групи чи роблять адміном, він пише про це в особисті власнику.
Напишіть боту в приват `/chatid` — це ваш ID, потім:
```bash
heroku config:set ADMIN_ID=<ваш id> -a theboysbot
```
