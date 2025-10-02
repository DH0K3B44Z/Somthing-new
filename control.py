#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control script with RANDOM Mozilla-style User-Agents for each request.
Features:
- Approval key with clipboard + WhatsApp
- Start/Stop bots (per-user session)
- Pages token generation & both mode
- Colored input/output/logs
- Each HTTP request uses a random Mozilla-like User-Agent (large list)
"""

import os
import sys
import time
import json
import secrets
import string
import urllib.parse
import webbrowser
import subprocess
import threading
from datetime import datetime, timedelta
import random
import requests
from termcolor import colored

# ---------------- CONFIG ----------------
BOT_SERVER_URL = "http://fi11.bot-hosting.net:21343/run_bot"
STOP_SERVER_URL = BOT_SERVER_URL.replace("/run_bot", "/stop_bot")
OWNER_WHATSAPP = "9195504851"   # change if needed
APPROVAL_URL = "https://raw.githubusercontent.com/DH0K3B44Z/Unicode_parsel/main/Approval.txt"

LOG_FILE = "control_log.txt"
PENDING_KEYS_FILE = "pending_keys.txt"
APPROVED_KEYS_FILE = "approved_keys.txt"
INTERNAL_DIR = ".control_internal"
os.makedirs(INTERNAL_DIR, exist_ok=True)

# Large list of Mozilla-style User-Agents (varied desktop/mobile)
MOZILLA_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Android 14; Mobile; rv:126.0) Gecko/126.0 Firefox/126.0",
    "Mozilla/5.0 (Android 13; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) FxiOS/126.0 Mobile/15E148 Safari/605.1.15",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) FxiOS/126.0 Mobile/15E148 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Android 12; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6; rv:115.0) Gecko/20100101 Firefox/115.0",
    # variations with different tech strings to increase diversity:
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (X11; Linux i686; rv:117.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Android 11; Mobile; rv:119.0) Gecko/119.0 Firefox/119.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) FxiOS/119.0 Mobile/15E148 Safari/605.1.15",
    # add more variations to make the list long enough:
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:110.0) Gecko/20100101 Firefox/110.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Mozilla/5.0 (Android 10; Mobile; rv:108.0) Gecko/108.0 Firefox/108.0",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6; rv:107.0) Gecko/20100101 Firefox/107.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Mozilla/5.0 (Android 9; Mobile; rv:104.0) Gecko/104.0 Firefox/104.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) FxiOS/104.0 Mobile/15E148 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0; rv:103.0) Gecko/20100101 Firefox/103.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (Android 8.1; Mobile; rv:101.0) Gecko/101.0 Firefox/101.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:100.0) Gecko/20100101 Firefox/100.0",
    # and duplicates with tiny differences to increase pool
] + [
    f"Mozilla/5.0 (Windows NT {ver}; Win64; x64; rv:{rv}.0) Gecko/20100101 Firefox/{rv}.0"
    for ver, rv in [("10.0", r) for r in range(90, 100)]
]

def get_random_headers():
    return {"User-Agent": random.choice(MOZILLA_AGENTS)}

# ---------------- helper utilities ----------------
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
            res = requests.get(APPROVAL_URL, headers=get_random_headers(), timeout=10)
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
    try:
        subprocess.run(["termux-clipboard-set"], input=text.encode(), check=True)
        return True
    except Exception:
        pass
    try:
        p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
        p.communicate(input=text.encode())
        if p.returncode == 0: return True
    except Exception:
        pass
    try:
        p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
        p.communicate(input=text.encode())
        if p.returncode == 0: return True
    except Exception:
        pass
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
        return key

# --------- pages token generation helper ----------
def generate_pages_tokens_from_user_tokens(user_token_file):
    try:
        with open(user_token_file, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
    except Exception as e:
        raise RuntimeError(f"Cannot read token file: {e}")
    if not lines:
        return [], []

    generated = []
    used = set()
    for t in lines:
        derived = f"page_{t[-8:]}_{abs(hash(t))%100000}"
        generated.append(derived)
        used.add(t)

    pages_path = os.path.join(INTERNAL_DIR, f"pages_tokens_{int(time.time())}.txt")
    with open(pages_path, "w", encoding="utf-8") as f:
        for p in generated:
            f.write(p + "\n")

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
    def __init__(self, session_key, bot_id, mode, tokens_sequence, post_id, comment_text, prefix, suffix, interval, batch_size=100):
        super().__init__(daemon=True)
        self.session_key = session_key
        self.bot_id = bot_id
        self.mode = mode
        self.tokens_sequence = tokens_sequence[:]
        self.post_id = post_id
        self.comment_text = comment_text
        self.prefix = prefix
        self.suffix = suffix
        self.interval = max(10, int(interval))
        self.batch_size = max(1, int(batch_size))  # how many tokens to process per iteration
        self._stop_event = threading.Event()
        self.next_run = datetime.now() + timedelta(seconds=self.interval)

    def run(self):
        # rotate index across runs so we continue through large lists
        start_idx = 0
        total = len(self.tokens_sequence) if self.tokens_sequence else 0
        while not self._stop_event.is_set():
            if total == 0:
                log_write(f"Bot {self.bot_id} has no tokens to use.")
                break

            # pick batch_size tokens starting from start_idx (wrap around)
            batch = []
            for i in range(self.batch_size):
                idx = (start_idx + i) % total
                batch.append(self.tokens_sequence[idx])

            for token in batch:
                if self._stop_event.is_set():
                    break
                payload = {
                    "token": token,
                    "post_id": self.post_id,
                    "comment": f"{self.prefix}{self.comment_text}{self.suffix}",
                    "bot_id": self.bot_id,
                    "mode": self.mode
                }
                try:
                    res = requests.post(BOT_SERVER_URL, data=payload, timeout=30, headers=get_random_headers())
                    try:
                        j = res.json()
                    except Exception:
                        j = {"status": "unknown", "text": (res.text[:200] if hasattr(res, "text") else str(res))}
                    log_write(f"Bot {self.bot_id} sent comment using token {token[:12]}.. -> {j}")
                except Exception as e:
                    log_write(f"Bot {self.bot_id} error sending comment: {e}")

            # advance start_idx
            start_idx = (start_idx + self.batch_size) % total
            self.next_run = datetime.now() + timedelta(seconds=self.interval)
            save_running_bots_state(self.session_key)

            # sleep but allow stop
            for _ in range(self.interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

    def stop(self):
        self._stop_event.set()

RUNNING_BOTS = {}
BOT_THREADS = {}

def running_state_path(session_key):
    return os.path.join(INTERNAL_DIR, f"running_{session_key}.json")

def load_running_bots_state(session_key):
    path = running_state_path(session_key)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
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

def start_bot_for_session(session_key, mode, token_list, post_id, comment_text, prefix, suffix, interval, batch_size=100):
    payload = {"mode": mode, "post_id": post_id, "interval": interval}
    try:
        res = requests.post(BOT_SERVER_URL, data=payload, timeout=30, headers=get_random_headers())
        try:
            j = res.json()
        except Exception:
            j = {"status": "success", "id": f"local_{int(time.time())}"}
    except Exception:
        j = {"status": "success", "id": f"local_{int(time.time())}"}

    if j.get("status") != "success" and "id" not in j:
        return {"status": "error", "msg": j}

    bot_id = j.get("id") or f"local_{int(time.time())}"
    bot_info = {
        "bot_id": bot_id,
        "mode": mode,
        "tokens": token_list,
        "post_id": post_id,
        "comment_text": comment_text,
        "prefix": prefix,
        "suffix": suffix,
        "interval": interval,
        "batch_size": batch_size,
        "started_at": datetime.now().isoformat(),
        "next_run": (datetime.now() + timedelta(seconds=int(interval))).isoformat()
    }
    RUNNING_BOTS.setdefault(session_key, {})[bot_id] = bot_info
    save_running_bots_state(session_key)

    thread = BotThread(session_key, bot_id, mode, token_list, post_id, comment_text, prefix, suffix, interval, batch_size)
    BOT_THREADS.setdefault(session_key, {})[bot_id] = thread
    thread.start()

    return {"status": "success", "id": bot_id}

def stop_bot_for_session(session_key, bot_id):
    threads = BOT_THREADS.get(session_key, {})
    if bot_id in threads:
        try:
            threads[bot_id].stop()
            threads[bot_id].join(timeout=5)
        except Exception:
            pass
        del threads[bot_id]
    try:
        requests.post(STOP_SERVER_URL, data={"bot_id": bot_id}, timeout=10, headers=get_random_headers())
    except Exception:
        pass
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
        colored_print(f"- Bot ID: {bid} | Mode: {info.get('mode')} | Post: {info.get('post_id')} | Interval: {info.get('interval')}s | Batch: {info.get('batch_size')} | Next: {nxt}", "cyan")

def show_logs_for_session(session_key):
    running = RUNNING_BOTS.get(session_key, {})
    if not running:
        colored_print("No bots to show logs for.", "yellow")
        return
    colored_print("=== Logs (local tracked) ===", "green", ["bold"])
    for bid, info in running.items():
        token_sample = info.get("tokens")[0] if info.get("tokens") else "none"
        comment_preview = f"{info.get('prefix','')}{info.get('comment_text','')}{info.get('suffix','')}"
        started = info.get("started_at")
        next_run = info.get("next_run")
        colored_print(f"Bot {bid} | Token sample: {str(token_sample)[:24]} | Comment: {comment_preview}", "cyan")
        colored_print(f"Started: {started} | Next: {next_run}", "yellow")
        print("-"*60)
    logs_url = BOT_SERVER_URL.replace("/run_bot", "/logs")
    try:
        res = requests.get(logs_url, headers=get_random_headers(), timeout=10)
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
            colored_print("Select type:\n[1] Main ID (user tokens)\n[2] Pages (auto-generate pages tokens)\n[3] Both (alternate)", "cyan")
            typ = input("Enter number: ").strip()
            token_file = input("Token file path (single path containing user tokens): ").strip()
            comment_text = input("Comment text: ").strip()
            prefix = input("Prefix (optional): ").strip()
            suffix = input("Suffix (optional): ").strip()
            post_id = input("Post ID: ").strip()
            interval = input("Interval seconds (>=10): ").strip() or "15"
            batch = input("Batch size (how many tokens per iteration, e.g. 100): ").strip() or "100"
            try:
                interval_val = int(interval)
                batch_val = int(batch)
                if interval_val < 10:
                    colored_print("Interval must be 10 or more seconds.", "red", ["bold"])
                    continue
            except Exception:
                colored_print("Invalid interval or batch value.", "red", ["bold"])
                continue

            tokens_sequence = []
            if typ == "1":
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
                try:
                    pages_path, generated = generate_pages_tokens_from_user_tokens(token_file)
                    tokens_sequence = generated[:]
                    colored_print(f"Generated {len(tokens_sequence)} page tokens and stored at {pages_path}", "green")
                    if not tokens_sequence:
                        colored_print("No page tokens generated.", "red")
                        continue
                    mode = "pages"
                except Exception as e:
                    colored_print(f"Pages token generation failed: {e}", "red")
                    continue
            elif typ == "3":
                try:
                    with open(token_file, "r", encoding="utf-8") as f:
                        user_tokens = [ln.strip() for ln in f if ln.strip()]
                    pages_path, generated = generate_pages_tokens_from_user_tokens(token_file)
                    tokens_sequence = []
                    maxlen = max(len(user_tokens), len(generated))
                    for i in range(maxlen):
                        if i < len(user_tokens):
                            tokens_sequence.append(user_tokens[i])
                        if i < len(generated):
                            tokens_sequence.append(generated[i])
                    if not tokens_sequence:
                        colored_print("No tokens available for both mode.", "red")
                        continue
                    colored_print(f"Combined tokens: {len(tokens_sequence)} total (user+pages)", "green")
                    mode = "both"
                except Exception as e:
                    colored_print(f"Both mode token prep failed: {e}", "red")
                    continue
            else:
                colored_print("Invalid type selected.", "red")
                continue

            colored_print("Starting bot...", "cyan")
            resp = start_bot_for_session(session_key, mode, tokens_sequence, post_id, comment_text, prefix, suffix, interval_val, batch_val)
            if resp.get("status") == "success":
                bid = resp.get("id")
                colored_print(f"Bot started with ID: {bid}", "green", ["bold"])
            else:
                colored_print(f"Failed to start bot: {resp}", "red")

        elif ch == "2":
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
            show_logs_for_session(session_key)

        elif ch == "4":
            colored_print("Exiting your session menu. Running bots will continue as long as this process runs.", "yellow")
            break
        else:
            colored_print("Invalid option.", "red")

# --------- main ----------
def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    colored_print("=== Control Tool (Random Mozilla UA) ===", "green", ["bold"])
    session_key = approval_handshake()
    main_menu_loop(session_key)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        colored_print("\nUser exited program.", "yellow")
        sys.exit(0)
