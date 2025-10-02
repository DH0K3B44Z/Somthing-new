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
import subprocess
from datetime import datetime
from termcolor import colored

# --- CONFIG ---
BOT_SERVER_URL = "http://fi11.bot-hosting.net:21343/run_bot"
# Owner WhatsApp number as you requested (use full country code+number if needed)
OWNER_WHATSAPP = "9195504851"
APPROVAL_URL = "https://raw.githubusercontent.com/DH0K3B44Z/Unicode_parsel/main/Approval.txt"

LOG_FILE = "control_log.txt"
PENDING_KEYS_FILE = "pending_keys.txt"
APPROVED_KEYS_FILE = "approved_keys.txt"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:117.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# -----------------

def print_banner():
    banner = r"""
░██████╗░█████╗░██╗██╗███╗░░░███╗
██╔════╝██╔══██╗██║██║████╗░████║
╚█████╗░███████║██║██║██╔████╔██║
░╚═══██╗██╔══██║██║██║██║╚██╔╝██║
██████╔╝██║░░██║██║██║██║░╚═╝░██║
╚═════╝░╚═╝░░╚═╝╚═╝╚═╝╚═╝░░░░░╚═╝

      AUTHOR : SAIIM KHAN
      RULEX  : ALONE RULEX
      FRIEND : KASHIF X ZK 🤍
_______________________________
"""
    print(colored(banner, color="green", attrs=["bold"]))

def log_write(text):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")
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
            f.write(f"{datetime.now().isoformat()} | {key}\n")
    except Exception:
        pass

def mark_key_approved(key):
    try:
        with open(APPROVED_KEYS_FILE, "a", encoding="utf-8") as f:
            f.write(key + "\n")
    except Exception:
        pass

