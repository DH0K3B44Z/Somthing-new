#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
control.py - Termux client
Uploads files to server and signals bot manager.
Includes choice: User Id / Pages / Both
"""
import os
import sys
import time
import secrets
import string
import urllib.parse
import webbrowser
import requests
from datetime import datetime
from termcolor import colored

# ---------------- CONFIG ---------------- #
SERVER_URL = "http://bot-hosting.net:8000"  # Change to your server (include port if needed)
APPROVAL_URL = "https://raw.githubusercontent.com/DH0K3B44Z/Unicode_parsel/main/Approval.txt"
OWNER_WHATSAPP = "919557954851"

# ---------------- HELPERS ---------------- #
def type_print(text, color=None, attrs=None, delay=0.005):
    from sys import stdout
    try:
        from termcolor import colored as tcol
        colored_text = tcol(text, color=color, attrs=attrs) if color else text
    except Exception:
        colored_text = text
    for ch in colored_text:
        stdout.write(ch)
        stdout.flush()
        time.sleep(delay)
    print()

def display_banner():
    ascii_art = """
░██████╗░█████╗░██╗██╗███╗░░░███╗
██╔════╝██╔══██╗██║██║████╗░████║
╚█████╗░███████║██║██║██╔████╔██║
░╚═══██╗██╔══██║██║██║██║╚██╔╝██║
██████╔╝██║░░██║██║██║██║░╚═╝░██║
╚═════╝░╚═╝░░╚═╝╚═╝╚═╝╚═╝░░░░░╚═╝
>>>  FB AUTO COMMENT BOT CONTROL  <<<
"""
    type_print(ascii_art, "cyan", ["bold"])

def generate_key(length=12):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def check_approval(key):
    try:
        r = requests.get(APPROVAL_URL, timeout=10)
        if r.status_code == 200:
            lines = [ln.strip().lstrip("﻿") for ln in r.text.splitlines() if ln.strip()]
            return key in lines
    except Exception:
        pass
    return False

def send_key_whatsapp(key):
    message = f"Hello owner, my key: {key}\\nPlease approve me for the tool."
    url = f"https://wa.me/{OWNER_WHATSAPP}?text={urllib.parse.quote(message)}"
    try:
        webbrowser.open(url, new=2)
    except Exception:
        print("Open this URL to message owner:")
        print(url)

def upload_files(user, mode, file_paths, key):
    """
    Sends multipart/form-data to server endpoint /upload
    file_paths: dict with keys tokens, comments, haters, here, time, post_id (strings or paths)
    """
    url = f"{SERVER_URL}/upload"
    files = {}
    data = {"user": user, "mode": mode, "key": key}
    # attach files if they exist
    for form_name, path in file_paths.items():
        if not path:
            continue
        # if post_id or time are direct values (not file paths), send as data
        if form_name in ("post_id", "time") and not os.path.isfile(path):
            data[form_name] = path
            continue
        if os.path.isfile(path):
            try:
                files[form_name] = open(path, "rb")
            except Exception as e:
                print(f"[ERROR] Could not open {path}: {e}")
                return {"status": "error", "error": str(e)}
    try:
        r = requests.post(url, files=files, data=data, timeout=30)
        for f in files.values():
            try: f.close()
            except: pass
        if r.status_code == 200:
            return r.json()
        else:
            return {"status": "error", "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ---------------- UI FLOWS ---------------- #
def ask_file_paths():
    paths = {}
    paths['tokens'] = input("Enter your token file path: ").strip()
    paths['comments'] = input("Enter your comment file path: ").strip()
    # Post ID: directly accept a value
    paths['post_id'] = input("Type your post ID: ").strip()
    # prefix and suffix can be direct text (user asked manual typing)
    pref = input("Type haters name (prefix) (leave blank to skip): ").strip()
    if pref:
        # create a temp local file with this single prefix so server receives as file
        tmp = f"__tmp_prefix_{int(time.time())}.txt"
        with open(tmp, "w", encoding="utf-8") as f: f.write(pref + "\n")
        paths['haters'] = tmp
    else:
        paths['haters'] = ""
    suf = input("Type here name (suffix) (leave blank to skip): ").strip()
    if suf:
        tmp2 = f"__tmp_suffix_{int(time.time())}.txt"
        with open(tmp2, "w", encoding="utf-8") as f: f.write(suf + "\n")
        paths['here'] = tmp2
    else:
        paths['here'] = ""
    interval = input("Type time interval in seconds (e.g. 60): ").strip()
    paths['time'] = interval  # will be sent as data
    return paths

def main_menu():
    os.system("clear")
    display_banner()
    type_print("[1] Start Comment Bot", "yellow", ["bold"])
    type_print("[2] Show Logs", "yellow", ["bold"])
    type_print("[3] Stop Your Bot", "yellow", ["bold"])
    ch = input("\nSelect an option: ").strip()
    if ch not in ("1","2","3"):
        print("Invalid choice")
        return

    user = input("Enter your username (server folder name): ").strip()
    if not user:
        print("Username required")
        return

    # Approval handshake
    key = generate_key()
    if not check_approval(key):
        type_print("\n🎫 Your Unique Access Key (copy this):", "cyan", ["bold"])
        type_print(key, "yellow", ["bold"])
        input(colored("\nPress Enter to open WhatsApp and send the key...", "cyan") if 'colored' in globals() else "\nPress Enter to open WhatsApp and send the key...")
        send_key_whatsapp(key)
        input("Press Enter to check approval now...")
        if not check_approval(key):
            type_print("❌ Key not approved. Ask owner to add it to Approval.txt on GitHub.", "red", ["bold"])
            return
        else:
            type_print("✅ Key approved. Continuing...", "green", ["bold"])

    # Option flows
    if ch == "1":
        # ask mode like original script
        type_print("\nSelect type to use:", "cyan", ["bold"])
        type_print("[1] User Id   [2] Pages   [3] Both", "yellow", ["bold"])
        choice = input("Enter your number: ").strip()
        if choice == "1":
            mode = "user"
        elif choice == "2":
            mode = "pages"
        elif choice == "3":
            mode = "both"
        else:
            print("Invalid mode")
            return

        paths = ask_file_paths()
        print("\nUploading files and starting bot (this may take a few seconds)...")
        resp = upload_files(user, mode, paths, key)
        # cleanup temp prefix/suffix files if created
        for tmpk in ("haters","here"):
            p = paths.get(tmpk)
            if p and p.startswith("__tmp_") and os.path.exists(p):
                os.remove(p)
        if resp.get("status") == "ok":
            type_print("\n✅ Your bot successfully started", "green", ["bold"])
            # inner menu
            while True:
                print("\n[1] Show your bot (logs)\n[2] Stop your bot\n[3] Exit")
                sub = input("Enter option: ").strip()
                if sub == "1":
                    # fetch logs (simple)
                    try:
                        r = requests.get(f"{SERVER_URL}/logs/{user}", timeout=20)
                        if r.status_code == 200:
                            print("\n--- LOGS ---\n")
                            print(r.text)
                        else:
                            print("[ERROR] Could not fetch logs.")
                    except Exception as e:
                        print(f"[ERROR] {e}")
                elif sub == "2":
                    try:
                        r = requests.post(f"{SERVER_URL}/stop/{user}", timeout=10)
                        if r.status_code == 200:
                            print("⛔ Your bot stopped.")
                        else:
                            print("[ERROR] Stop request failed.")
                    except Exception as e:
                        print(f"[ERROR] {e}")
                elif sub == "3":
                    break
                else:
                    print("Invalid option")
        else:
            print("Failed to start bot:", resp.get("error"))

    elif ch == "2":
        # show logs quick
        try:
            r = requests.get(f"{SERVER_URL}/logs/{user}", timeout=20)
            if r.status_code == 200:
                print(r.text)
            else:
                print("[ERROR] Could not fetch logs.")
        except Exception as e:
            print(f"[ERROR] {e}")

    elif ch == "3":
        try:
            r = requests.post(f"{SERVER_URL}/stop/{user}", timeout=10)
            if r.status_code == 200:
                print("⛔ Your bot stopped.")
            else:
                print("[ERROR] Stop request failed.")
        except Exception as e:
            print(f"[ERROR] {e}")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
