import json
import os
from pathlib import Path
from urllib.parse import urljoin

import requests
from flask import Flask, jsonify, request


JAC_URL = "https://jacresults.com/"
STATE_FILE = Path("alert_state.json")

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


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"already_alerted": False}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"already_alerted": False}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")


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


def run_alert_check() -> dict:
    state = load_state()
    live = class_12_live()

    if live and not state.get("already_alerted", False):
        chat_id = int(get_env("TELEGRAM_CHAT_ID"))
        send_telegram_message(
            chat_id,
            f"JAC Class 12 result appears to be live now on the official site: {JAC_URL}",
        )
        state["already_alerted"] = True
        save_state(state)
        return {"ok": True, "alert_sent": True, "live": True}

    if not live and state.get("already_alerted", False):
        state["already_alerted"] = False
        save_state(state)

    return {"ok": True, "alert_sent": False, "live": live}


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


@app.get("/check")
def scheduled_check():
    secret = request.args.get("key", "")
    expected = get_env("CRON_SECRET")
    if secret != expected:
        return jsonify({"ok": False, "error": "unauthorized"}), 403
    return jsonify(run_alert_check())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
