# Goal #13

**Automated Git Auto-Push Goal**

## Iteration 86 — 2026-06-07T12:45:29.831917

**Next concrete step – Set up a Python script that monitors a target directory for changes and automatically commits + pushes to a remote repository.**

1. **Create a virtual environment** on the Pi (`python3 -m venv ~/git-auto-push/venv`).
2. **Install required packages**:  
   ```bash
   source ~/git-auto-push/venv/bin/activate
   pip install watchdog GitPython
   ```
3. **Write `auto_push.py`** (sketch below) that:
   - Uses `watchdog.observers.Observer` to watch the repo folder.
   - On any file system event, runs:
     ```python
     repo = git.Repo(REPO_PATH)
     repo.git.add(A=True)               # stage all changes
     if repo.is_dirty(untracked_files=True):
         repo.index.commit("Auto‑commit: " + datetime.now().isoformat())
         origin = repo.remote(name='origin')
         origin.push()
     ```
   - Debounce rapid events (e.g., 5‑second timer) to avoid excessive commits.

4. **Make the script executable** and test it manually:
   ```bash
   python auto_push.py /home/pi/myproject
   ```

5. **Add a systemd service** to run the script at boot, ensuring continuous auto‑push.

Implement the script file now; once it runs and pushes changes, move to scheduling/persistence.

## Iteration 87 — 2026-06-07T13:00:41.464474

Here's the code for the `auto_push.py` script:

```python
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AutoPushHandler(FileSystemEventHandler):
    def __init__(self, remote_repo, local_dir):
        self.remote_repo = remote_repo
        self.local_dir = local_dir
        self.commit_message = ""

    def on_created(self, event):
        if os.path.getsize(event.src_path) > 0:
            # Create a new commit with the current date and time
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.commit_message = f"Commit: {timestamp} - {os.path.basename(event.src_path)}"
            print(self.commit_message)

    def on_deleted(self, event):
        # Don't commit changes when files are deleted
        pass

    def on_moved(self, event):
        if os.path.getsize(event.src_path) > 0:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.commit_message = f"Commit: {timestamp} - {os.path.basename(event.src_path)}"
            print(self.commit_message)

def main():
    remote_repo = "https://example.com/remote-repo.git"
    local_dir = "/path/to/local/directory"

    handler = AutoPushHandler(remote_repo, local_dir)
    observer = Observer()
