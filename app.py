import json
import os
from pathlib import Path
from urllib.parse import urljoin

import requests
from flask import Flask, jsonify, request


JAC_URL = "https://jacresults.com/"
OWNER_NAME = "Priyanshu Raj"
INSTAGRAM_URL = "https://instagram.com/priyanshuxraj"
STATE_FILE = Path("alert_state.json")
RESULT_FETCH_MODES = ("html", "pdf")

app = Flask(__name__)
CHAT_STATES = {}


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


def result_entry_live() -> bool:
    response = requests.get(
        JAC_URL,
        headers={"User-Agent": "JACCloudTelegramBot/1.0"},
        timeout=30,
    )
    response.raise_for_status()
    html = response.text.lower()
    return (
        "enter-class-xii-2026" in html
        or "enter-class-xii-arts-2026" in html
        or "results of annual intermediate examination - 2026" in html
    )


def detect_result_delivery_modes() -> list[str]:
    if not result_entry_live():
        return []
    # Placeholder capability map until the official 2026 result form is live
    # and its response flow can be verified end-to-end.
    return list(RESULT_FETCH_MODES)


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
    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": "Owner: Priyanshu Raj",
                    "url": INSTAGRAM_URL,
                }
            ],
            [
                {
                    "text": "Instagram: @priyanshuxraj",
                    "url": INSTAGRAM_URL,
                }
            ],
        ]
    }
    response = requests.post(
        api_url,
        data={
            "chat_id": str(chat_id),
            "text": text,
            "reply_markup": json.dumps(reply_markup),
        },
        timeout=30,
    )
    response.raise_for_status()


def build_reply(message_text: str) -> str:
    text = message_text.lower()
    if any(word in text for word in ("hi", "hello", "hey", "hii", "namaste")):
        return (
            f"Hello! I am the JAC result bot by {OWNER_NAME}. "
            "I can check the official JAC Class 12 result for you. "
            "Ask me things like: result live or not"
        )

    if "how are you" in text:
        return (
            f"I am good. I am the JAC result bot by {OWNER_NAME}. "
            "I am watching the official JAC Class 12 result site for you. "
            "Ask me: result live or not"
        )

    if any(phrase in text for phrase in ("thank you", "thanks", "thx")):
        return (
            f"You are welcome. I am {OWNER_NAME}'s JAC result bot. "
            "Message me anytime to check the JAC Class 12 result."
        )

    if any(phrase in text for phrase in ("who are you", "what can you do", "help")):
        return (
            f"I am {OWNER_NAME}'s JAC result bot. I can tell you whether the official Class 12 result "
            "is live. Try: result live or not"
        )

    if "result" in text or "live" in text or "jac" in text:
        return (
            f"Yes, the official JAC Class 12 result appears to be live on {JAC_URL}"
            if class_12_live()
            else f"No, the official JAC Class 12 result is not live yet on {JAC_URL}"
        )

    return (
        f"I am {OWNER_NAME}'s JAC result bot. I can chat a little and check the official JAC Class 12 result for you. "
        "Try saying hello or ask: result live or not"
    )


def start_result_lookup(chat_id: int) -> str:
    CHAT_STATES[chat_id] = {"step": "await_roll_code"}
    return (
        "Okay. Send your roll code first.\n"
        "Format example: 11001"
    )


def handle_lookup_flow(chat_id: int, message_text: str):
    state = CHAT_STATES.get(chat_id)
    if not state:
        return None

    text = message_text.strip()
    step = state.get("step")

    if step == "await_roll_code":
        state["roll_code"] = text
        state["step"] = "await_roll_number"
        return "Now send your roll number."

    if step == "await_roll_number":
        state["roll_number"] = text
        state["step"] = "await_stream"
        return "Now send your stream: science, commerce, or arts."

    if step == "await_stream":
        stream = text.lower()
        if stream not in {"science", "commerce", "arts"}:
            return "Please send one valid stream: science, commerce, or arts."

        state["stream"] = stream
        state["step"] = "await_format"
        return "Now choose result format: html or pdf."

    if step == "await_format":
        format_choice = text.lower()
        if format_choice not in {"html", "pdf"}:
            return "Please choose one valid format: html or pdf."

        state["format"] = format_choice
        CHAT_STATES.pop(chat_id, None)

        if not result_entry_live():
            return (
                "I got your details:\n"
                f"Roll code: {state['roll_code']}\n"
                f"Roll number: {state['roll_number']}\n"
                f"Stream: {state['stream'].title()}\n\n"
                f"Preferred format: {format_choice.upper()}\n\n"
                "But the official 2026 JAC Class 12 result entry page is not live yet, "
                "so I cannot fetch the result directly right now. You can still ask: result live or not"
            )

        supported_modes = detect_result_delivery_modes()
        if format_choice not in supported_modes:
            return (
                f"The official 2026 result page is live, but {format_choice.upper()} delivery is not "
                "available from the verified JAC flow yet."
            )

        return (
            f"The official 2026 result entry page appears to be live and I have recorded your preference "
            f"for {format_choice.upper()} delivery, but the final verified JAC fetch flow is not wired yet. "
            "Once the exact official submission and response format are confirmed, I can use either HTML "
            "summary delivery or direct PDF sending depending on what JAC returns."
        )

    CHAT_STATES.pop(chat_id, None)
    return None


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
        lookup_reply = handle_lookup_flow(chat_id, text)
        if lookup_reply is not None:
            reply = lookup_reply
        elif any(
            phrase in text.lower()
            for phrase in (
                "check result",
                "my result",
                "check my result",
                "result check",
            )
        ):
            reply = start_result_lookup(chat_id)
        else:
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
