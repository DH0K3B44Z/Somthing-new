#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import os, time, random, threading, json
from datetime import datetime
import requests

# ---------------- CONFIG ---------------- #
APP_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_DATA_DIR = os.path.join(APP_DIR, "bot_users")
os.makedirs(BOT_DATA_DIR, exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
]

app = Flask(__name__)
active_bots = {}  # user_id: threading.Thread

# ---------------- HELPERS ---------------- #
def read_file_lines(path):
    try:
        return [line.strip() for line in open(path, encoding="utf-8") if line.strip()]
    except:
        return []

def post_comment(token, post_id, message):
    url = f"https://graph.facebook.com/{post_id}/comments"
    params = {"message": message, "access_token": token}
    try:
        res = requests.post(url, params=params, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=15)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def run_bot(user_folder):
    # Load files
    token_file = os.path.join(user_folder, "token_file.txt")
    comment_file = os.path.join(user_folder, "comment_file.txt")
    settings_file = os.path.join(user_folder, "settings.json")
    log_file = os.path.join(user_folder, "log.txt")

    if not os.path.exists(settings_file):
        return

    settings = json.load(open(settings_file))
    post_id = settings.get("post_id")
    prefix = settings.get("prefix", "")
    suffix = settings.get("suffix", "")
    interval = int(settings.get("interval", 60))

    tokens = read_file_lines(token_file)
    comments = read_file_lines(comment_file)
    comment_idx = 0

    while True:
        # Check stop signal
        if os.path.exists(os.path.join(user_folder, "stop.txt")):
            break

        if not comments or not tokens:
            break

        token = tokens[comment_idx % len(tokens)]
        message = f"{prefix} {comments[0]} {suffix}".strip()

        res = post_comment(token, post_id, message)
        now = datetime.now().strftime("%d-%m-%Y %I:%M %p")

        # Logging
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{now}] Token: {token[:8]}*** - {message} -> {res}\n")

        # Move to next comment
        comments.pop(0)
        comment_idx += 1

        time.sleep(interval + random.randint(3, 8))

# ---------------- ROUTES ---------------- #
@app.route("/run_bot", methods=["POST"])
def start_bot():
    user_id = request.remote_addr  # Simple multi-user isolation (IP-based)
    user_folder = os.path.join(BOT_DATA_DIR, user_id.replace(":", "_"))
    os.makedirs(user_folder, exist_ok=True)

    # Save uploaded files
    if "token_file" in request.files:
        request.files["token_file"].save(os.path.join(user_folder, "token_file.txt"))
    if "comment_file" in request.files:
        request.files["comment_file"].save(os.path.join(user_folder, "comment_file.txt"))

    # Save settings
    settings = {
        "user_type": request.form.get("user_type", "1"),
        "post_id": request.form.get("post_id", ""),
        "prefix": request.form.get("prefix", ""),
        "suffix": request.form.get("suffix", ""),
        "interval": request.form.get("interval", 60)
    }
    with open(os.path.join(user_folder, "settings.json"), "w") as f:
        json.dump(settings, f)

    # Remove stop signal if exists
    stop_file = os.path.join(user_folder, "stop.txt")
    if os.path.exists(stop_file):
        os.remove(stop_file)

    # Start bot thread
    if user_id not in active_bots or not active_bots[user_id].is_alive():
        t = threading.Thread(target=run_bot, args=(user_folder,))
        t.daemon = True
        t.start()
        active_bots[user_id] = t

    return jsonify({"status": "success", "msg": "Bot started for your session!"})

@app.route("/run_bot", methods=["GET"])
def stop_bot():
    user_id = request.remote_addr
    user_folder = os.path.join(BOT_DATA_DIR, user_id.replace(":", "_"))
    os.makedirs(user_folder, exist_ok=True)

    stop_file = os.path.join(user_folder, "stop.txt")
    with open(stop_file, "w") as f:
        f.write("stop")

    return jsonify({"status": "success", "msg": "Stop signal sent to your bot."})

@app.route("/logs", methods=["GET"])
def get_logs():
    user_id = request.remote_addr
    user_folder = os.path.join(BOT_DATA_DIR, user_id.replace(":", "_"))
    log_file = os.path.join(user_folder, "log.txt")
    if os.path.exists(log_file):
        return open(log_file, "r", encoding="utf-8").read()
    return "No logs found."

# ---------------- RUN SERVER ---------------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
