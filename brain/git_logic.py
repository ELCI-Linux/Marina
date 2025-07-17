import os
import subprocess
import time
from datetime import datetime, timedelta

class GitLogic:
    def __init__(self, repo_path, remote_name="origin", branch="main", commit_cooldown_sec=300):
        """
        :param repo_path: Path to the local git repository
        :param remote_name: Remote to push to (default: origin)
        :param branch: Branch to commit and push to (default: main)
        :param commit_cooldown_sec: Minimum seconds between commits to avoid spamming
        """
        self.repo_path = os.path.abspath(repo_path)
        self.remote_name = remote_name
        self.branch = branch
        self.commit_cooldown_sec = commit_cooldown_sec
        self.last_commit_time = None

    def _run_git(self, args, capture_output=True):
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=capture_output,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: git {' '.join(args)}\nError: {e.stderr.strip()}")

    def has_uncommitted_changes(self):
        status = self._run_git(["status", "--porcelain"])
        return bool(status)

    def get_last_commit_time(self):
        try:
            timestamp = self._run_git(["log", "-1", "--format=%ct"])
            return datetime.fromtimestamp(int(timestamp))
        except Exception:
            return None

    def should_commit(self):
        if not self.has_uncommitted_changes():
            return False

        last_commit = self.get_last_commit_time()
        if last_commit is None:
            return True  # No commits yet

        now = datetime.now()
        if (now - last_commit) < timedelta(seconds=self.commit_cooldown_sec):
            # Too soon to commit again
            return False

        return True

    def stage_all(self):
        self._run_git(["add", "--all"])

    def commit(self, message=None):
        if message is None:
            message = f"Auto-commit by Marina at {datetime.now().isoformat()}"

        self.stage_all()
        try:
            self._run_git(["commit", "-m", message])
            self.last_commit_time = datetime.now()
            return True
        except RuntimeError as e:
            # Usually means nothing to commit
            if "nothing to commit" in str(e).lower():
                return False
            else:
                raise e

    def push(self):
        try:
            self._run_git(["push", self.remote_name, self.branch])
            return True
        except RuntimeError as e:
            # Handle errors such as auth failure, network errors, or diverged branches
            print(f"[git_logic] Push failed: {e}")
            return False

    def auto_commit_and_push(self, message=None):
        if not self.should_commit():
            print("[git_logic] No changes or commit cooldown active; skipping commit.")
            return False

        committed = self.commit(message)
        if not committed:
            print("[git_logic] Commit not needed or failed.")
            return False

        pushed = self.push()
        if not pushed:
            print("[git_logic] Push failed.")
            return False

        print("[git_logic] Commit and push successful.")
        return True
