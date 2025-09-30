import time
import random
import requests
from google.cloud import firestore

# Mozilla User Agents list sample
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    'Mozilla/5.0 (X11; Linux x86_64)...',
    # Add many user agents here
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def send_comment(token, post_id, message):
    url = f"https://graph.facebook.com/{post_id}/comments"
    headers = {'User-Agent': get_random_user_agent()}
    params = {'access_token': token, 'message': message}
    response = requests.post(url, params=params, headers=headers)
    return response

def firebase_init():
    try:
        db = firestore.Client()
        return db
    except Exception as e:
        print("Firestore init failed:", e)
        return None

def process_comments(db):
    while True:
        input_docs = db.collection("input_data").where("status", "==", "started").stream()
        for doc in input_docs:
            data = doc.to_dict()
            username = data['username']
            tokens = data.get('tokens', [])
            comments = data.get('comments', [])
            post_id = data.get('post_id', '')
            prefix = data.get('prefix', '')
            suffix = data.get('suffix', '')
            time_interval = data.get('time_interval', 60)
            status = data.get('status', '')

            stop_post_id = data.get('stop_post_id', None)
            if status == 'stopped' and stop_post_id == post_id:
                # Stop comment process for this post
                print(f"Bot stopped for user {username} on post {post_id}")
                db.collection("input_data").document(username).update({"status": "idle"})
                continue

            for token in tokens:
                for comment in comments:
                    full_comment = f"{prefix}{comment}{suffix}"
                    response = send_comment(token, post_id, full_comment)
                    if response.status_code == 200:
                        print(f"Comment sent for {username}: {full_comment}")
                    else:
                        print(f"Failed for {username} token: {token} response: {response.text}")
                    time.sleep(time_interval + random.randint(5,15))
        time.sleep(30)

def main():
    db = firebase_init()
    if not db:
        print("Exiting, no firestore connection.")
        return

    process_comments(db)

if __name__ == "__main__":
    main()
