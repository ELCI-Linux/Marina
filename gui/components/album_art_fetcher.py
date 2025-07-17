#!/usr/bin/env python3
"""
Album Art Fetcher for Marina
Fetches album artwork for songs using MusicBrainz and Last.fm APIs
"""

import requests
import io
import threading
import time
from typing import Optional, Callable, Tuple
from PIL import Image, ImageTk
import musicbrainzngs
import hashlib
import os
import tempfile

class AlbumArtFetcher:
    def __init__(self, cache_dir: Optional[str] = None):
        # Set up MusicBrainz
        musicbrainzngs.set_useragent("Marina", "1.0", "https://github.com/user/marina")
        
        # Cache directory for downloaded images
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "marina_album_art")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache for images to avoid re-downloading
        self.image_cache = {}
        
        # Thread pool for async fetching
        self.active_requests = {}
        
    def _get_cache_path(self, song_name: str, artist_name: str) -> str:
        """Get cache file path for a song"""
        key = f"{artist_name}_{song_name}".lower()
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hash_key}.jpg")
        
    def _search_musicbrainz(self, song_name: str, artist_name: str) -> Optional[str]:
        """Search MusicBrainz for release information"""
        try:
            # Search for recordings
            result = musicbrainzngs.search_recordings(
                query=f'recording:"{song_name}" AND artist:"{artist_name}"',
                limit=5
            )
            
            if not result.get('recording-list'):
                return None
                
            # Try to find a recording with release information
            for recording in result['recording-list']:
                if 'release-list' in recording:
                    for release in recording['release-list']:
                        release_id = release['id']
                        
                        # Get detailed release information
                        try:
                            release_detail = musicbrainzngs.get_release_by_id(
                                release_id, 
                                includes=['recordings', 'release-groups']
                            )
                            
                            # Check if we have cover art
                            if 'release' in release_detail:
                                return release_id
                                
                        except Exception as e:
                            print(f"Error getting release details: {e}")
                            continue
                            
            return None
            
        except Exception as e:
            print(f"MusicBrainz search error: {e}")
            return None
            
    def _get_coverart_url(self, release_id: str) -> Optional[str]:
        """Get cover art URL from MusicBrainz cover art archive"""
        try:
            # Use Cover Art Archive API
            url = f"https://coverartarchive.org/release/{release_id}/front"
            
            # Check if cover art exists
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                return url
                
        except Exception as e:
            print(f"Cover art URL error: {e}")
            
        return None
        
    def _fetch_lastfm_art(self, song_name: str, artist_name: str) -> Optional[str]:
        """Fallback to Last.fm for album art"""
        try:
            # Last.fm API (no key required for basic info)
            url = "https://ws.audioscrobbler.com/2.0/"
            params = {
                'method': 'track.getInfo',
                'api_key': 'your_api_key_here',  # You'd need to get an API key
                'artist': artist_name,
                'track': song_name,
                'format': 'json'
            }
            
            # For now, skip Last.fm since it requires API key
            return None
            
        except Exception as e:
            print(f"Last.fm search error: {e}")
            return None
            
    def _download_image(self, url: str, cache_path: str) -> Optional[Image.Image]:
        """Download and cache image"""
        try:
            headers = {
                'User-Agent': 'Marina/1.0 (https://github.com/user/marina)'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Load image
            image = Image.open(io.BytesIO(response.content))
            
            # Save to cache
            image.save(cache_path, 'JPEG', quality=85)
            
            return image
            
        except Exception as e:
            print(f"Image download error: {e}")
            return None
            
    def _get_default_image(self, size: Tuple[int, int] = (64, 64)) -> Image.Image:
        """Create a default album art image with music note"""
        from PIL import ImageDraw, ImageFont
        
        # Create dark gray background
        image = Image.new('RGB', size, color='#2d2d2d')
        draw = ImageDraw.Draw(image)
        
        # Add a border
        border_color = '#4CAF50'
        border_width = 2
        draw.rectangle(
            [border_width, border_width, size[0] - border_width, size[1] - border_width],
            outline=border_color,
            width=border_width
        )
        
        # Draw a music note symbol in the center
        center_x, center_y = size[0] // 2, size[1] // 2
        
        # Simple music note using basic shapes
        note_color = '#4CAF50'
        
        # Note stem
        stem_x = center_x + 8
        draw.line([stem_x, center_y - 15, stem_x, center_y + 10], fill=note_color, width=2)
        
        # Note head (oval)
        head_size = 8
        draw.ellipse(
            [center_x - head_size//2, center_y + 5, center_x + head_size//2, center_y + 15],
            fill=note_color
        )
        
        # Note flag
        flag_points = [
            (stem_x, center_y - 15),
            (stem_x + 12, center_y - 10),
            (stem_x + 12, center_y - 5),
            (stem_x, center_y)
        ]
        draw.polygon(flag_points, fill=note_color)
        
        # Add text at the bottom
        try:
            # Try to use a small font
            font_size = max(8, size[1] // 8)
            font = ImageFont.load_default()
            text = "♪"
            
            # Get text size
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the text at the bottom
            text_x = (size[0] - text_width) // 2
            text_y = size[1] - text_height - 5
            
            draw.text((text_x, text_y), text, fill=note_color, font=font)
            
        except Exception as e:
            print(f"Error drawing text on default image: {e}")
        
        return image
        
    def fetch_album_art_sync(self, song_name: str, artist_name: str, 
                           size: Tuple[int, int] = (64, 64)) -> Image.Image:
        """Synchronously fetch album art"""
        cache_path = self._get_cache_path(song_name, artist_name)
        
        # Check if we have it cached
        if os.path.exists(cache_path):
            try:
                image = Image.open(cache_path)
                return image.resize(size, Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"Cache read error: {e}")
                os.remove(cache_path)  # Remove corrupted cache
                
        # Search MusicBrainz
        release_id = self._search_musicbrainz(song_name, artist_name)
        
        if release_id:
            # Get cover art URL
            cover_url = self._get_coverart_url(release_id)
            
            if cover_url:
                # Download image
                image = self._download_image(cover_url, cache_path)
                
                if image:
                    return image.resize(size, Image.Resampling.LANCZOS)
                    
        # Fallback to Last.fm (if implemented)
        # lastfm_url = self._fetch_lastfm_art(song_name, artist_name)
        
        # Return default image if nothing found
        return self._get_default_image(size)
        
    def fetch_album_art_async(self, song_name: str, artist_name: str, 
                            callback: Callable[[Image.Image], None],
                            size: Tuple[int, int] = (64, 64)):
        """Asynchronously fetch album art"""
        key = f"{artist_name}_{song_name}"
        
        # Cancel any existing request for this song
        if key in self.active_requests:
            # Mark old request as cancelled (simple flag)
            self.active_requests[key]['cancelled'] = True
            
        # Create new request info
        request_info = {'cancelled': False}
        self.active_requests[key] = request_info
        
        def fetch_worker():
            try:
                # Check if request was cancelled
                if request_info['cancelled']:
                    return
                    
                # First, try to provide cached image immediately
                cache_path = self._get_cache_path(song_name, artist_name)
                if os.path.exists(cache_path):
                    try:
                        image = Image.open(cache_path)
                        resized = image.resize(size, Image.Resampling.LANCZOS)
                        if not request_info['cancelled']:
                            callback(resized)
                            return
                    except Exception as e:
                        print(f"Cache read error: {e}")
                        os.remove(cache_path)
                        
                # If not cached, fetch from web
                image = self.fetch_album_art_sync(song_name, artist_name, size)
                
                # Call callback if not cancelled
                if not request_info['cancelled']:
                    callback(image)
                    
            except Exception as e:
                print(f"Async fetch error: {e}")
                # Provide default image on error
                if not request_info['cancelled']:
                    callback(self._get_default_image(size))
            finally:
                # Clean up request info
                self.active_requests.pop(key, None)
                
        # Start worker thread
        thread = threading.Thread(target=fetch_worker, daemon=True)
        thread.start()
        
    def clear_cache(self):
        """Clear the image cache"""
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
            self.image_cache.clear()
            print("Album art cache cleared")
        except Exception as e:
            print(f"Error clearing cache: {e}")
            
    def get_cache_size(self) -> int:
        """Get cache size in bytes"""
        total_size = 0
        try:
            for filename in os.listdir(self.cache_dir):
                filepath = os.path.join(self.cache_dir, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
        except Exception as e:
            print(f"Error calculating cache size: {e}")
            
        return total_size

# Test the fetcher
if __name__ == "__main__":
    import tkinter as tk
    from tkinter import ttk
    
    def test_fetcher():
        fetcher = AlbumArtFetcher()
        
        # Test sync fetch
        print("Testing sync fetch...")
        image = fetcher.fetch_album_art_sync("Bohemian Rhapsody", "Queen", (128, 128))
        print(f"Got image: {image.size}")
        
        # Test async fetch
        print("Testing async fetch...")
        def on_image_received(img):
            print(f"Async image received: {img.size}")
            
        fetcher.fetch_album_art_async("Hotel California", "Eagles", on_image_received, (128, 128))
        
        # Wait a bit for async
        time.sleep(2)
        
    test_fetcher()
