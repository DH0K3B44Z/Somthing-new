# client.py
import requests
import random
import time

API_URL = 'http://127.0.0.1:5000'  # change to server IP/domain

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
]

def print_green(text):
    print(f"\u001B[1;32m{text}\u001B[0m")

def print_red(text):
    print(f"\u001B[1;31m{text}\u001B[0m")

def send_request(endpoint, api_key=None, data=None, method="GET"):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    if api_key:
        headers["X-API-KEY"] = api_key
    url = f"{API_URL}/{endpoint}"
    try:
        if method.upper() == "POST":
            resp = requests.post(url, json=data, headers=headers)
        else:
            resp = requests.get(url, headers=headers, params=data)
        return resp
    except Exception as e:
        print_red(f"Request to {endpoint} failed: {e}")
        return None

def register_user(username):
    resp = send_request("register", data={"username": username}, method="POST")
    if resp and resp.status_code in (200,201):
        api_key = resp.json().get("api_key")
        print_green(f"Registered. API key: {api_key}")
        return api_key
    else:
        print_red(f"Failed to register: {resp.text if resp else 'No response'}")
        return None

def update_bot_data(api_key, data):
    resp = send_request("update", api_key=api_key, data=data, method="POST")
    if resp and resp.status_code == 200:
        print_green("Bot data updated successfully.")
    else:
        print_red(f"Failed to update data: {resp.text if resp else 'No response'}")

def start_bot(api_key):
    resp = send_request("start", api_key=api_key, method="POST")
    if resp and resp.status_code == 200:
        print_green("Bot started.")
    else:
        print_red(f"Failed to start bot: {resp.text if resp else 'No response'}")

def stop_bot(api_key):
    resp = send_request("stop", api_key=api_key, method="POST")
    if resp and resp.status_code == 200:
        print_green("Bot stopped.")
    else:
        print_red(f"Failed to stop bot: {resp.text if resp else 'No response'}")

def get_status(api_key):
    resp = send_request("status", api_key=api_key)
    if resp and resp.status_code == 200:
        print_green(f"Bot status: {resp.json()}")
    else:
        print_red(f"Failed to get status: {resp.text if resp else 'No response'}")

if __name__ == "__main__":
    # Example flow:
    username = "user1"
    api_key = register_user(username)   # get unique key for this user
    if not api_key:
        exit(1)

    data = {
        "username": username,
        "tokens": ["token1", "token2"],
        "comments": ["Hello from control!"],
        "post_id": "123456789",
        "prefix": "[PREFIX] ",
        "suffix": " [SUFFIX]",
        "interval": 10
    }

    update_bot_data(api_key, data)
    start_bot(api_key)
    time.sleep(15)
    get_status(api_key)
    stop_bot(api_key)
