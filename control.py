#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, requests, random, time, secrets, string, webbrowser, urllib.parse
from datetime import datetime
from termcolor import colored

# ---------------- CONFIG ---------------- #
BOT_SERVER_URL = "https://YOUR_BOT_HOSTING_DOMAIN/run_bot"  # Replace with your bot-hosting endpoint
OWNER_WHATSAPP = "919557954851"
APPROVAL_URL = "https://raw.githubusercontent.com/DH0K3B44Z/Unicode_parsel/main/Approval.txt"

LOG_FILE = "control_log.txt"
PENDING_KEYS_FILE = "pending_keys.txt"
APPROVED_KEYS_FILE = "approved_keys.txt"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
]

# ---------------- HELPERS ---------------- #
def type_print(text, color=None, attrs=None, delay=0.02):
    colored_text = colored(text, color=color, attrs=attrs) if color else text
    for ch in colored_text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def log_line(text):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except:
        pass

# ---------------- APPROVAL ---------------- #
def generate_short_key(length=12):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def save_pending_key(key):
    try:
        with open(PENDING_KEYS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | {key}\n")
    except:
        pass

def mark_key_as_approved(key):
    try:
        with open(APPROVED_KEYS_FILE, "a", encoding="utf-8") as f:
            f.write(key + "\n")
    except:
        pass

def check_approval(key, retries=4, delay=2):
    for _ in range(retries):
        try:
            res = requests.get(APPROVAL_URL, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
            if res.status_code == 200 and key in res.text:
                mark_key_as_approved(key)
                return True
        except:
            pass
        time.sleep(delay)
    return False

def open_whatsapp_with_key(key):
    msg = f"Hello owner, my key: {key}\nPlease approve me for the tool."
    url = f"https://wa.me/{OWNER_WHATSAPP}?text={urllib.parse.quote(msg)}"
    try:
        webbrowser.open(url, new=2)
    except:
        print(f"Send manually: {url}")

def approval_handshake():
    if os.path.exists(APPROVED_KEYS_FILE):
        type_print("\n✅ Key already approved. Continuing...", "green", ["bold"])
        return True
    key = generate_short_key()
    type_print("\n🎫 Your Access Key:", "cyan", ["bold"])
    type_print(key, "yellow", ["bold"])
    save_pending_key(key)
    input(colored("\nPress Enter to open WhatsApp and send the key...", "cyan"))
    open_whatsapp_with_key(key)
    input(colored("\nPress Enter to check approval...", "magenta"))
    if check_approval(key):
        type_print("\n✅ Approved. Continuing...", "green", ["bold"])
        return True
    type_print("\n❌ Not approved yet.", "red", ["bold"])
    return False

# ---------------- BOT CONTROL ---------------- #
def send_files_to_bot(files_data, data_fields):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = requests.post(BOT_SERVER_URL, files=files_data, data=data_fields, headers=headers, timeout=30)
        return response.json() if response.ok else {"status": "error", "msg": response.text}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# ---------------- MAIN MENU ---------------- #
def main():
    os.system("clear")
    type_print("""
░██████╗░█████╗░██╗██╗███╗░░░███╗
██╔════╝██╔══██╗██║██║████╗░████║
╚█████╗░███████║██║██║██╔████╔██║
░╚═══██╗██╔══██║██║██║██║╚██╔╝██║
██████╔╝██║░░██║██║██║██║░╚═╝░██║
╚═════╝░╚═╝░░╚═╝╚═╝╚═╝╚═╝░░░░░╚═╝
""", "cyan", ["bold"])

    if not approval_handshake():
        return

    while True:
        type_print("\n[1] Start Comment Bot\n[2] Show Logs\n[3] Stop Bot\n[4] Exit", "yellow", ["bold"])
        choice = input(colored("Enter your choice: ", "cyan")).strip()

        if choice == "1":
            type_print("\nSelect type:\n[1] User ID\n[2] Pages\n[3] Both", "cyan", ["bold"])
            user_type = input(colored("Enter your number: ", "yellow")).strip()

            token_file = input("Enter token file path: ").strip()
            comment_file = input("Enter comment file path: ").strip()
            post_id = input("Enter post id: ").strip()
            prefix = input("Enter prefix (haters name): ").strip()
            suffix = input("Enter suffix (here name): ").strip()
            interval = input("Enter time interval (seconds): ").strip()

            files_data = {
                "token_file": open(token_file, "rb"),
                "comment_file": open(comment_file, "rb")
            }
            data_fields = {
                "user_type": user_type,
                "post_id": post_id,
                "prefix": prefix,
                "suffix": suffix,
                "interval": interval
            }
            res = send_files_to_bot(files_data, data_fields)
            type_print(f"\n{res}", "green", ["bold"])
            type_print("✅ Bot successfully started!", "green", ["bold"])

        elif choice == "2":
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r") as f:
                    print(f.read())
            else:
                print("No logs found.")

        elif choice == "3":
            try:
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                requests.get(f"{BOT_SERVER_URL}?stop=1", headers=headers, timeout=10)
                type_print("✅ Stop command sent to bot.", "yellow", ["bold"])
            except:
                type_print("❌ Failed to send stop command.", "red", ["bold"])

        elif choice == "4":
            type_print("Exiting...", "red", ["bold"])
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        type_print("\nExiting by user.", "yellow", ["bold"])
        sys.exit(0)
