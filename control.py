#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control Script - Termux Client
- Handles file input
- Sends data to server
- Starts/stops user bot worker
- Shows logs
"""

import os, sys, time, requests, secrets, string, urllib.parse, webbrowser
from datetime import datetime
from termcolor import colored

# ---------------- CONFIG ---------------- #
SERVER_URL = "http://bot-hosting.net"  # Change to your server
APPROVAL_URL = "https://raw.githubusercontent.com/DH0K3B44Z/Unicode_parsel/main/Approval.txt"
OWNER_WHATSAPP = "919557954851"
DATA_FOLDER = "user_data"

# ---------------- HELPERS ---------------- #
def type_print(text, color=None, attrs=None, delay=0.02):
    from sys import stdout
    from termcolor import colored as term_colored
    colored_text = term_colored(text, color=color, attrs=attrs) if color else text
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
"""
    type_print(ascii_art, "cyan", ["bold"])

def generate_key(length=12):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def check_approval(key):
    try:
        res = requests.get(APPROVAL_URL, timeout=10)
        if res.status_code == 200 and key in res.text:
            return True
    except: pass
    return False

def send_key_whatsapp(key):
    msg = f"Hello owner, my key: {key}\nPlease approve me for the tool."
    url = f"https://wa.me/{OWNER_WHATSAPP}?text={urllib.parse.quote(msg)}"
    try:
        webbrowser.open(url, new=2)
    except:
        print(f"Send manually: {url}")

def upload_files(user, paths, key):
    url = f"{SERVER_URL}/upload"
    files = {}
    for k,v in paths.items():
        try: files[k] = open(v,"rb")
        except Exception as e: print(f"[ERROR] {e}")
    data = {"user": user, "key": key}
    try:
        r = requests.post(url, files=files, data=data, timeout=20)
        return r.json() if r.ok else {"status":"error"}
    except: return {"status":"error"}

def user_input_paths():
    paths = {}
    paths['tokens'] = input("Enter your token file path: ").strip()
    paths['comments'] = input("Enter your comment file path: ").strip()
    paths['haters'] = input("Enter haters (prefix) file path: ").strip()
    paths['here'] = input("Enter here (suffix) file path: ").strip()
    paths['time'] = input("Enter time interval (seconds): ").strip()
    paths['post_id'] = input("Enter full post id: ").strip()
    return paths

# ---------------- MAIN ---------------- #
def main():
    os.system("clear")
    display_banner()
    type_print("[1] Start Comment Bot\n[2] Show Logs\n[3] Stop Your Bot", "yellow", ["bold"])
    choice = input("Select option: ").strip()
    
    user = input("Enter your username/id: ").strip()
    key = generate_key()
    
    if not check_approval(key):
        type_print(f"\n🎫 Your Unique Access Key: {key}", "yellow", ["bold"])
        input("Press Enter to open WhatsApp and send key to owner...")
        send_key_whatsapp(key)
        input("Press Enter to check approval...")
        if not check_approval(key):
            type_print("❌ Key not approved yet. Ask owner to add it.", "red", ["bold"])
            return
    
    if choice == '1':
        paths = user_input_paths()
        result = upload_files(user, paths, key)
        if result.get("status")=="ok":
            type_print("✅ Your bot successfully started!", "green", ["bold"])
        else:
            type_print("❌ Failed to start bot!", "red", ["bold"])
    elif choice=='2':
        # fetch logs
        r = requests.get(f"{SERVER_URL}/logs/{user}")
        print(r.text if r.ok else "[ERROR] Cannot fetch logs")
    elif choice=='3':
        # stop bot
        requests.post(f"{SERVER_URL}/stop/{user}")
        type_print("Bot stopped.", "cyan", ["bold"])
    else:
        type_print("Invalid option", "red", ["bold"])

if __name__=="__main__":
    try:
        main()
    except KeyboardInterrupt:
        type_print("\nExiting...", "yellow", ["bold"])
