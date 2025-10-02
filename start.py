#!/usr/bin/env bash
set -euo pipefail

ENC_FILE="control.py.enc"

# checks
command -v openssl >/dev/null 2>&1 || { echo "openssl not found."; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "python3 not found."; exit 3; }

if [[ ! -f "$ENC_FILE" ]]; then
  echo "Encrypted file '$ENC_FILE' not found."
  exit 4
fi

read -rsp "Enter decryption password: " PASSWORD
echo

# create portable temp file using Python's tempfile (works on Termux)
TMP="$(python3 - <<'PY'
import tempfile
f = tempfile.NamedTemporaryFile(prefix="control.", suffix=".py", delete=False)
print(f.name)
f.close()
PY
)"

if [[ -z "${TMP:-}" ]]; then
  echo "Failed to create temp file."
  exit 5
fi

# ensure cleanup
cleanup() {
  rc=$?
  # try secure delete if possible
  if [[ -n "${TMP:-}" && -f "$TMP" ]]; then
    if command -v shred >/dev/null 2>&1; then
      shred -u "$TMP" || rm -f "$TMP"
    else
      rm -f "$TMP" || true
    fi
  fi
  PASSWORD=""
  exit $rc
}
trap cleanup EXIT INT TERM

# decrypt (use fd to avoid showing password in ps)
if ! openssl enc -aes-256-cbc -d -pbkdf2 -iter 100000 -in "$ENC_FILE" -out "$TMP" -pass fd:3 3<<<"$PASSWORD"; then
  echo "Decryption failed. Check password or file."
  exit 6
fi

echo "Decryption OK — running script..."
python3 "$TMP" "$@"
# cleanup runs automatically via trap
