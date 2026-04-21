import os
from urllib.parse import urljoin

import requests
from flask import Flask, jsonify, request


JAC_URL = "https://jacresults.com/"

app = Flask(__name__)


def get_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def class_12_live() -> bool:
    response = requests.get(
        JAC_URL,
        headers={"User-Agent": "JACCloudTelegramBot/1.0"},
        timeout=30,
    )
    response.raise_for_status()
    html = response.text.lower()
    markers = (
        "class xii",
        "class 12",
        "annual intermediate examination - 2026",
        "intermediate examination - 2026",
    )
    return any(marker in html for marker in markers)


def send_telegram_message(chat_id: int, text: str) -> None:
    token = get_env("TELEGRAM_BOT_TOKEN")
    api_url = urljoin(f"https://api.telegram.org/bot{token}/", "sendMessage")
    response = requests.post(
        api_url,
        data={"chat_id": str(chat_id), "text": text},
        timeout=30,
    )
    response.raise_for_status()


def build_reply(message_text: str) -> str:
    text = message_text.lower()
    if "result" in text or "live" in text or "jac" in text:
        return (
            f"Yes, the official JAC Class 12 result appears to be live on {JAC_URL}"
            if class_12_live()
            else f"No, the official JAC Class 12 result is not live yet on {JAC_URL}"
        )
    return "Send: result live or not"


@app.get("/")
def healthcheck():
    return jsonify({"ok": True, "service": "jac-telegram-bot"})


@app.post("/telegram")
def telegram_webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    text = message.get("text")
    chat_id = chat.get("id")

    if text and chat_id:
        reply = build_reply(text)
        send_telegram_message(chat_id, reply)

    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
