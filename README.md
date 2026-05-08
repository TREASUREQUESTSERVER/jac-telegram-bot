# NEET Result Bot Setup

This folder now contains a Telegram/Render bot setup that can check whether the official NEET result is live on the NTA NEET portal.

Official NEET site:

- [NTA NEET Portal](https://exams.nta.ac.in/NEET/)

Main cloud bot files:

- `app.py`
- `requirements.txt`
- `render.yaml`

Environment variables you should keep in Render:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `CRON_SECRET`
- `OPENAI_API_KEY` (only if you want AI replies and have quota)
- `OPENAI_MODEL`
- `RESULT_YEAR` optional, defaults to current year

Current bot behavior:

- `result live or not` checks official NEET result status
- `check my result` explains that direct NEET candidate-login retrieval is not wired yet
- `/check` can still be used by cron-job.org for live alerts

The older JAC helper scripts are still in this folder, but the active cloud bot in `app.py` is now NEET-focused.

## What it does

- Checks the JAC results homepage.
- Looks for Class 12 / XII / Intermediate result markers.
- Sends one WhatsApp alert when it detects the result.
- Stores a small local state file so it does not spam duplicate alerts.

## Files

- `jac_whatsapp_watch.py`: the watcher script
- `.env.example`: environment variable template
- `run-jac-whatsapp-watch.cmd`: Windows launcher
- `jac_telegram_watch.py`: Telegram watcher script
- `jac_telegram_watch.ps1`: Telegram watcher script for Windows PowerShell
- `run-jac-telegram-watch.cmd`: Telegram launcher
- `jac_telegram_reply_bot.ps1`: Telegram reply bot for yes/no checks
- `run-jac-telegram-reply-bot.cmd`: Launcher for the reply bot
- `jac_watch_state.json`: created automatically after the first run

## Twilio setup

Use the official Twilio WhatsApp Sandbox flow:

1. Create or sign in to your Twilio account.
2. Open the Twilio WhatsApp quickstart and sandbox pages.
3. Activate the sandbox in the Twilio Console.
4. In WhatsApp on your phone, send the sandbox join code to the Twilio sandbox number.
5. Copy your Twilio Account SID and Auth Token from the Twilio Console.

Official docs:

- [Twilio WhatsApp quickstart](https://www.twilio.com/docs/whatsapp/quickstart)
- [Twilio WhatsApp Sandbox](https://www.twilio.com/docs/whatsapp/sandbox)

## Local config

1. Copy `.env.example` to `.env`.
2. Fill in these values:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_FROM`
   - `ALERT_WHATSAPP_TO`

For sandbox testing, `TWILIO_WHATSAPP_FROM` is usually `whatsapp:+14155238886`.

Your destination should look like:

`ALERT_WHATSAPP_TO=whatsapp:+91xxxxxxxxxx`

## Test it once

Open PowerShell in this folder and run:

```powershell
cmd /c run-jac-whatsapp-watch.cmd
```

If Class 12 is not live yet, you should see a "No new Class 12 result detected." message.

## Run every 5 minutes on Windows

Create a Scheduled Task that runs this command every 5 minutes:

```text
cmd /c "C:\Users\trqgp\Documents\Codex\2026-04-22-hey\run-jac-whatsapp-watch.cmd"
```

Suggested task settings:

- Trigger: Daily
- Repeat task every: 5 minutes
- For a duration of: 1 day
- Enabled: Yes

Make sure the machine stays on and has internet access.

## Notes

- The Twilio sandbox is for testing. Twilio notes that sandbox sessions expire after three days, so you may need to rejoin the sandbox later.
- The detection logic checks the main homepage text. If JAC publishes Class 12 results in a very different format, the keywords may need a small update.

## Telegram setup

If you already created a Telegram bot and confirmed your chat ID, this is simpler than WhatsApp.

1. Copy `.env.example` to `.env`.
2. Fill only these two lines:
   - `TELEGRAM_BOT_TOKEN=your_new_bot_token`
   - `TELEGRAM_CHAT_ID=6069431552`
3. Test the watcher:

```powershell
cmd /c run-jac-telegram-watch.cmd
```

If the official Class 12 result is not live yet, it will print:

```text
No Class 12 result detected yet.
```

## Run Telegram check every 5 minutes on Windows

Create a Windows Scheduled Task with this command:

```text
cmd /c "C:\Users\trqgp\Documents\Codex\2026-04-22-hey\run-jac-telegram-watch.cmd"
```

Suggested settings:

- Trigger: Daily
- Repeat task every: 5 minutes
- For a duration of: 1 day
- Enabled: Yes

## Telegram reply bot

If you want to message your bot and get an answer like `yes` or `no`, run:

```text
cmd /c "C:\Users\trqgp\Documents\Codex\2026-04-22-hey\run-jac-telegram-reply-bot.cmd"
```

Then send your bot a message like:

```text
result live or not
```

The bot will check the official JAC results site and reply.

Important:

- This reply bot must keep running.
- If you close the window, the bot stops replying.
- For permanent use, you can also run this through Task Scheduler at logon.

## Cloud option without keeping your laptop on

I also added a Render-ready version of the Telegram reply bot:

- `app.py`
- `requirements.txt`
- `render.yaml`

This version works as a webhook-based bot:

- You send your Telegram bot a message like `result live or not`
- Render receives the webhook
- It checks the official JAC site
- It replies `yes` or `no`

### Render setup

1. Create a free Render account.
2. Put this folder in a GitHub repo.
3. In Render, create a new Web Service from that repo.
4. Render should detect `render.yaml`.
5. Add environment variable:
   - `TELEGRAM_BOT_TOKEN=your_bot_token`
6. Deploy.

After deploy, your service URL will look like:

`https://your-service-name.onrender.com`

Then set the Telegram webhook in your browser:

```text
https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=https://YOUR-SERVICE.onrender.com/telegram
```

After that, message your bot:

```text
result live or not
```

Important:

- Render's official free web service docs say free services can spin down after 15 minutes of inactivity.
- That means the first reply after a long idle period may be slower while the service wakes up.

## OpenAI-connected Telegram bot

This project can also run with OpenAI-powered replies for Telegram chats while still grounding result answers in the official JAC website.

Add these Render environment variables:

- `OPENAI_API_KEY=your_openai_api_key`
- `OPENAI_MODEL=gpt-5.2`

This uses the official OpenAI Responses API path recommended for new projects:

- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses/retrieve)
- [OpenAI Python quickstart](https://platform.openai.com/docs/quickstart?api-mode=responses&lang=python)

Important:

- Telegram chat replies through OpenAI are paid API usage.
- The result-alert endpoint `/check` still uses normal code for reliable scheduled checking.
- The bot can keep a chat feel while still grounding result status against the official JAC site.

## Free cloud auto-alerts

To send an automatic Telegram alert without keeping your laptop on, use the existing Render service plus a free cron trigger service such as [cron-job.org](https://cron-job.org/en/).

Add these environment variables in Render:

- `TELEGRAM_BOT_TOKEN=your_bot_token`
- `TELEGRAM_CHAT_ID=6069431552`
- `CRON_SECRET=choose_any_random_secret`

Then create a cron-job.org job that opens:

```text
https://YOUR-RENDER-URL/check?key=YOUR_CRON_SECRET
```

Schedule it every 5 minutes.

What it does:

- checks the official JAC result site
- sends one Telegram alert when Class 12 goes live
- avoids sending duplicates unless the service is redeployed or its local state is reset
