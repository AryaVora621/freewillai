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
# STATUS: complete