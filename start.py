#!/usr/bin/env python3
"""
Simple launcher:
  - expects control.py.enc in current directory
  - uses hard-coded password "DH0K3B44Z"
  - decrypts to a temporary file, runs it with python3, then removes the temp file
Usage:
  python launcher.py [args...]
"""

import os
import sys
import tempfile
import subprocess
import atexit
import shutil

ENC_FILE = "control.py.enc"
PASSWORD = "DH0K3B44Z"   # as requested

def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)

if not os.path.isfile(ENC_FILE):
    die(f"Encrypted file not found: {ENC_FILE}")

if shutil.which("openssl") is None:
    die("openssl not found in PATH. Install openssl and retry.")

# create a portable temporary file path (works on Termux/Android)
fd, tmp_path = tempfile.mkstemp(prefix="control.", suffix=".py")
os.close(fd)

# ensure cleanup on exit
def cleanup():
    try:
        if os.path.exists(tmp_path):
            # prefer shred if available
            if shutil.which("shred"):
                try:
                    subprocess.run(["shred", "-u", tmp_path], check=False)
                    return
                except Exception:
                    pass
            try:
                os.remove(tmp_path)
            except Exception:
                pass
    except Exception:
        pass

atexit.register(cleanup)

# Decrypt using openssl. We give the password on stdin and use -pass fd:0
openssl_cmd = [
    "openssl", "enc", "-aes-256-cbc", "-d",
    "-pbkdf2", "-iter", "100000",
    "-in", ENC_FILE,
    "-out", tmp_path,
    "-pass", "fd:0"
]

print("Decrypting...", flush=True)
proc = subprocess.run(openssl_cmd, input=PASSWORD + "\n", text=True,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if proc.returncode != 0:
    # decryption failed — show stderr for troubleshooting and exit
    stderr = proc.stderr.strip()
    if not stderr:
        stderr = "(no openssl error output)"
    die(f"Decryption failed:\n{stderr}")

print("Decryption successful — running script...", flush=True)

# Run the decrypted script with any args passed to this launcher
try:
    run_cmd = [sys.executable, tmp_path] + sys.argv[1:]
    result = subprocess.run(run_cmd)
    retcode = result.returncode
except KeyboardInterrupt:
    # propagate ctrl-c
    raise
except Exception as e:
    die(f"Failed to run decrypted script: {e}")

# normal exit (cleanup will run via atexit)
sys.exit(retcode)
