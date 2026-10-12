# theBoysbot

Telegram-бот: слухає повідомлення в групі, і якщо хтось скинув TikTok-посилання
(`https://vt.tiktok.com/ZSbwWoaWA`), відповідає тим самим посиланням через `kktiktok.com`
(`https://vt.kktiktok.com/ZSbwWoaWA`), щоб відео нормально вбудовувалося в Telegram.

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
BOT_TOKEN=xxx python bot.py
```

## 3. Деплой на Heroku
```bash
git init && git add . && git commit -m "init"
heroku create the-boys-bot
heroku config:set BOT_TOKEN=xxx
git push heroku main
heroku ps:scale web=0 worker=1
heroku logs --tail
```
Бот працює через polling, тому потрібен **worker**-дайно, а не web (див. `Procfile`).
