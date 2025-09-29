#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import random
import requests
import secrets
import string
import urllib.parse
import webbrowser
from datetime import datetime
from termcolor import colored

# CONFIGURATION
BOT_SERVER_URL = "https://your-bot-hosting-domain/run_bot"  # Replace with actual hosting domain
OWNER_WHATSAPP = "919557954851"
APPROVAL_URL = "https://raw.githubusercontent.com/DH0K3B44Z/Unicode_parsel/main/Approval.txt"

LOG_FILE = "control_log.txt"
PENDING_KEYS_FILE = "pending_keys.txt"
APPROVED_KEYS_FILE = "approved_keys.txt"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:117.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def log_write(text):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "
")
    except Exception:
        pass

def type_print(text, color=None, attrs=None, delay=0.02):
    colored_text = colored(text, color=color, attrs=attrs) if color else text
    for ch in colored_text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def generate_key(length=12):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def save_pending_key(key):
    try:
        with open(PENDING_KEYS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | {key}
")
    except:
        pass

def mark_key_approved(key):
    try:
        with open(APPROVED_KEYS_FILE, "a", encoding="utf-8") as f:
            f.write(key + "
")
    except:
        pass

def check_approval(key, retries=4, delay=3):
    for _ in range(retries):
        try:
            res = requests.get(APPROVAL_URL, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
            if res.status_code == 200 and key in res.text:
                mark_key_approved(key)
                return True
        except:
            pass
        time.sleep(delay)
    return False

def open_whatsapp(key):
    msg = f"Hello owner, my key: {key}
Please approve me for the tool."
    url = f"https://wa.me/{OWNER_WHATSAPP}?text={urllib.parse.quote(msg)}"
    try:
        webbrowser.open(url, new=2)
    except:
        print(f"Manually send: {url}")

def approval_handshake():
    if os.path.exists(APPROVED_KEYS_FILE):
        type_print("✅ Key already approved. Continuing...", "green", ["bold"])
        return True
    key = generate_key()
    type_print("🎫 Your Access Key (copy it):", "cyan", ["bold"])
    type_print(key, "yellow", ["bold"])
    save_pending_key(key)
    input(colored("Press Enter to open WhatsApp and send the key...", "cyan"))
    open_whatsapp(key)
    input(colored("Press Enter to check approval status...", "magenta"))
    if check_approval(key):
        type_print("✅ Approved. Proceeding...", "green", ["bold"])
        return True
    else:
        type_print("❌ Not approved yet.", "red", ["bold"])
        return False

def send_bot_request(files_data, form_data):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        res = requests.post(BOT_SERVER_URL, files=files_data, data=form_data, headers=headers, timeout=30)
        return res.json() if res.ok else {"status":"error","msg":res.text}
    except Exception as e:
        return {"status":"error","msg":str(e)}

def main_menu():
    while True:
        type_print("
[1] Start Bot
[2] Show Logs
[3] Exit", "yellow", ["bold"])
        choice = input(colored("Your choice: ", "cyan")).strip()
        if choice == "1":
            type_print("Select type:
[1] User IDs
[2] Pages
[3] Both", "cyan", ["bold"])
            user_type = input("Enter number: ").strip()
            token_file = input("Token file path: ").strip()
            comment_file = input("Comment file path: ").strip()
            post_id = input("Post ID: ").strip()
            prefix = input("Prefix file path (haters): ").strip()
            suffix = input("Suffix file path (yours): ").strip()
            interval = input("Time interval (seconds): ").strip()

            try:
                files_data = {
                    "token_file": open(token_file, "rb"),
                    "comment_file": open(comment_file, "rb"),
                    "prefix_file": open(prefix, "rb"),
                    "suffix_file": open(suffix, "rb")
                }
            except Exception as e:
                type_print(f"File error: {e}", "red", ["bold"])
                continue

            form_data = {
                "user_type": user_type,
                "post_id": post_id,
                "interval": interval
            }

            result = send_bot_request(files_data, form_data)

            for f in files_data.values():
                f.close()

            type_print(str(result), "green" if result.get("status")=="success" else "red", ["bold"])
            if result.get("status") == "success":
                type_print("✅ Bot running successfully.", "green", ["bold"])

        elif choice == "2":
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    print(f.read())
            else:
                print("No logs available.")
        elif choice == "3":
            type_print("Exiting...", "red", ["bold"])
            break
        else:
            print("Invalid choice.")

def main():
    os.system("clear" if os.name != "nt" else "cls")
    if not approval_handshake():
        return
    main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        type_print("
Exiting by user.", "yellow", ["bold"])
        sys.exit(0)
