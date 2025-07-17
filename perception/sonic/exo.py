# perception/shazamio_recognition.py

import asyncio
from shazamio import Shazam, exceptions

shazam = Shazam()

async def recognize_song(file_path: str) -> dict:
    """
    Recognize song from audio file using Shazam unofficial API.

    Args:
        file_path (str): Path to the audio file (mp3, wav, etc.)

    Returns:
        dict: Recognition result with metadata or error info
    """
    try:
        result = await shazam.recognize_song(file_path)
        return {
            "success": True,
            "track": result.get("track", {}),
            "raw": result
        }
    except exceptions.ShazamException as e:
        return {"success": False, "error": f"Shazam recognition error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def recognize_song_sync(file_path: str) -> dict:
    """
    Synchronous wrapper for recognize_song async function.

    Args:
        file_path (str): Path to audio file

    Returns:
        dict: Recognition result
    """
    return asyncio.run(recognize_song(file_path))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python shazamio_recognition.py <audio_file>")
        sys.exit(1)

    audio_path = sys.argv[1]
    result = recognize_song_sync(audio_path)

    if result["success"]:
        track = result["track"]
        print(f"Title: {track.get('title')}")
        print(f"Artist: {track.get('subtitle')}")
        print(f"Album: {track.get('sections', [{}])[0].get('metadata', [{}])[0].get('text')}")
    else:
        print("Recognition failed:", result["error"])
