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