# backend.py
from flask import Flask, request, jsonify
import time
import random
import requests
import logging
import sys
import threading
import secrets
import json
import os

app = Flask(__name__)

# ================== CONFIG ==================
API_KEYS_FILE = "api_keys.json"   # persistent store for api keys
LOG_LIMIT = 100
# ============================================

# Colored logging setup (same as before)
class ColorFormatter(logging.Formatter):
    RESET_SEQ = "\u001B[0m"
    COLOR_SEQ = "\u001B[1;{}m"
    COLORS = {'INFO': 32, 'ERROR': 31, 'WARNING': 33, 'DEBUG': 34}
    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            color = self.COLOR_SEQ.format(self.COLORS[levelname])
            record.levelname = color + levelname + self.RESET_SEQ
            record.msg = color + str(record.msg) + self.RESET_SEQ
        return super().format(record)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(ColorFormatter('%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

ascii_logo = """
\u001B[1;32m
  ____       _          _   
 |  _  ___ | |__   ___| |_ 
 | |_) / _ | '_  / _  __|
 |  __/ (_) | |_) |  __/ |_ 
 |_|   ___/|_.__/ ___|__|
\u001B[0m
"""
app.logger.info(ascii_logo)

# Shared bot data
bot_data = {
    "status": "stopped",
    "username": "",
    "tokens": [],
    "comments": [],
    "post_id": "",
    "prefix": "",
    "suffix": "",
    "interval": 10,
    "logs": []
}
data_lock = threading.Lock()

# API keys mapping: key -> username
api_keys = {}
api_keys_lock = threading.Lock()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

# ========= Persistence for API keys =========
def load_api_keys():
    global api_keys
    if os.path.exists(API_KEYS_FILE):
        try:
            with open(API_KEYS_FILE, "r") as f:
                api_keys = json.load(f)
                app.logger.info(f"Loaded {len(api_keys)} API keys from {API_KEYS_FILE}")
        except Exception as e:
            app.logger.error(f"Failed loading API keys: {e}")
            api_keys = {}
    else:
        api_keys = {}

def save_api_keys():
    try:
        with open(API_KEYS_FILE, "w") as f:
            json.dump(api_keys, f)
    except Exception as e:
        app.logger.error(f"Failed saving API keys: {e}")

load_api_keys()
# ============================================

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def require_api_key(f):
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-KEY")
        with api_keys_lock:
            if not key or key not in api_keys:
                return jsonify({"error": "Unauthorized - invalid or missing API key"}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def send_comment(token, post_id, message):
    url = f"https://graph.facebook.com/{post_id}/comments"
    headers = {"User-Agent": get_random_user_agent()}
    params = {"access_token": token, "message": message}
    try:
        response = requests.post(url, params=params, headers=headers)
        return response
    except Exception as e:
        app.logger.error(f"Exception sending comment: {e}")
        return None

def add_log(msg):
    with data_lock:
        bot_data["logs"].append({"time": time.asctime(), "msg": msg})
        bot_data["logs"] = bot_data["logs"][-LOG_LIMIT:]

# --------- Auth endpoints for key management ----------
@app.route('/register', methods=['POST'])
def register():
    """
    Body: {"username": "user1"}
    Returns: {"api_key": "<generated-key>"}
    """
    j = request.json or {}
    username = j.get("username")
    if not username:
        return jsonify({"error": "username required"}), 400

    # generate secure random key
    new_key = secrets.token_urlsafe(32)
    with api_keys_lock:
        api_keys[new_key] = username
        save_api_keys()
    app.logger.info(f"Registered new API key for user '{username}'")
    return jsonify({"api_key": new_key}), 201

@app.route('/revoke', methods=['POST'])
def revoke():
    """
    Body: {"api_key": "<key>"} or {"username":"user1"} -> revoke matching keys
    """
    j = request.json or {}
    key = j.get("api_key")
    username = j.get("username")
    removed = []
    with api_keys_lock:
        if key:
            if key in api_keys:
                removed.append((key, api_keys.pop(key)))
        elif username:
            for k, u in list(api_keys.items()):
                if u == username:
                    removed.append((k, u))
                    api_keys.pop(k, None)
        else:
            return jsonify({"error": "api_key or username required"}), 400
        save_api_keys()
    if not removed:
        return jsonify({"message": "No matching key(s) found"}), 404
    return jsonify({"revoked": [{"api_key": k, "username": u} for (k,u) in removed]}), 200

@app.route('/list_keys', methods=['GET'])
def list_keys():
    """
    Optional query param ?username=foo
    (No auth on this endpoint — you can choose to protect it. Right now it's open.)
    """
    username = request.args.get("username")
    with api_keys_lock:
        if username:
            filtered = {k: u for k,u in api_keys.items() if u == username}
            return jsonify(filtered)
        return jsonify(api_keys)

# ----------------------------------------------------

@app.route('/update', methods=['POST'])
@require_api_key
def update():
    new_data = request.json
    if not new_data:
        app.logger.error("No data received in update request")
        return jsonify({"error": "No data provided"}), 400
    with data_lock:
        bot_data.update(new_data)
    app.logger.info("Bot data updated via /update")
    return jsonify({"message": "Data updated"}), 200

@app.route('/status', methods=['GET'])
@require_api_key
def status():
    with data_lock:
        return jsonify(bot_data)

@app.route('/start', methods=['POST'])
@require_api_key
def start_bot():
    with data_lock:
        if bot_data["status"] == "started":
            return jsonify({"message": "Bot already running"}), 409
        bot_data["status"] = "started"
    app.logger.info("Bot started via /start")
    return jsonify({"message": "Bot started"}), 200

@app.route('/stop', methods=['POST'])
@require_api_key
def stop_bot():
    with data_lock:
        if bot_data["status"] == "stopped":
            return jsonify({"message": "Bot already stopped"}), 409
        bot_data["status"] = "stopped"
    app.logger.info("Bot stopped via /stop")
    return jsonify({"message": "Bot stopped"}), 200

def bot_runner():
    while True:
        with data_lock:
            if bot_data["status"] != "started":
                pass
            else:
                tokens = bot_data["tokens"]
                comments = bot_data["comments"]
                post_id = bot_data["post_id"]
                prefix = bot_data["prefix"]
                suffix = bot_data["suffix"]
                interval = bot_data["interval"]

                for token in tokens:
                    for comment in comments:
                        # check status inside loop (non-atomic read)
                        if bot_data["status"] == "stopped":
                            break
                        full_comment = f"{prefix}{comment}{suffix}"
                        resp = send_comment(token, post_id, full_comment)
                        if resp and resp.status_code == 200:
                            log_msg = f"Comment sent: {full_comment}"
                            app.logger.info(f"\u001B[1;32m{log_msg}\u001B[0m")
                        else:
                            error_msg = resp.text if resp else "No response"
                            log_msg = f"Failed to send: {full_comment} | Error: {error_msg}"
                            app.logger.error(f"\u001B[1;31m{log_msg}\u001B[0m")
                        add_log(log_msg)
                        time.sleep(interval)
        time.sleep(5)

if __name__ == '__main__':
    runner_thread = threading.Thread(target=bot_runner, daemon=True)
    runner_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=False)
