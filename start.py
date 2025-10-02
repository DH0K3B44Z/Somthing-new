#!/usr/bin/env bash
set -euo pipefail

# Improved, safer decrypt-and-run for control.py.enc
# - Prompts for password (silent)
# - Uses a secure temp file
# - Passes the password to openssl via a file descriptor (avoids showing in ps)
# - Uses pbkdf2 and many iterations (recommended)
# - Ensures cleanup of plaintext on any exit (trap)
# - Falls back to best-effort secure deletion

ENC_FILE="control.py.enc"

# checks
command -v openssl >/dev/null 2>&1 || { echo "openssl not found in PATH."; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "python3 not found in PATH."; exit 3; }

if [[ ! -f "$ENC_FILE" ]]; then
  echo "Encrypted file '$ENC_FILE' not found."
  exit 4
fi

# read password silently
read -rsp "Enter decryption password: " PASSWORD
echo

# create tmp file for decrypted script
TMP="$(mktemp /tmp/control.XXXXXX.py)"

# ensure tmp removed on exit (or interruption)
cleanup() {
  local rc=$?
  # attempt to securely erase tmp if it exists
  if [[ -n "${TMP:-}" && -f "$TMP" ]]; then
    if command -v shred >/dev/null 2>&1; then
      shred -u "$TMP" || rm -f "$TMP"
    else
      # overwrite then remove (best-effort)
      printf '%0' > "$TMP" 2>/dev/null || true
      rm -f "$TMP" || true
    fi
  fi
  # clear PASSWORD from memory (best-effort)
  PASSWORD=""
  exit $rc
}
trap cleanup EXIT INT TERM

# decrypt using fd:3 to avoid exposing password on ps args
if ! openssl enc -aes-256-cbc -d -pbkdf2 -iter 100000 -in "$ENC_FILE" -out "$TMP" -pass fd:3 3<<<"$PASSWORD"; then
  echo "Decryption failed. Please check the password or the encrypted file."
  exit 5
fi

echo "Decryption successful — running decrypted script..."
# run the Python script (forward any args)
python3 "$TMP" "$@"
