#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import base64
import hashlib
import getpass
from termcolor import colored

# ======= CONFIG =======
ENC_FILE = "control.py.enc"

PASSWORD_HASH = "1ddaada48e4e43ecf8f4965ba890b225a44fa36a2a403802cd5993f806b141eb"
MAX_ATTEMPTS = 3
# ======================

def check_password(user_input: str) -> bool:
    return hashlib.sha256(user_input.encode("utf-8")).hexdigest() == PASSWORD_HASH

def secure_input(prompt: str) -> str:
    """
    Try getpass.getpass() first. If that fails to hide input (some envs),
    fallback to platform-specific no-echo reads.
    """
    try:
        # Standard approach (hides input in normal terminals)
        return getpass.getpass(prompt=prompt)
    except Exception:
        pass

    # Fallbacks:
    if os.name == "nt":
        # Windows fallback using msvcrt (no echo)
        import msvcrt
        sys.stdout.write(prompt)
        sys.stdout.flush()
        buf = ""
        while True:
            ch = msvcrt.getwch()  # wide char
            if ch in ("\r", "\n"):
                sys.stdout.write("\n")
                return buf
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch == "\x08":  # backspace
                if len(buf) > 0:
                    buf = buf[:-1]
                    # erase last char from console
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            buf += ch
    else:
        # Unix fallback using termios/tty (disable echo)
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            tty.setraw(fd)
            buf = ""
            while True:
                ch = sys.stdin.read(1)
                if ch in ("\r", "\n"):
                    sys.stdout.write("\n")
                    return buf
                if ch == "\x03":
                    raise KeyboardInterrupt
                if ch == "\x7f":  # backspace
                    if len(buf) > 0:
                        buf = buf[:-1]
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                    continue
                buf += ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def launch_encoded_script():
    try:
        if os.path.exists(ENC_FILE):
            with open(ENC_FILE, "rb") as f:
                encoded_content = f.read()
            decoded_bytes = base64.b64decode(encoded_content)
            # Execute decoded script in a fresh global context
            exec(compile(decoded_bytes.decode("utf-8"), ENC_FILE, "exec"), {})
        else:
            print(colored(f"{ENC_FILE} not found!", "red", ["bold"]))
    except Exception as e:
        print(colored(f"Error running control script: {e}", "red", ["bold"]))

def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(colored("=== Welcome to Control Script Launcher ===", "cyan", ["bold"]))

    attempts = 0
    while attempts < MAX_ATTEMPTS:
        try:
            user_input = secure_input(colored("Enter password to start: ", "yellow"))
        except KeyboardInterrupt:
            print()
            print(colored("Aborted by user.", "red"))
            sys.exit(1)

        if check_password(user_input):
            print(colored("Password correct! Launching the control script...", "green", ["bold"]))
            launch_encoded_script()
            return
        else:
            attempts += 1
            print(colored(f"Incorrect password ({attempts}/{MAX_ATTEMPTS})", "red"))

    print(colored("Max attempts reached. Exiting.", "red", ["bold"]))
    sys.exit(1)

if __name__ == "__main__":
    main()
