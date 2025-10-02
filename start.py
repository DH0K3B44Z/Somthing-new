#!/usr/bin/env python3
import subprocess
import sys
import os

# Config
ENC_FILE = "control.py.enc"
PASSWORD = "1920"

# Check if file exists
if not os.path.isfile(ENC_FILE):
    print(f"Error: {ENC_FILE} not found!")
    sys.exit(1)

# Construct OpenSSL decrypt command
cmd = [
    "openssl",
    "enc",
    "-d",
    "-aes-256-cbc",
    "-pbkdf2",
    "-in", ENC_FILE,
    "-pass", f"pass:{PASSWORD}"
]

try:
    # Run OpenSSL and pipe output to Python interpreter
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    python_proc = subprocess.Popen([sys.executable, "-"], stdin=proc.stdout)
    proc.stdout.close()  # Allow proc to receive SIGPIPE if python_proc exits
    python_proc.communicate()
except FileNotFoundError:
    print("Error: OpenSSL not found. Please install OpenSSL and ensure it's in PATH.")
    sys.exit(1)
