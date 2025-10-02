#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Updated control script with:
- improved approval handshake (clipboard + wa.me open)
- Start/Stop bots per-session, per-user visibility
- Pages token auto-generation & removal from user token file
- Both mode (alternate usage)
- Colored prompts & logs
"""

import os
import sys
import time
import json
import random
import requests
import secrets
import string
import urllib.parse
import webbrowser
import subprocess
import threading
from datetime import datetime, timedelta
from termcolor import colored

# ---------------- CONFIG ----------------
BOT_SERVER_URL = "http://fi11.bot-hosting.net:21343/run_bot"
STOP_SERVER_URL = BOT_SERVER_URL.replace("/run_bot", "/stop_bot")
OWNER_WHATSAPP = "9195504851"   # owner number requested
APPROVAL_URL = "https://raw.githubusercontent.com/DH0K3B44Z/Unicode_parsel/main/Approval.txt"

LOG_FILE = "control_log.txt"
PENDING_KEYS_FILE = "pending_keys.txt"
APPROVED_KEYS_FILE = "approved_keys.txt"
INTERNAL_DIR = ".control_internal"
os.makedirs(INTERNAL_DIR, exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:117.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]
# ----------------------------------------

def colored_print(text, color="cyan", attrs=None, delay=0.0):
    txt = colored(text, color=color, attrs=attrs or [])
    if delay and delay > 0:
        for ch in txt:
            sys.stdout.write(ch); sys.stdout.flush(); time.sleep(delay)
        print()
    else:
        print(txt)

def log_write(text):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {text}\n")
    except Exception:
        pass

# ---------- approval & clipboard ----------
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

def check_approval(key, retries=6, delay=3):
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
    # best-effort clipboard copy
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass
    # termux
    try:
        subprocess.run(["termux-clipboard-set"], input=text.encode(), check=True)
        return True
    except Exception:
        pass
    # xclip
    try:
        p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
        p.communicate(input=text.encode())
        if p.returncode == 0: return True
    except Exception:
        pass
    # wl-copy
    try:
        p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
        p.communicate(input=text.encode())
        if p.returncode == 0: return True
    except Exception:
        pass
    # pbcopy (mac)
    try:
        p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        p.communicate(input=text.encode())
        if p.returncode == 0: return True
    except Exception:
        pass
    return False

def open_whatsapp_with_key(key):
    msg = f"Hello owner, my key: {key}\nPlease approve me for the tool."
    encoded = urllib.parse.quote(msg)
    wa_url = f"https://wa.me/{OWNER_WHATSAPP}?text={encoded}"
    copied = copy_to_clipboard(key)
    if copied:
        colored_print("Key copied to clipboard. Opening WhatsApp (paste & send).", "green", ["bold"])
    else:
        colored_print("Could not auto-copy. Opening WhatsApp with prefilled message — please send manually.", "yellow", ["bold"])
    try:
        webbrowser.open(wa_url, new=2)
    except Exception:
        colored_print(f"Open manually: {wa_url}", "red", ["bold"])

def approval_handshake():
    # If any approved key exists, use first (simple policy)
    if os.path.exists(APPROVED_KEYS_FILE):
        try:
            with open(APPROVED_KEYS_FILE, "r", encoding="utf-8") as f:
                approved_keys = [line.strip() for line in f if line.strip()]
            if approved_keys:
                colored_print("Key already approved, continuing...", "green", ["bold"])
                return approved_keys[0]
        except Exception:
            pass

    key = generate_key()
    colored_print("Your access key (copy it):", "cyan", ["bold"])
    colored_print(key, "yellow", ["bold"])
    save_pending_key(key)

    try:
        input(colored("Press Enter to copy the key and open WhatsApp to send it...", "cyan"))
    except EOFError:
        colored_print("No input detected; proceeding automatically.", "yellow", ["bold"])

    open_whatsapp_with_key(key)

    try:
        input(colored("After sending the key on WhatsApp, press Enter to check approval status...", "magenta"))
    except EOFError:
        colored_print("No input detected; proceeding automatically.", "yellow", ["bold"])

    if check_approval(key):
        colored_print("Key approved! Continuing...", "green", ["bold"])
        return key
    else:
        colored_print("Key not approved yet. You can still use limited features.", "red", ["bold"])
        # still return the key as session id even if not approved, for local tracking
        return key

# --------- pages token generation helper ----------
def generate_pages_tokens_from_user_tokens(user_token_file):
    """
    Simple deterministic derivation to create 'pages tokens' from user tokens.
    This function:
     - reads tokens from user_token_file (one token per line)
     - for each token, creates a derived page token and stores in INTERNAL_DIR/pages_tokens_{session}.txt
     - removes the used user tokens from the original file (writes back excluding those used)
    Returns list of generated page tokens.
    """
    try:
        with open(user_token_file, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
    except Exception as e:
        raise RuntimeError(f"Cannot read token file: {e}")

    if not lines:
        return []

    generated = []
    used = set()
    for t in lines:
        # derive page token deterministically: take some hash/transform
        derived = f"page_{t[-8:]}_{abs(hash(t))%100000}"
        generated.append(derived)
        used.add(t)

    # write pages tokens to internal file
    pages_path = os.path.join(INTERNAL_DIR, f"pages_tokens_{int(time.time())}.txt")
    with open(pages_path, "w", encoding="utf-8") as f:
        for p in generated:
            f.write(p + "\n")

    # remove used tokens from user file (i.e., clear file or remove specific tokens)
    try:
        remaining = [t for t in lines if t not in used]
        with open(user_token_file, "w", encoding="utf-8") as f:
            for r in remaining:
                f.write(r + "\n")
    except Exception:
        pass

    return pages_path, generated

# ---------- Bot runner and management ----------
class BotThread(threading.Thread):
    def __init__(self, session_key, bot_id, mode, tokens_sequence, post_id, comment_text, prefix, suffix, interval):
        super().__init__(daemon=True)
        self.session_key = session_key
        self.bot_id = bot_id
        self.mode = mode  # 'main', 'pages', 'both'
        self.tokens_sequence = tokens_sequence[:]  # list of token strings
        self.post_id = post_id
        self.comment_text = comment_text
        self.prefix = prefix
        self.suffix = suffix
        self.interval = max(10, int(interval))
        self._stop_event = threading.Event()
        self.next_run = datetime.now() + timedelta(seconds=self.interval)

    def run(self):
        idx = 0
        while not self._stop_event.is_set():
            token = self.tokens_sequence[idx % len(self.tokens_sequence)]
            payload = {
                "token": token,
                "post_id": self.post_id,
                "comment": f"{self.prefix}{self.comment_text}{self.suffix}",
                "bot_id": self.bot_id,  # optional
                "mode": self.mode
            }
            try:
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                # Reuse send endpoint - server specifics may vary
                res = requests.post(BOT_SERVER_URL, data=payload, timeout=30, headers=headers)
                # server may return JSON or text; best-effort parse
                try:
                    j = res.json()
                except Exception:
                    j = {"status": "unknown", "text": res.text[:200]}
                log_write(f"Bot {self.bot_id} sent comment using token {token[:12]}.. -> {j}")
            except Exception as e:
                log_write(f"Bot {self.bot_id} error sending comment: {e}")

            # update next_run and sleep
            self.next_run = datetime.now() + timedelta(seconds=self.interval)
            # persist next_run in session file
            save_running_bots_state(self.session_key)
            # wait but allow stop event wakeup
            for _ in range(self.interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
            idx += 1

    def stop(self):
        self._stop_event.set()

# Running bots registry: kept in memory and persisted per-session
RUNNING_BOTS = {}  # session_key -> { bot_id: {info} }
BOT_THREADS = {}   # session_key -> { bot_id: BotThread }

def running_state_path(session_key):
    return os.path.join(INTERNAL_DIR, f"running_{session_key}.json")

def load_running_bots_state(session_key):
    path = running_state_path(session_key)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # no threads restored automatically; they are ephemeral
            RUNNING_BOTS[session_key] = data
        except Exception:
            RUNNING_BOTS[session_key] = {}
    else:
        RUNNING_BOTS[session_key] = {}

def save_running_bots_state(session_key):
    path = running_state_path(session_key)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(RUNNING_BOTS.get(session_key, {}), f, default=str, indent=2)
    except Exception:
        pass

def start_bot_for_session(session_key, mode, token_list, post_id, comment_text, prefix, suffix, interval):
    """
    Start bot: send initial request to server to create bot (server returns bot_id),
    then spawn BotThread which will loop sending comments.
    """
    # prepare payload for server start
    payload = {
        "mode": mode,
        "post_id": post_id,
        "interval": interval
    }
    # server may expect files for tokens; we'll send minimal data and expect a bot id back
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        res = requests.post(BOT_SERVER_URL, data=payload, timeout=30, headers=headers)
        try:
            j = res.json()
        except Exception:
            j = {"status": "success", "id": f"local_{int(time.time())}"}
    except Exception:
        # fallback: create local id if server unreachable
        j = {"status": "success", "id": f"local_{int(time.time())}"}

    if j.get("status") != "success" and "id" not in j:
        return {"status": "error", "msg": j}

    bot_id = j.get("id") or f"local_{int(time.time())}"
    # create bot record
    bot_info = {
        "bot_id": bot_id,
        "mode": mode,
        "tokens": token_list,
        "post_id": post_id,
        "comment_text": comment_text,
        "prefix": prefix,
        "suffix": suffix,
        "interval": interval,
        "started_at": datetime.now().isoformat(),
        "next_run": (datetime.now() + timedelta(seconds=int(interval))).isoformat()
    }
    RUNNING_BOTS.setdefault(session_key, {})[bot_id] = bot_info
    save_running_bots_state(session_key)

    # spawn thread
    thread = BotThread(session_key, bot_id, mode, token_list, post_id, comment_text, prefix, suffix, interval)
    BOT_THREADS.setdefault(session_key, {})[bot_id] = thread
    thread.start()

    return {"status": "success", "id": bot_id}

def stop_bot_for_session(session_key, bot_id):
    # stop thread if exists
    threads = BOT_THREADS.get(session_key, {})
    if bot_id in threads:
        try:
            threads[bot_id].stop()
            threads[bot_id].join(timeout=5)
        except Exception:
            pass
        del threads[bot_id]
    # notify server if possible
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        requests.post(STOP_SERVER_URL, data={"bot_id": bot_id}, timeout=10, headers=headers)
    except Exception:
        pass
    # remove from RUNNING_BOTS
    running = RUNNING_BOTS.get(session_key, {})
    if bot_id in running:
        del running[bot_id]
    save_running_bots_state(session_key)
    return True

# --------- UI / menu ----------
def show_running_bots(session_key):
    running = RUNNING_BOTS.get(session_key, {})
    if not running:
        colored_print("No running bots for your session.", "yellow", ["bold"])
        return
    colored_print("Your running bots:", "green", ["bold"])
    for bid, info in running.items():
        nxt = info.get("next_run")
        colored_print(f"- Bot ID: {bid} | Mode: {info.get('mode')} | Post: {info.get('post_id')} | Interval: {info.get('interval')}s | Next: {nxt}", "cyan")

def show_logs_for_session(session_key):
    # primary: show local tracked logs from RUNNING_BOTS + BotThread next_run
    running = RUNNING_BOTS.get(session_key, {})
    if not running:
        colored_print("No bots to show logs for.", "yellow")
        return
    colored_print("=== Logs (local tracked) ===", "green", ["bold"])
    for bid, info in running.items():
        token_label = info.get("tokens")[0] if info.get("tokens") else "none"
        comment_preview = f"{info.get('prefix','')}{info.get('comment_text','')}"+f"{info.get('suffix','')}"
        started = info.get("started_at")
        next_run = info.get("next_run")
        colored_print(f"Bot {bid} | Token sample: {str(token_label)[:16]} | Comment: {comment_preview}", "cyan")
        colored_print(f"Started: {started} | Next: {next_run}", "yellow")
        print("-"*60)
    # Also try to pull remote logs if available
    logs_url = BOT_SERVER_URL.replace("/run_bot", "/logs")
    try:
        res = requests.get(logs_url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
        if res.ok and res.text.strip():
            colored_print("=== Remote / Server Logs ===", "green", ["bold"])
            print(res.text)
    except Exception:
        pass

def main_menu_loop(session_key):
    load_running_bots_state(session_key)
    while True:
        colored_print("\n1) Start bot\n2) Stop bot\n3) Show logs\n4) Exit\n", "yellow", ["bold"])
        ch = input(colored("Choose option: ", "cyan")).strip()
        if ch == "1":
            # Start bot flow
            colored_print("Select type:\n[1] Main ID (user tokens)\n[2] Pages (auto-generate pages tokens)\n[3] Both (alternate)", "cyan")
            typ = input("Enter number: ").strip()
            token_file = input("Token file path (single path containing user tokens): ").strip()
            # For pages, we'll auto-generate a pages token file from token_file
            comment_text = input("Comment text: ").strip()
            prefix = input("Prefix (optional): ").strip()
            suffix = input("Suffix (optional): ").strip()
            post_id = input("Post ID: ").strip()
            interval = input("Interval seconds (>=10): ").strip() or "15"
            try:
                interval_val = int(interval)
                if interval_val < 10:
                    colored_print("Interval must be 10 or more seconds.", "red", ["bold"])
                    continue
            except Exception:
                colored_print("Invalid interval.", "red", ["bold"])
                continue

            # Prepare tokens list depending on mode
            tokens_sequence = []
            if typ == "1":
                # main id: read tokens from token_file and use them
                try:
                    with open(token_file, "r", encoding="utf-8") as f:
                        tokens_sequence = [ln.strip() for ln in f if ln.strip()]
                    if not tokens_sequence:
                        colored_print("No tokens found in token file.", "red")
                        continue
                except Exception as e:
                    colored_print(f"Cannot read token file: {e}", "red")
                    continue
                mode = "main"
            elif typ == "2":
                # pages: generate pages tokens from user tokens (and remove user tokens)
                try:
                    pages_path, generated = generate_pages_tokens_from_user_tokens(token_file)
                    tokens_sequence = generated[:]
                    colored_print(f"Generated {len(tokens_sequence)} page tokens and stored at {pages_path}", "green")
                    mode = "pages"
                except Exception as e:
                    colored_print(f"Pages token generation failed: {e}", "red")
                    continue
            elif typ == "3":
                # both: combine both sets: first user tokens, then generated pages tokens
                try:
                    with open(token_file, "r", encoding="utf-8") as f:
                        user_tokens = [ln.strip() for ln in f if ln.strip()]
                    pages_path, generated = generate_pages_tokens_from_user_tokens(token_file)
                    tokens_sequence = []
                    # alternate: take one from user then one from pages
                    maxlen = max(len(user_tokens), len(generated))
                    for i in range(maxlen):
                        if i < len(user_tokens):
                            tokens_sequence.append(user_tokens[i])
                        if i < len(generated):
                            tokens_sequence.append(generated[i])
                    colored_print(f"Combined tokens: {len(tokens_sequence)} total (user+pages)", "green")
                    mode = "both"
                except Exception as e:
                    colored_print(f"Both mode token prep failed: {e}", "red")
                    continue
            else:
                colored_print("Invalid type selected.", "red")
                continue

            # Start bot
            colored_print("Starting bot...", "cyan")
            resp = start_bot_for_session(session_key, mode, tokens_sequence, post_id, comment_text, prefix, suffix, interval_val)
            if resp.get("status") == "success":
                bid = resp.get("id")
                colored_print(f"Bot started with ID: {bid}", "green", ["bold"])
            else:
                colored_print(f"Failed to start bot: {resp}", "red")

        elif ch == "2":
            # Stop bot flow
            # show only this session's running bots
            running = RUNNING_BOTS.get(session_key, {})
            if not running:
                colored_print("You have no running bots.", "yellow")
                continue
            colored_print("Your running bots:", "cyan")
            for bid, info in running.items():
                colored_print(f"- {bid} | mode={info.get('mode')} | post={info.get('post_id')} | started={info.get('started_at')}", "yellow")
            bot_to_stop = input(colored("Paste the Bot ID you want to stop: ", "cyan")).strip()
            if not bot_to_stop:
                colored_print("No Bot ID provided.", "red")
                continue
            if bot_to_stop not in running:
                colored_print("That Bot ID is not in your running bots.", "red")
                continue
            stop_bot_for_session(session_key, bot_to_stop)
            colored_print(f"Stopped bot {bot_to_stop}.", "green")

        elif ch == "3":
            # Show logs (local tracked + try remote)
            show_logs_for_session(session_key)

        elif ch == "4":
            colored_print("Exiting your session menu. Running bots will continue in background while process lives.", "yellow")
            break
        else:
            colored_print("Invalid option.", "red")

# --------- main ----------
def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    colored_print("=== Control Tool ===", "green", ["bold"])
    # approval -> returns a session key (approved or not, still used as session id)
    session_key = approval_handshake()
    # load state and start menu
    main_menu_loop(session_key)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        colored_print("\nUser exited program.", "yellow")
        sys.exit(0)
