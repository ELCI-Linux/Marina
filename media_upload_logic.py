#!/usr/bin/env python3
"""
Media Upload Logic for Marina LLM Chat GUI
Analyzes size of attachments and adapts based on LLM's context window
"""

import os
import shutil
import tempfile
import json
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import moviepy.editor as mp
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

class MediaUploadLogic:
    def __init__(self):
        # Context window sizes in tokens for each LLM (approximate)
        self.llm_context_window_sizes = {
            "GPT-4": 128000,      # GPT-4 Turbo
            "Claude": 100000,     # Claude 3
            "Gemini": 32000,      # Gemini Pro
            "DeepSeek": 32000,    # DeepSeek
            "Mistral": 32000,     # Mistral
            "LLaMA": 32000,       # LLaMA 2
            "Local": 4000         # Conservative estimate for local models
        }
        
        # Approximate token-to-byte ratios for different content types
        self.token_ratios = {
            'text': 4,     # ~4 bytes per token for text
            'image': 0.1,  # Images are tokenized differently
            'video': 0.01, # Video metadata only
            'audio': 0.1,  # Audio transcription estimates
            'binary': 0.01 # Binary files - metadata only
        }
        
    def analyze_and_optimize(self, prompt, attachments, target_llm):
        """Analyze attachments and optimize if necessary"""
        if not attachments:
            return []
            
        prompt_tokens = self.estimate_tokens(prompt, 'text')
        context_window = self.llm_context_window_sizes.get(target_llm, 8000)
        
        # Calculate total tokens needed
        attachment_tokens = 0
        for attachment in attachments:
            file_size = self.get_file_size(attachment['path'])
            tokens = self.estimate_tokens_from_file_size(file_size, attachment['type'])
            attachment_tokens += tokens
        
        total_tokens = prompt_tokens + attachment_tokens
        
        # Reserve 20% of context window for response
        available_tokens = int(context_window * 0.8)
        
        actions = []
        
        if total_tokens > available_tokens:
            print(f"Total tokens ({total_tokens}) exceed available context ({available_tokens})")
            
            # Determine optimization strategy
            if len(attachments) < 5:
                # Segment files if we have fewer than 5 attachments
                for attachment in attachments:
                    action = self.segment_file(attachment, available_tokens // len(attachments))
                    actions.append((attachment['name'], action))
            else:
                # Reduce resolution/convert formats for larger attachment sets
                for attachment in attachments:
                    if attachment['type'] == 'image':
                        action = self.reduce_resolution(attachment)
                    elif attachment['type'] == 'video':
                        action = self.convert_video_format(attachment)
                    elif attachment['type'] == 'text':
                        action = self.compress_text(attachment)
                    else:
                        action = "No optimization available for this file type"
                    
                    actions.append((attachment['name'], action))
        else:
            print(f"Total tokens ({total_tokens}) fit within context window ({available_tokens})")
        
        return actions
        
    def get_file_size(self, file_path):
        """Get size of a file in bytes"""
        try:
            return os.path.getsize(file_path)
        except OSError as e:
            print(f"Error getting file size: {e}")
            return 0
    
    def estimate_tokens(self, text, content_type):
        """Estimate tokens from text content"""
        if content_type == 'text':
            # Rough estimate: 1 token per 4 characters
            return len(text) // 4
        return 0
        
    def estimate_tokens_from_file_size(self, file_size, content_type):
        """Estimate tokens from file size and content type"""
        ratio = self.token_ratios.get(content_type, 0.01)
        return int(file_size * ratio)
    
    def segment_file(self, attachment, target_tokens):
        """Segment file into smaller parts"""
        try:
            if attachment['type'] == 'text':
                with open(attachment['path'], 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Calculate segment size based on target tokens
                target_chars = target_tokens * 4  # ~4 chars per token
                segments = [content[i:i + target_chars] for i in range(0, len(content), target_chars)]
                
                # Save segments to temporary files
                segment_paths = []
                for i, segment in enumerate(segments):
                    segment_path = attachment['path'].replace('.', f'_segment_{i}.')
                    with open(segment_path, 'w', encoding='utf-8') as f:
                        f.write(segment)
                    segment_paths.append(segment_path)
                
                return f"Segmented into {len(segments)} parts: {', '.join(segment_paths)}"
            else:
                return "Segmentation not supported for this file type"
        except Exception as e:
            return f"Failed to segment: {e}"
    
    def reduce_resolution(self, attachment):
        """Reduce image resolution"""
        if attachment['type'] != 'image':
            return "Not applicable for non-image"
        
        if not PIL_AVAILABLE:
            return "PIL not available - cannot reduce resolution"
        
        try:
            with Image.open(attachment['path']) as img:
                # Reduce to 50% of original size
                new_width = img.width // 2
                new_height = img.height // 2
                img_resized = img.resize((new_width, new_height), Image.LANCZOS)
                
                # Save with reduced resolution
                reduced_path = attachment['path'].replace('.', '_reduced.')
                img_resized.save(reduced_path, optimize=True, quality=85)
                
                # Update attachment path
                attachment['path'] = reduced_path
                
                return f"Resolution reduced to {new_width}x{new_height} and saved to {reduced_path}"
        except Exception as e:
            return f"Failed to reduce resolution: {e}"

    def convert_video_format(self, attachment):
        """Convert video to efficient format"""
        if attachment['type'] != 'video':
            return "Not applicable for non-video"
        
        if not MOVIEPY_AVAILABLE:
            return "MoviePy not available - cannot convert video"

        try:
            clip = mp.VideoFileClip(attachment['path'])
            
            # Convert to MP4 with reduced bitrate
            converted_path = attachment['path'].replace('.', '_converted.mp4')
            clip.write_videofile(
                converted_path, 
                codec='libx264', 
                audio_codec='aac',
                bitrate='1000k',  # Reduced bitrate
                verbose=False,
                logger=None
            )
            
            # Clean up
            clip.close()
            
            # Update attachment path
            attachment['path'] = converted_path
            
            return f"Video converted to MP4 and saved to {converted_path}"
        except Exception as e:
            return f"Failed to convert video: {e}"
            
    def compress_text(self, attachment):
        """Compress text file by removing extra whitespace"""
        if attachment['type'] != 'text':
            return "Not applicable for non-text"
            
        try:
            with open(attachment['path'], 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Remove extra whitespace and empty lines
            lines = content.split('\n')
            compressed_lines = [line.strip() for line in lines if line.strip()]
            compressed_content = '\n'.join(compressed_lines)
            
            # Save compressed version
            compressed_path = attachment['path'].replace('.', '_compressed.')
            with open(compressed_path, 'w', encoding='utf-8') as file:
                file.write(compressed_content)
            
            # Update attachment path
            attachment['path'] = compressed_path
            
            original_size = len(content)
            compressed_size = len(compressed_content)
            reduction = ((original_size - compressed_size) / original_size) * 100
            
            return f"Text compressed by {reduction:.1f}% and saved to {compressed_path}"
        except Exception as e:
            return f"Failed to compress text: {e}"