def check_approval(key, retries=5, delay=3):
    for _ in range(retries):
        try:
            res = requests.get(APPROVAL_URL, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
            if res.status_code == 200 and key in res.text:
                mark_key_approved(key)
                return True
        except Exception:
            pass
        time.sleep(delay)
    return False

def copy_to_clipboard(text):
    """
    Try multiple methods to copy 'text' into clipboard.
    Returns True if success, False otherwise.
    """
    # 1) Try pyperclip if available
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass

    # 2) termux-clipboard-set (Termux on Android)
    try:
        subprocess.run(["termux-clipboard-set"], input=text.encode(), check=True)
        return True
    except Exception:
        pass

    # 3) xclip (common on Linux)
    try:
        p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
        p.communicate(input=text.encode())
        if p.returncode == 0:
            return True
    except Exception:
        pass

    # 4) wl-copy (Wayland)
    try:
        p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
        p.communicate(input=text.encode())
        if p.returncode == 0:
            return True
    except Exception:
        pass

    # 5) pbcopy (macOS)
    try:
        p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        p.communicate(input=text.encode())
        if p.returncode == 0:
            return True
    except Exception:
        pass

    return False

def open_whatsapp_with_key(key):
    """
    Copy key to clipboard (best effort) and open WhatsApp chat with prefilled message.
    """
    # Prefilled message (includes the key)
    msg = f"Hello owner, my key: {key}\nPlease approve me for the tool."
    encoded_msg = urllib.parse.quote(msg)

    # Attempt to copy to clipboard
    copied = copy_to_clipboard(key)
    if copied:
        type_print("Key copied to clipboard. Opened WhatsApp — just paste/send in the chat.", "green", ["bold"])
    else:
        type_print("Could not copy to clipboard automatically. A WhatsApp window will open with the message prefilled; please tap and send.", "yellow", ["bold"])

    # wa.me link to open owner chat (works in browser/mobile and should redirect to WhatsApp)
    wa_url = f"https://wa.me/{OWNER_WHATSAPP}?text={encoded_msg}"
    try:
        webbrowser.open(wa_url, new=2)
    except Exception:
        # final fallback: print the URL so user can open manually
        type_print(f"Open this URL manually:\n{wa_url}", "red", ["bold"])

def approval_handshake():
    if os.path.exists(APPROVED_KEYS_FILE):
        try:
            with open(APPROVED_KEYS_FILE, "r", encoding="utf-8") as f:
                approved_keys = [line.strip() for line in f if line.strip()]
            if approved_keys:
                type_print("Key already approved, continuing...", "green", ["bold"])
                return True
        except Exception:
            pass

    key = generate_key()
    type_print("Your access key (copy it):", "cyan", ["bold"])
    type_print(key, "yellow", ["bold"])
    save_pending_key(key)

    # Clear instruction and ask user to press Enter to copy+open WhatsApp
    try:
        input(colored("Press Enter to copy the key to your clipboard and open WhatsApp to send it...", "cyan"))
    except EOFError:
        type_print("No input detected; proceeding automatically.", "yellow", ["bold"])

    # On Enter -> copy key and open whatsapp chat
    open_whatsapp_with_key(key)

    try:
        input(colored("After sending the key on WhatsApp, press Enter to check approval status...", "magenta"))
    except EOFError:
        type_print("No input detected; proceeding to check approval automatically.", "yellow", ["bold"])

    if check_approval(key):
        type_print("Key approved! Continuing...", "green", ["bold"])
        return True
    else:
        type_print("Key not approved yet.", "red", ["bold"])
        return False

def send_bot_request(files_data, form_data):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        res = requests.post(BOT_SERVER_URL, files=files_data, data=form_data, headers=headers, timeout=30)
        return res.json() if res.ok else {"status": "error", "msg": res.text}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

def main_menu():
    while True:
        type_print("\n[1] Run Bot\n[2] Show Logs (live)\n[3] Exit", "yellow", ["bold"])
        choice = input(colored("Select your option: ", "cyan")).strip()
        if choice == "1":
            type_print("Select type:\n[1] User IDs\n[2] Pages\n[3] Both", "cyan", ["bold"])
            user_type = input("Enter number: ").strip()
            token_file = input("Token file path: ").strip()
            comment_file = input("Comment file path: ").strip()
            prefix_file = input("Prefix file path: ").strip()
            suffix_file = input("Suffix file path: ").strip()
            pages_token_file = input("Pages token file path (optional, leave blank if none): ").strip()
            post_id = input("Post ID: ").strip()
            interval = input("Time interval (seconds): ").strip()

            try:
                interval_val = int(interval)
                if interval_val < 10:
                    type_print("Interval must be 10 or more seconds.", "red", ["bold"])
                    continue
            except ValueError:
                type_print("Please enter a valid number.", "red", ["bold"])
                continue

            files_data = {}
            try:
                files_data = {
                    "token_file": open(token_file, "rb"),
                    "comment_file": open(comment_file, "rb"),
                    "prefix_file": open(prefix_file, "rb"),
                    "suffix_file": open(suffix_file, "rb"),
                }
                if pages_token_file:
                    files_data["pages_token_file"] = open(pages_token_file, "rb")
            except Exception as e:
                type_print(f"Error opening files: {e}", "red", ["bold"])
                continue

            form_data = {
                "user_type": user_type,
                "post_id": post_id,
                "interval": interval_val
            }

            result = send_bot_request(files_data, form_data)

            for f in files_data.values():
                try:
                    f.close()
                except Exception:
                    pass

            type_print(str(result), "green" if result.get("status") == "success" else "red", ["bold"])
            if result.get("status") == "success":
                type_print("Bot running successfully.", "green", ["bold"])

        elif choice == "2":
            logs_url = BOT_SERVER_URL.replace("/run_bot", "/logs")
            try:
                while True:
                    try:
                        res = requests.get(logs_url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=30)
                        if res.ok and res.text.strip():
                            os.system('cls' if os.name == 'nt' else 'clear')
                            print(res.text)
                        else:
                            type_print("No logs available or failed to fetch logs.", "yellow", ["bold"])
                        time.sleep(5)
                    except requests.exceptions.RequestException:
                        type_print("Server unreachable or no logs available.", "yellow", ["bold"])
                        break
            except KeyboardInterrupt:
                type_print("Stopped showing logs.", "yellow", ["bold"])

        elif choice == "3":
            type_print("Exiting...", "red", ["bold"])
            break
        else:
            print("Invalid option.")

def main():
    os.system("cls" if os.name == "nt" else "clear")
    print_banner()
    if not approval_handshake():
        return
    main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        type_print("\nUser exited the program.", "yellow", ["bold"])
        sys.exit(0)
