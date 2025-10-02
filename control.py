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

# Store only the SHA-256 of the password (no plaintext password here).
# This value is the SHA-256 digest of your password (e.g. DH0K3B44Z).
PASSWORD_HASH = "1ddaada48e4e43ecf8f4965ba890b225a44fa36a2a403802cd5993f806b141eb"

# Optional: limit attempts
MAX_ATTEMPTS = 3
# ======================

def check_password(user_input: str) -> bool:
    """Hash the user input and compare to stored hash."""
    h = hashlib.sha256(user_input.encode("utf-8")).hexdigest()
    return h == PASSWORD_HASH

def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(colored("=== Welcome to Control Script Launcher ===", "cyan", ["bold"]))
    attempts = 0

    while attempts < MAX_ATTEMPTS:
        # getpass hides the input on the terminal
        user_input = getpass.getpass(prompt=colored("Enter password to start: ", "yellow"))
        if check_password(user_input):
            print(colored("Password correct! Launching the control script...", "green", ["bold"]))
            # Execute Base64 encoded script
            try:
                if os.path.exists(ENC_FILE):
                    with open(ENC_FILE, "rb") as f:
                        encoded_content = f.read()
                    decoded_bytes = base64.b64decode(encoded_content)
                    # Execute decoded script in a fresh globals dict
                    exec(compile(decoded_bytes.decode("utf-8"), ENC_FILE, "exec"), {})
                else:
                    print(colored(f"{ENC_FILE} not found!", "red", ["bold"]))
                return
            except Exception as e:
                print(colored(f"Error running control script: {e}", "red", ["bold"]))
                return
        else:
            attempts += 1
            print(colored(f"Incorrect password ({attempts}/{MAX_ATTEMPTS})", "red"))
    print(colored("Max attempts reached. Exiting.", "red", ["bold"]))
    sys.exit(1)

if __name__ == "__main__":
    main()
