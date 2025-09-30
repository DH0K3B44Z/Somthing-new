import os
import subprocess
from getpass import getpass

GITHUB_REPO = "https://github.com/DH0K3B44Z/Somthing-new.git"
LOCAL_REPO = "./Somthing-new-control"

def clone_or_pull_repo():
    if not os.path.exists(LOCAL_REPO):
        subprocess.run(["git", "clone", GITHUB_REPO, LOCAL_REPO])
    else:
        subprocess.run(["git", "-C", LOCAL_REPO, "pull"])

def git_commit_and_push(message):
    subprocess.run(["git", "-C", LOCAL_REPO, "add", "."])
    subprocess.run(["git", "-C", LOCAL_REPO, "commit", "-m", message])
    subprocess.run(["git", "-C", LOCAL_REPO, "push"])

def main():
    clone_or_pull_repo()
    user = input("Enter your user prefix (e.g. user1): ").strip()

    base_path = os.path.join(LOCAL_REPO, "User-data")
    user_tokens = os.path.join(base_path, f"{user}_tokens.txt")
    user_comments = os.path.join(base_path, f"{user}_comments.txt")
    user_config = os.path.join(base_path, f"{user}_config.json")
    user_list_file = os.path.join(base_path, "user-list.json")

    print("Place your token, comments, and config files manually in the following location:")
    print(f"{base_path}")

    input("Press Enter when files are ready...")

    # Update user-list.json
    import json
    if os.path.exists(user_list_file):
        with open(user_list_file, "r") as f:
            user_list = json.load(f)
    else:
        user_list = {"users": []}

    if user not in user_list["users"]:
        user_list["users"].append(user)
        with open(user_list_file, "w") as f:
            json.dump(user_list, f, indent=4)

    # Commit and push changes
    commit_msg = f"Update data for {user}"
    git_commit_and_push(commit_msg)
    print(f"Data for {user} pushed successfully to GitHub repo.")

if __name__ == "__main__":
    main()
