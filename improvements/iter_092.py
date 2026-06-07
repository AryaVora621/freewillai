# Auto-generated improvement — Iteration 92
# Suggestion: Use more descriptive variable names instead of `plan` and `repo_path`.

def clone_repo_to_storage(plan, repo_path):
    local_dir = "/home/pi/" + plan
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    remote_url = "https://example.com/repo"
    ssh_command = f"scp {repo_path} {local_dir}"
    subprocess.run(ssh_command, shell=True)
