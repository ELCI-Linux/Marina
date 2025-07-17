import os
import time
from datetime import datetime, timedelta

class CloudLogic:
    def __init__(self, sync_folder, provider_client, bucket_name,
                 min_sync_interval_sec=600):
        """
        :param sync_folder: Local folder path to sync/upload
        :param provider_client: Cloud SDK client instance (e.g. boto3 client)
        :param bucket_name: Bucket or container name on cloud provider
        :param min_sync_interval_sec: Minimum seconds between syncs to avoid spamming
        """
        self.sync_folder = os.path.abspath(sync_folder)
        self.client = provider_client
        self.bucket_name = bucket_name
        self.min_sync_interval_sec = min_sync_interval_sec
        self.last_sync_time = None

    def should_sync(self):
        if self.last_sync_time is None:
            return True

        now = datetime.now()
        if (now - self.last_sync_time) > timedelta(seconds=self.min_sync_interval_sec):
            return True

        return False

    def list_local_files(self):
        file_list = []
        for root, _, files in os.walk(self.sync_folder):
            for f in files:
                file_list.append(os.path.join(root, f))
        return file_list

    def upload_file(self, local_path, remote_path):
        """
        Upload a single file to cloud storage.
        Override this method for your specific provider.
        """
        raise NotImplementedError("upload_file() must be implemented by subclass.")

    def sync(self):
        if not self.should_sync():
            print("[cloud_logic] Sync cooldown active; skipping sync.")
            return False

        files = self.list_local_files()
        print(f"[cloud_logic] Syncing {len(files)} files...")

        success = True
        for file_path in files:
            # Compute remote path relative to sync_folder
            relative_path = os.path.relpath(file_path, self.sync_folder)
            try:
                self.upload_file(file_path, relative_path)
            except Exception as e:
                print(f"[cloud_logic] Failed to upload {file_path}: {e}")
                success = False

        if success:
            self.last_sync_time = datetime.now()
            print("[cloud_logic] Sync successful.")
        else:
            print("[cloud_logic] Sync completed with errors.")

        return success
