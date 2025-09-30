#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
import os
import threading
import time
import random
import json
import requests
from datetime import datetime

app = Flask(__name__)

BOT_DATA_DIR = "bot_user_data"
os.makedirs(BOT_DATA_DIR, exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:117.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

active_bots = {}  # ip: threading.Thread

def random_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}

def read_lines(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def post_facebook_comment(token, post_id, message):
    url = f"https://graph.facebook.com/{post_id}/comments"
    params = {"message": message, "access_token": token}
    try:
        r = requests.post(url, params=params, headers=random_headers(), timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def run_bot_thread(user_folder):
    token_file = os.path.join(user_folder, "token_file.txt")
    comment_file = os.path.join(user_folder, "comment_file.txt")
    prefix_file = os.path.join(user_folder, "prefix_file.txt")
    suffix_file = os.path.join(user_folder, "suffix_file.txt")
    settings_file = os.path.join(user_folder, "settings.json")
    log_file = os.path.join(user_folder, "log.txt")
    stop_flag_file = os.path.join(user_folder, "stop.txt")

    if not os.path.isfile(settings_file):
        return

    with open(settings_file, "r", encoding="utf-8") as f:
        settings = json.load(f)

    user_type = settings.get("user_type", "1")
    post_id = settings.get("post_id")
    interval = int(settings.get("interval", 60))

    tokens = read_lines(token_file)
    comments = read_lines(comment_file)
    prefixes = read_lines(prefix_file)
    suffixes = read_lines(suffix_file)

    comment_index = 0

    while True:
        if os.path.exists(stop_flag_file):
            break
        if not tokens or not comments:
            break

        # pick token circularly
        token = tokens[comment_index % len(tokens)]
        # pick comment FIFO
        message = comments[0]

        prefix = random.choice(prefixes) if prefixes else ""
        suffix = random.choice(suffixes) if suffixes else ""

        full_comment = f"{prefix} {message} {suffix}".strip()

        response = post_facebook_comment(token, post_id, full_comment)

        now = datetime.now().strftime("%d-%m-%Y %I:%M %p")
        log_line = f"[{now}] Token: {token[:8]}*** Comment: {full_comment} Result: {response}\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line)

        if "error" in response:
            # remove token that caused error
            tokens.pop(comment_index % len(tokens))
            if not tokens:
                break
            continue

        # remove used comment
        comments.pop(0)
        comment_index += 1

        time.sleep(interval + random.randint(3, 8))

@app.route("/run_bot", methods=["POST"])
def start_bot():
    user_ip = request.remote_addr.replace(":", "_")
    user_folder = os.path.join(BOT_DATA_DIR, user_ip)
    os.makedirs(user_folder, exist_ok=True)

    # Save uploaded files
    if "token_file" in request.files:
        request.files["token_file"].save(os.path.join(user_folder, "token_file.txt"))
    if "comment_file" in request.files:
        request.files["comment_file"].save(os.path.join(user_folder, "comment_file.txt"))
    if "prefix_file" in request.files:
        request.files["prefix_file"].save(os.path.join(user_folder, "prefix_file.txt"))
    if "suffix_file" in request.files:
        request.files["suffix_file"].save(os.path.join(user_folder, "suffix_file.txt"))

    # Save settings JSON
    settings = {
        "user_type": request.form.get("user_type", "1"),
        "post_id": request.form.get("post_id"),
        "interval": request.form.get("interval", 60),
    }
    with open(os.path.join(user_folder, "settings.json"), "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

    # Remove stop flag if exists
    stop_file = os.path.join(user_folder, "stop.txt")
    if os.path.exists(stop_file):
        os.remove(stop_file)

    # Start thread if not running
    if user_ip not in active_bots or not active_bots[user_ip].is_alive():
        thread = threading.Thread(target=run_bot_thread, args=(user_folder,))
        thread.daemon = True
        thread.start()
        active_bots[user_ip] = thread

    return jsonify({"status": "success", "msg": "Bot started for your session."})

@app.route("/run_bot", methods=["GET"])
def stop_bot():
    user_ip = request.remote_addr.replace(":", "_")
    user_folder = os.path.join(BOT_DATA_DIR, user_ip)
    os.makedirs(user_folder, exist_ok=True)

    stop_file = os.path.join(user_folder, "stop.txt")
    with open(stop_file, "w", encoding="utf-8") as f:
        f.write("stop")

    return jsonify({"status": "success", "msg": "Bot stop signal sent."})

@app.route("/logs", methods=["GET"])
def get_logs():
    user_ip = request.remote_addr.replace(":", "_")
    log_file = os.path.join(BOT_DATA_DIR, user_ip, "log.txt")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            return f.read()
    return "No logs available."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
