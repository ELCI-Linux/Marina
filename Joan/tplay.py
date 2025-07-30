#!/usr/bin/env python3
"""
TPlay - Terminal Media Player for Joan
Simple terminal-based media player integrated with Joan's ASCII interface

Part of Marina AI System
"""

import subprocess
import os
import signal
import time
from pathlib import Path
from typing import Optional, List

class TPlay:
    """Terminal media player using mpv backend"""
    
    def __init__(self):
        self.process = None
        self.current_file = None
        self.is_paused = False
        self.supported_formats = [
            '.mp3', '.mp4', '.wav', '.flac', '.ogg', '.m4a', '.webm', 
            '.avi', '.mkv', '.mov', '.mpv', '.m4v', '.3gp', '.flv'
        ]
    
    def is_supported_format(self, file_path: str) -> bool:
        """Check if file format is supported"""
        return Path(file_path).suffix.lower() in self.supported_formats
    
    def play(self, media_path: str, volume: int = 80) -> str:
        """Play a media file
        
        Args:
            media_path: Path to media file
            volume: Volume level (0-100)
            
        Returns:
            Status message
        """
        if not os.path.exists(media_path):
            return f"❌ Error: Media file not found at {media_path}"
        
        if not self.is_supported_format(media_path):
            return f"❌ Error: Unsupported file format for {Path(media_path).suffix}"
        
        # Stop current playback if any
        if self.is_playing():
            self.stop()
        
        try:
            # Use mpv with terminal-friendly options
            mpv_args = [
                "mpv",
                "--no-video" if self._is_audio_file(media_path) else "--vo=gpu",
                f"--volume={volume}",
                "--no-input-default-bindings",
                "--input-ipc-server=/tmp/mpv-socket",
                "--really-quiet",
                media_path
            ]
            
            self.process = subprocess.Popen(
                mpv_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.current_file = media_path
            self.is_paused = False
            
            # Check if process started successfully
            time.sleep(0.1)
            if self.process.poll() is not None:
                error_output = self.process.stderr.read().decode('utf-8')
                return f"❌ Error starting playback: {error_output[:100]}..."
            
            filename = Path(media_path).name
            return f"🎵 Now playing: {filename}"
            
        except FileNotFoundError:
            return "❌ Error: mpv not found. Please install mpv to use tplay."
        except Exception as e:
            return f"❌ Error starting playback: {str(e)}"
    
    def pause(self) -> str:
        """Pause/unpause playback"""
        if not self.is_playing():
            return "❌ No media is currently playing"
        
        try:
            # Send pause command to mpv via IPC
            subprocess.run([
                "echo", "cycle pause"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.is_paused = not self.is_paused
            status = "⏸️  Paused" if self.is_paused else "▶️  Resumed"
            return f"{status}: {Path(self.current_file).name if self.current_file else 'Unknown'}"
            
        except Exception as e:
            return f"❌ Error controlling playback: {str(e)}"
    
    def stop(self) -> str:
        """Stop playback"""
        if not self.process:
            return "❌ No media is playing"
        
        try:
            # Terminate the entire process group
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            
            # Wait for process to terminate
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Force kill if didn't terminate gracefully
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                self.process.wait()
            
            filename = Path(self.current_file).name if self.current_file else "Unknown"
            
            self.process = None
            self.current_file = None
            self.is_paused = False
            
            return f"⏹️  Stopped: {filename}"
            
        except ProcessLookupError:
            # Process already terminated
            self.process = None
            self.current_file = None
            self.is_paused = False
            return "⏹️  Playback stopped"
        except Exception as e:
            return f"❌ Error stopping playback: {str(e)}"
    
    def status(self) -> str:
        """Get current playback status"""
        if not self.is_playing():
            return "⏹️  No media playing"
        
        filename = Path(self.current_file).name if self.current_file else "Unknown"
        status_icon = "⏸️" if self.is_paused else "▶️"
        
        return f"{status_icon} {filename}"
    
    def is_playing(self) -> bool:
        """Check if media is currently playing"""
        if not self.process:
            return False
        
        # Check if process is still running
        if self.process.poll() is not None:
            self.process = None
            self.current_file = None
            self.is_paused = False
            return False
        
        return True
    
    def list_supported_formats(self) -> str:
        """List supported media formats"""
        audio_formats = [fmt for fmt in self.supported_formats if fmt in ['.mp3', '.wav', '.flac', '.ogg', '.m4a']]
        video_formats = [fmt for fmt in self.supported_formats if fmt not in audio_formats]
        
        result = "📋 Supported Media Formats:\n\n"
        result += f"🎵 Audio: {', '.join(audio_formats)}\n"
        result += f"🎬 Video: {', '.join(video_formats)}"
        
        return result
    
    def _is_audio_file(self, file_path: str) -> bool:
        """Check if file is audio-only"""
        audio_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']
        return Path(file_path).suffix.lower() in audio_extensions
    
    def find_media_files(self, directory: str) -> List[str]:
        """Find media files in directory
        
        Args:
            directory: Directory to search
            
        Returns:
            List of media file paths
        """
        if not os.path.isdir(directory):
            return []
        
        media_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if self.is_supported_format(file):
                    media_files.append(os.path.join(root, file))
        
        return sorted(media_files)

# Command-line interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="TPlay - Terminal Media Player for Joan",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tplay.py play song.mp3                    # Play a media file
  tplay.py stop                             # Stop playback
  tplay.py status                           # Show status
  tplay.py formats                          # List supported formats
  tplay.py find ~/Music                     # Find media files
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Play command
    play_parser = subparsers.add_parser('play', help='Play a media file')
    play_parser.add_argument('file', help='Path to media file')
    play_parser.add_argument('--volume', '-v', type=int, default=80, help='Volume (0-100)')
    
    # Control commands
    subparsers.add_parser('pause', help='Pause/unpause playback')
    subparsers.add_parser('stop', help='Stop playback')
    subparsers.add_parser('status', help='Show playback status')
    subparsers.add_parser('formats', help='List supported formats')
    
    # Find command
    find_parser = subparsers.add_parser('find', help='Find media files in directory')
    find_parser.add_argument('directory', help='Directory to search')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    player = TPlay()
    
    if args.command == 'play':
        result = player.play(args.file, args.volume)
    elif args.command == 'pause':
        result = player.pause()
    elif args.command == 'stop':
        result = player.stop()
    elif args.command == 'status':
        result = player.status()
    elif args.command == 'formats':
        result = player.list_supported_formats()
    elif args.command == 'find':
        files = player.find_media_files(args.directory)
        if files:
            result = f"📁 Found {len(files)} media files in {args.directory}:\n"
            result += "\n".join(f"  • {os.path.basename(f)}" for f in files[:20])
            if len(files) > 20:
                result += f"\n  ... and {len(files) - 20} more files"
        else:
            result = f"📁 No media files found in {args.directory}"
    
    print(result)

if __name__ == "__main__":
    main()

