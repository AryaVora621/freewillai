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
