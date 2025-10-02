#!/usr/bin/env python3
# launcher.py
# Simple password-protected Base64 launcher for control.py.enc
# Password (plaintext): DH0K3B44Z  (NOT stored in plain text here)

import os
import sys
import base64
import hashlib
import tempfile

# ---------- obfuscated stored value ----------
# Stored form: base64(sha256(password_hex)) reversed and split into parts.
# (This is just obfuscation so the hash isn't plainly visible)
_OBF_PARTS = [
    "==gYlFDN",
    "xImNwgjZ",
    "zkTO1Q2Y",
    "yADOzADN",
    "hJTY2MTY",
    "mRDNhVjM",
    "yIGM5gTY",
    "iVjN5QjZ",
    "4Y2YlNDN",
    "lRTZ4QTY",
    "kFWYkRWM",
]

ENC_FILE = "control.py.enc"
MAX_ATTEMPTS = 3

def _reconstruct_hash_hex():
    """Reconstruct the stored SHA-256 hex string from obfuscated parts."""
    # join parts, reverse, base64-decode to get original hex string
    joined = "".join(_OBF_PARTS)
    b64 = joined[::-1]
    try:
        decoded = base64.b64decode(b64).decode("utf-8")
    except Exception:
        # if anything goes wrong, fail safe
        return None
    return decoded  # this is the expected sha256 hexdigest (hex-string)

def _check_password(user_input):
    expected_hash = _reconstruct_hash_hex()
    if not expected_hash:
        return False
    # compute sha256 of the provided password and compare
    h = hashlib.sha256(user_input.encode("utf-8")).hexdigest()
    return h == expected_hash

def _secure_input(prompt):
    """Hidden input. Try getpass first, fallback to simple no-echo where possible."""
    try:
        import getpass
        return getpass.getpass(prompt)
    except Exception:
        pass

    if os.name == "nt":
        import msvcrt
        sys.stdout.write(prompt)
        sys.stdout.flush()
        buf = ""
        while True:
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                sys.stdout.write("\n")
                return buf
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch == "\x08":
                if buf:
                    buf = buf[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            buf += ch
    else:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
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
                if ch == "\x7f":
                    if buf:
                        buf = buf[:-1]
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                    continue
                buf += ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

def _run_encoded_script():
    if not os.path.exists(ENC_FILE):
        print(f"[!] {ENC_FILE} not found.")
        return

    with open(ENC_FILE, "rb") as f:
        encoded = f.read()

    try:
        decoded_bytes = base64.b64decode(encoded)
    except Exception as e:
        print(f"[!] Error decoding base64: {e}")
        return

    # Try to decode as utf-8 source and exec; otherwise write temp file and run it
    try:
        src = decoded_bytes.decode("utf-8")
        # execute in isolated namespace
        globs = {"__name__": "__main__"}
        exec(compile(src, ENC_FILE, "exec"), globs)
    except UnicodeDecodeError:
        # binary or non-utf8: write to temp file and run with Python interpreter
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        try:
            tmp.write(decoded_bytes)
            tmp.close()
            # Use same interpreter binary
            os.system(f"{sys.executable} \"{tmp.name}\"")
        finally:
            try:
                os.remove(tmp.name)
            except Exception:
                pass
    except SystemExit:
        # allow script to call sys.exit()
        raise
    except Exception as e:
        print(f"[!] Error running decoded script: {e}")

def main():
    # simple prompt
    attempts = 0
    while attempts < MAX_ATTEMPTS:
        try:
            pwd = _secure_input("Enter password to start: ")
        except KeyboardInterrupt:
            print("\nAborted.")
            return

        if _check_password(pwd):
            print("Password correct. Launching...")
            _run_encoded_script()
            return
        else:
            attempts += 1
            print(f"Incorrect password ({attempts}/{MAX_ATTEMPTS})")
    print("Max attempts reached. Exiting.")

if __name__ == "__main__":
    main()
