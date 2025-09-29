#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server-side Bot Manager
- Multi-user isolated
- Runs comment bot workers
- Enforces approval
"""

import os, time, json, threading, requests
from datetime import datetime

DATA_ROOT = "/home/bot/data"
APPROVAL_URL = "https://raw.githubusercontent.com/DH0K3B44Z/Unicode_parsel/main/Approval.txt"

# ---------------- WORKER ---------------- #
class BotWorker(threading.Thread):
    def __init__(self, user_folder):
        super().__init__()
        self.user_folder = user_folder
        self.running = True

    def run(self):
        token_file = os.path.join(self.user_folder,"tokens.txt")
        comment_file = os.path.join(self.user_folder,"comments.txt")
        post_id_file = os.path.join(self.user_folder,"post_id.txt")
        haters_file = os.path.join(self.user_folder,"haters.txt")
        here_file = os.path.join(self.user_folder,"here.txt")
        time_file = os.path.join(self.user_folder,"time.txt")
        log_file = os.path.join(self.user_folder,"log.txt")

        def log(msg):
            ts = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
            with open(log_file,"a",encoding="utf-8") as f:
                f.write(f"[{ts}] {msg}\n")

        # Read files safely
        try:
            tokens = [l.strip() for l in open(token_file) if l.strip()]
            comments = [l.strip() for l in open(comment_file) if l.strip()]
            post_id = open(post_id_file).read().strip()
            prefixes = [l.strip() for l in open(haters_file)] if os.path.exists(haters_file) else []
            suffixes = [l.strip() for l in open(here_file)] if os.path.exists(here_file) else []
            base_time = int(open(time_file).read().strip()) if os.path.exists(time_file) else 60
        except Exception as e:
            log(f"[ERROR] Failed to read files: {e}")
            return

        while self.running and comments:
            for token in tokens:
                if not comments: break
                comment = comments.pop(0)
                prefix = prefixes[0] if prefixes else ""
                suffix = suffixes[0] if suffixes else ""
                full_msg = f"{prefix} {comment} {suffix}".strip()
                # Here we just simulate sending comment
                try:
                    # simulate API call
                    log(f"Sent comment with token {token[:5]}... : {full_msg}")
                except Exception as e:
                    log(f"[ERROR] {e}")
                time.sleep(base_time)

    def stop(self):
        self.running=False

# ---------------- SERVER MANAGEMENT ---------------- #
active_workers = {}

def start_user_worker(user):
    user_folder = os.path.join(DATA_ROOT, user)
    approved = check_user_approval(user_folder)
    if not approved: return False
    if user in active_workers:
        return True
    worker = BotWorker(user_folder)
    worker.start()
    active_workers[user] = worker
    return True

def stop_user_worker(user):
    if user in active_workers:
        active_workers[user].stop()
        del active_workers[user]

def check_user_approval(user_folder):
    key_file = os.path.join(user_folder,"key.txt")
    if not os.path.exists(key_file): return False
    key = open(key_file).read().strip()
    try:
        r = requests.get(APPROVAL_URL, timeout=10)
        return key in r.text
    except:
        return False

# ---------------- SIMPLE API ---------------- #
from flask import Flask, request, send_file
app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload():
    user = request.form.get("user")
    key = request.form.get("key")
    user_folder = os.path.join(DATA_ROOT,user)
    os.makedirs(user_folder, exist_ok=True)
    # Save key
    open(os.path.join(user_folder,"key.txt"),"w").write(key)
    # Save files
    for fkey in request.files:
        f = request.files[fkey]
        f.save(os.path.join(user_folder,f.filename))
    # Start worker
    if start_user_worker(user):
        return {"status":"ok"}
    return {"status":"error"}

@app.route("/logs/<user>")
def logs(user):
    user_folder = os.path.join(DATA_ROOT,user)
    log_file = os.path.join(user_folder,"log.txt")
    return send_file(log_file) if os.path.exists(log_file) else "No logs"

@app.route("/stop/<user>", methods=["POST"])
def stop(user):
    stop_user_worker(user)
    return "ok"

if __name__=="__main__":
    app.run(host="0.0.0.0", port=8000)
