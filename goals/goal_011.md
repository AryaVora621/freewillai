# Goal #11

1. **Automated Git Auto-Push**: Write a Python script that uses the `git` command to automatically push changes from the current directory to GitHub after each autonomous commit on the Raspberry Pi.

## Iteration 65 — 2026-06-07T03:11:53.399409

import subprocess
import os

def git_push():
    local_dir = os.getcwd()
    remote_url = "https://github.com/your-username/your-repo-name.git"
    try:
        subprocess.run(f"git -C {local_dir} push --mirror {remote_url}", shell=True)
        print("Push successful")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    git_push()

## Iteration 66 — 2026-06-07T03:25:52.992833

# Goal: Automated Git Auto-Push on Raspberry Pi
import subprocess
import os

def git_push():
    local_dir = os.getcwd()
    remote_url = "https://github.com/your-username/your-repo-name.git"
    try:
        subprocess.run(f"git -C {local_dir} push --mirror {remote_url}", shell=True)
        print("Push successful")
    except Exception as e:
        print(f"Error: {e}")

def main():
    git_push()

if __name__ == "__main__":
    main()

## Iteration 67 — 2026-06-07T03:39:34.125728

# Automated Git Auto-Push on Raspberry Pi
import subprocess
import os

def git_push():
    local_dir = os.getcwd()
    remote_url = "https://github.com/your-username/your-repo-name.git"
    try:
        subprocess.run(f"git -C {local_dir} push --mirror {remote_url}", shell=True)
        print("Push successful")
    except Exception as e:
        print(f"Error: {e}")

def main():
    while True:
        git_push()
        input("Press enter to continue...")

if __name__ == "__main__":
    main()

## Iteration 68 — 2026-06-07T03:53:45.266994

# Goal: Automated Git Auto-Push on Raspberry Pi after each commit
import os, subprocess, time

def git_push():
    repo_dir = os.getcwd()
    try:
        # ensure there are commits to push
        result = subprocess.run(
            ["git", "-C", repo_dir, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        branch = result.stdout.strip()
        subprocess.run(
            ["git", "-C", repo_dir, "push", "origin", branch],
            check=True
        )
        print(f"Pushed branch {branch} successfully")
    except subprocess.CalledProcessError as e:
        print("Git push failed:", e)

def monitor_and_push(poll_interval=30):
    repo_dir = os.getcwd()
    while True:
        # check if there are unpushed commits
        try:
            out = subprocess.run(
                ["git", "-C", repo_dir, "log", "@{u}.."],
                capture_output=True, text=True, check=False
            )
            if out.stdout:
                git_push()
        except Exception as e:
            print("Error checking repo:", e)
        time.sleep(poll_interval)

if __name__ == "__main__":
    monitor_and_push()
#
