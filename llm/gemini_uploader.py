import os
import requests
import json

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
UPLOAD_URL = f"https://generativelanguage.googleapis.com/upload/v1beta/files?uploadType=multipart&key={GEMINI_API_KEY}"
GENERATION_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-pro:generateContent?key={GEMINI_API_KEY}"

def upload_file(file_path, mime_type="application/pdf"):
    try:
        with open(file_path, "rb") as f:
            files = {
                "metadata": ("metadata", json.dumps({
                    "file": {"displayName": os.path.basename(file_path)}
                }), "application/json"),
                "file": (os.path.basename(file_path), f, mime_type)
            }
            response = requests.post(UPLOAD_URL, files=files)
            response.raise_for_status()
            file_resource_name = response.json().get("name")
            print(f"[GEMINI] File uploaded as: {file_resource_name}")
            return file_resource_name
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        return None

def send_with_file(prompt_text, file_resource_name, mime_type="application/pdf"):
    try:
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "fileData": {
                                "mimeType": mime_type,
                                "fileUri": file_resource_name
                            }
                        }
                    ]
                },
                {
                    "parts": [{"text": prompt_text}]
                }
            ]
        }
        response = requests.post(GENERATION_URL, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()["candidates"][0]["content"]
        return content.strip()
    except Exception as e:
        return f"[ERROR] File-based prompt failed: {e}"

def list_uploaded_files():
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/files?key={GEMINI_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("files", [])
    except Exception as e:
        return f"[ERROR] Failed to list files: {e}"

def delete_file(file_resource_name):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/files/{file_resource_name}?key={GEMINI_API_KEY}"
        response = requests.delete(url)
        response.raise_for_status()
        return f"[GEMINI] File {file_resource_name} deleted successfully."
    except Exception as e:
        return f"[ERROR] Failed to delete file: {e}"

if __name__ == "__main__":
    # Example usage
    file_path = "sample.pdf"
    prompt = "Summarise the uploaded PDF."
    resource = upload_file(file_path, mime_type="application/pdf")
    if resource:
        result = send_with_file(prompt, resource)
        print(f"\n[GEMINI RESPONSE]\n{result}")
