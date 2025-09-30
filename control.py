import requests
import time
import random
import os
import webbrowser
from google.cloud import firestore  # Requires firebase admin setup
import json
import getpass

# ASCII art function
def print_ascii_typing(text, delay=0.05):
    import sys
    for c in text:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

# Load approval keys list from GitHub
def load_approval_keys():
    url = "https://raw.githubusercontent.com/DH0K3B44Z/Unicode_parsel/main/Approval.txt"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            keys = r.text.splitlines()
            return set(k.strip() for k in keys if k.strip())
    except Exception as e:
        print("Approval keys load error:", e)
    return set()

def open_whatsapp(number="+919557954851"):
    url = f"https://wa.me/{number.lstrip('+')}"
    webbrowser.open(url)

def generate_user_key(username):
    return f"{username}DH442NH002"

def is_key_approved(key, approval_keys):
    return key in approval_keys

def firebase_init():
    # Initialize firebase client (credentials json must be in same dir)
    try:
        db = firestore.Client()
        return db
    except Exception as e:
        print("Firestore init failed:", e)
        return None

def save_permanent_key(db, username, key):
    try:
        db.collection("users").document(username).set({"key": key})
        return True
    except:
        return False

def check_existing_key(db, username):
    try:
        user_doc = db.collection("users").document(username).get()
        if user_doc.exists:
            return user_doc.to_dict().get("key","")
    except:
        return ""
    return ""

def upload_user_data(db, username, data):
    # Store input data for backend bot
    try:
        db.collection("input_data").document(username).set(data)
        return True
    except:
        return False

def main():
    clear_screen()
    print_ascii_typing("""
  _____       _       _     _
 / ____|     | |     | |   | |
| (___  _   _| | __ _| |__ | | ___  ___
 ___ | | | | |/ _` | '_ | |/ _ / __|
 ____) | |_| | | (_| | |_) | |  __/__ \\
|_____/ __,_|_|__,_|_.__/|_|___||___/
""", delay=0.04)
    print("Author : Saiim
Bestu : kashiif 🥰 Zk 🌹
Version : 2.0
Tool Type : Paid")
    print("______________")
    print(" D4RFU K1 M44 K1 CHU7")
    print("______________
")

    approval_keys = load_approval_keys()

    username = input("Enter your username: ").strip()
    existing_key = None

    db = firebase_init()
    if db:
        existing_key = check_existing_key(db, username)

    if existing_key:
        key = existing_key
        print(f"Existing approval key found for {username}: {key}")
    else:
        key = generate_user_key(username)
        print(f"Your generated approval key is: {key}")
        print("To get approval, please send this key on WhatsApp.")
        print("Opening WhatsApp...")
        open_whatsapp("+919557954851")
        input("Press Enter after sending the key on WhatsApp...")

        if key not in approval_keys:
            print("Approval key not approved yet. Exiting.")
            return

        if db:
            save_permanent_key(db, username, key)

    print("Approval successful!
")

    # Main interface
    while True:
        clear_screen()
        print_ascii_typing("    [1] Pages
    [2] Main_ID
    [3] Both
    Type your choice: ", delay=0.02)
        choice = input().strip()

        if choice not in ['1','2','3']:
            print("Invalid choice, try again.")
            time.sleep(2)
            continue

        token_file = input("Enter path to token file: ").strip()
        comment_file = input("Enter path to comment file: ").strip()
        post_id = input("Enter Post ID: ").strip()
        prefix = input("Enter prefix text (optional): ").strip()
        suffix = input("Enter suffix text (optional): ").strip()
        time_interval = int(input("Enter time interval (seconds): ").strip())

        # Load token and comments from files locally and upload to firebase for backend processing
        try:
            with open(token_file, 'r', encoding='utf-8') as tf:
                tokens = [line.strip() for line in tf if line.strip()]
            with open(comment_file, 'r', encoding='utf-8') as cf:
                comments = [line.strip() for line in cf if line.strip()]
        except Exception as e:
            print("File reading error:", e)
            return

        user_data = {
            "choice": choice,
            "tokens": tokens,
            "comments": comments,
            "post_id": post_id,
            "prefix": prefix,
            "suffix": suffix,
            "time_interval": time_interval,
            "username": username,
            "key": key,
            "status": "started"
        }

        if db:
            upload_user_data(db, username, user_data)
        print("Data uploaded. Bot started on backend.
")
        # Show menu for logs, restart, stop, exit
        while True:
            print("[1] Show Your Logs")
            print("[2] Start bot again")
            print("[3] Stop your bot")
            print("[4] Exit
")
            option = input("Choose option: ").strip()
            if option == '1':
                # Fetch logs from backend or cloud logs here (suppose)
                print("Feature under development.")
            elif option == '2':
                print("Restarting bot...")
                if db:
                    upload_user_data(db, username, user_data)  # restart sending
            elif option == '3':
                post_to_stop = input("Enter Post ID to stop bot comment on: ").strip()
                if db:
                    db.collection("input_data").document(username).update({"status": "stopped", "stop_post_id": post_to_stop})
                print("Bot stop command sent.")
            elif option == '4':
                print("Exiting UI. Bot runs in background.")
                break
            else:
                print("Invalid option.")
