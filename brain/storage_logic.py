import os
import json
import shutil
from datetime import datetime

class StorageLogic:
    def __init__(self, base_dir):
        """
        :param base_dir: Base directory for storage operations (e.g., project data folder)
        """
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _full_path(self, relative_path):
        return os.path.abspath(os.path.join(self.base_dir, relative_path))

    def read_json(self, relative_path):
        path = self._full_path(relative_path)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_json(self, relative_path, data, backup=True):
        path = self._full_path(relative_path)
        dir_path = os.path.dirname(path)
        os.makedirs(dir_path, exist_ok=True)

        if backup and os.path.exists(path):
            self._backup_file(path)

        temp_path = path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        os.replace(temp_path, path)  # atomic replace

    def read_text(self, relative_path):
        path = self._full_path(relative_path)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def write_text(self, relative_path, text, backup=True):
        path = self._full_path(relative_path)
        dir_path = os.path.dirname(path)
        os.makedirs(dir_path, exist_ok=True)

        if backup and os.path.exists(path):
            self._backup_file(path)

        temp_path = path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(text)

        os.replace(temp_path, path)

    def _backup_file(self, path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{path}.bak_{timestamp}"
        shutil.copy2(path, backup_path)
        print(f"[storage_logic] Backup created: {backup_path}")

    def delete(self, relative_path):
        path = self._full_path(relative_path)
        if os.path.exists(path):
            os.remove(path)

    def exists(self, relative_path):
        path = self._full_path(relative_path)
        return os.path.exists(path)
