import os
import json
from pathlib import Path
from datetime import datetime
import boto3  # AWS S3 as default

BUCKET_NAME = "marina-backups"
REGION = "us-east-1"
LOCAL_MEMORY_PATH = Path("~/Marina/brain/memory").expanduser()

s3 = boto3.client("s3")

def upload_memory_to_cloud(filename: str):
    filepath = LOCAL_MEMORY_PATH / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Memory file {filename} does not exist.")

    with open(filepath, "rb") as f:
        s3.upload_fileobj(f, BUCKET_NAME, f"memory_snapshots/{filename}")
    return f"Uploaded {filename} to S3 bucket {BUCKET_NAME}."

def backup_latest():
    latest_path = LOCAL_MEMORY_PATH / "latest.json"
    if not latest_path.exists():
        return "No latest.json file found."
    return upload_memory_to_cloud("latest.json")


def list_remote_snapshots():
    objects = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="memory_snapshots/")
    return [obj["Key"] for obj in objects.get("Contents", [])]
