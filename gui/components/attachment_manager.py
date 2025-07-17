#!/usr/bin/env python3
"""
Attachment Manager for Marina LLM Chat GUI
Handles file attachments with preview, editing, and removal capabilities
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import shutil
import mimetypes
from pathlib import Path
import tempfile

class AttachmentManager:
    def __init__(self, root, theme_manager):
        self.root = root
        self.theme_manager = theme_manager
        self.attachments = []
        self.attachment_widgets = {}
        self.preview_window = None
        self.tmp_dir = tempfile.mkdtemp(prefix="marina_attachments_")
        
        # Ensure tmp directory exists
        os.makedirs(self.tmp_dir, exist_ok=True)
        
        # File type icons mapping
        self.file_icons = {
            'text': '📄',
            'image': '🖼️',
            'audio': '🎵',
            'video': '🎬',
            'pdf': '📕',
            'zip': '🗜️',
            'code': '💻',
            'excel': '📊',
            'word': '📝',
            'powerpoint': '📊',
            'default': '📎'
        }
        
        # Code file extensions
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.sh',
            '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.html', '.css',
            '.scss', '.sass', '.less', '.xml', '.json', '.yaml', '.yml', '.toml',
            '.ini', '.cfg', '.conf', '.sql', '.md', '.rst', '.txt', '.log'
        }
        
    def select_attachments(self):
        """Use zenity to select multiple files"""
        try:
            # Run zenity file selection dialog
            result = subprocess.run([
                'zenity', '--file-selection', '--multiple', '--separator=\n'
            ], capture_output=True, text=True, check=True)
            
            if result.returncode == 0 and result.stdout.strip():
                file_paths = result.stdout.strip().split('\n')
                for file_path in file_paths:
                    if file_path and os.path.exists(file_path):
                        self.add_attachment(file_path)
                        
        except subprocess.CalledProcessError:
            # User cancelled the dialog
            pass
        except FileNotFoundError:
            messagebox.showerror("Error", "zenity not found. Please install zenity for file selection.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select files: {str(e)}")
    
    def add_attachment(self, file_path):
        """Add a file attachment"""
        if file_path in [att['path'] for att in self.attachments]:
            messagebox.showwarning("Warning", f"File already attached: {os.path.basename(file_path)}")
            return
            
        try:
            file_stat = os.stat(file_path)
            file_size = self.format_file_size(file_stat.st_size)
            file_name = os.path.basename(file_path)
            file_icon = self.get_file_icon(file_path)
            
            attachment = {
                'path': file_path,
                'name': file_name,
                'size': file_size,
                'icon': file_icon,
                'type': self.get_file_type(file_path)
            }
            
            self.attachments.append(attachment)
            return attachment
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add attachment: {str(e)}")
            return None
    
    def get_file_icon(self, file_path):
        """Get appropriate icon for file type"""
        file_ext = Path(file_path).suffix.lower()
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if file_ext in self.code_extensions:
            return self.file_icons['code']
        elif mime_type:
            if mime_type.startswith('image/'):
                return self.file_icons['image']
            elif mime_type.startswith('audio/'):
                return self.file_icons['audio']
            elif mime_type.startswith('video/'):
                return self.file_icons['video']
            elif mime_type == 'application/pdf':
                return self.file_icons['pdf']
            elif mime_type.startswith('text/'):
                return self.file_icons['text']
            elif 'zip' in mime_type or 'compressed' in mime_type:
                return self.file_icons['zip']
            elif 'excel' in mime_type or 'spreadsheet' in mime_type:
                return self.file_icons['excel']
            elif 'word' in mime_type or 'document' in mime_type:
                return self.file_icons['word']
            elif 'powerpoint' in mime_type or 'presentation' in mime_type:
                return self.file_icons['powerpoint']
        
        return self.file_icons['default']
    
    def get_file_type(self, file_path):
        """Determine file type for processing"""
        file_ext = Path(file_path).suffix.lower()
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if file_ext in self.code_extensions or (mime_type and mime_type.startswith('text/')):
            return 'text'
        elif mime_type and mime_type.startswith('image/'):
            return 'image'
        elif mime_type and mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type and mime_type.startswith('video/'):
            return 'video'
        else:
            return 'binary'
    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def create_attachment_widget(self, parent, attachment, on_preview, on_remove):
        """Create a widget for displaying an attachment"""
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=2, pady=2)
        
        # File icon and name
        info_frame = ttk.Frame(frame)
        info_frame.pack(side="left", fill="x", expand=True)
        
        file_label = ttk.Label(info_frame, text=f"{attachment['icon']} {attachment['name']}")
        file_label.pack(side="left", anchor="w")
        
        size_label = ttk.Label(info_frame, text=f"({attachment['size']})", 
                              foreground="gray")
        size_label.pack(side="left", anchor="w", padx=(5, 0))
        
        # Action buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(side="right")
        
        preview_btn = ttk.Button(button_frame, text="👁️", width=3,
                                command=lambda: on_preview(attachment))
        preview_btn.pack(side="left", padx=2)
        
        remove_btn = ttk.Button(button_frame, text="❌", width=3,
                               command=lambda: on_remove(attachment))
        remove_btn.pack(side="left", padx=2)
        
        return frame
    
    def preview_attachment(self, attachment):
        """Open attachment preview window"""
        if self.preview_window:
            self.preview_window.destroy()
        
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.title(f"Preview: {attachment['name']}")
        self.preview_window.geometry("800x600")
        
        # Apply theme
        if self.theme_manager.dark_theme.get():
            self.preview_window.configure(bg=self.theme_manager.colors["bg"])
        
        # Create main frame
        main_frame = ttk.Frame(self.preview_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text=f"{attachment['icon']} {attachment['name']}")
        title_label.pack(anchor="w", pady=(0, 10))
        
        # Content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        if attachment['type'] == 'text':
            self.create_text_preview(content_frame, attachment)
        elif attachment['type'] == 'image':
            self.create_image_preview(content_frame, attachment)
        else:
            self.create_binary_preview(content_frame, attachment)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        if attachment['type'] == 'text':
            edit_btn = ttk.Button(button_frame, text="✏️ Edit", 
                                 command=lambda: self.edit_attachment(attachment))
            edit_btn.pack(side="left", padx=5)
        
        close_btn = ttk.Button(button_frame, text="Close", 
                              command=self.preview_window.destroy)
        close_btn.pack(side="right", padx=5)
    
    def create_text_preview(self, parent, attachment):
        """Create text file preview"""
        text_widget = tk.Text(parent, wrap=tk.WORD, font=("Monaco", 10))
        text_widget.pack(fill="both", expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)
        
        try:
            with open(attachment['path'], 'r', encoding='utf-8') as f:
                content = f.read()
            text_widget.insert(1.0, content)
            text_widget.config(state="disabled")
        except Exception as e:
            text_widget.insert(1.0, f"Error reading file: {str(e)}")
            text_widget.config(state="disabled")
    
    def create_image_preview(self, parent, attachment):
        """Create image file preview"""
        try:
            from PIL import Image, ImageTk
            
            # Load and resize image
            img = Image.open(attachment['path'])
            img.thumbnail((600, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            label = ttk.Label(parent, image=photo)
            label.image = photo  # Keep a reference
            label.pack(expand=True)
            
        except ImportError:
            ttk.Label(parent, text="PIL not available. Cannot preview image.").pack(expand=True)
        except Exception as e:
            ttk.Label(parent, text=f"Error loading image: {str(e)}").pack(expand=True)
    
    def create_binary_preview(self, parent, attachment):
        """Create binary file preview"""
        info_text = f"Binary file: {attachment['name']}\n"
        info_text += f"Size: {attachment['size']}\n"
        info_text += f"Type: {attachment['type']}\n"
        info_text += f"Path: {attachment['path']}"
        
        ttk.Label(parent, text=info_text, justify="left").pack(expand=True)
    
    def edit_attachment(self, attachment):
        """Edit text attachment"""
        if attachment['type'] != 'text':
            messagebox.showwarning("Warning", "Only text files can be edited.")
            return
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit: {attachment['name']}")
        edit_window.geometry("800x600")
        
        # Apply theme
        if self.theme_manager.dark_theme.get():
            edit_window.configure(bg=self.theme_manager.colors["bg"])
        
        # Create main frame
        main_frame = ttk.Frame(edit_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text=f"Editing: {attachment['name']}")
        title_label.pack(anchor="w", pady=(0, 10))
        
        # Text editor
        text_widget = tk.Text(main_frame, wrap=tk.WORD, font=("Monaco", 10))
        text_widget.pack(fill="both", expand=True, pady=(0, 10))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Load content
        try:
            with open(attachment['path'], 'r', encoding='utf-8') as f:
                content = f.read()
            text_widget.insert(1.0, content)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
            edit_window.destroy()
            return
        
        # Save function
        def save_changes():
            try:
                content = text_widget.get(1.0, tk.END)
                # Save to tmp directory with same name
                tmp_path = os.path.join(self.tmp_dir, attachment['name'])
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Update attachment path to tmp version
                attachment['path'] = tmp_path
                
                messagebox.showinfo("Success", f"File saved to: {tmp_path}")
                edit_window.destroy()
                
                # Close preview window if open
                if self.preview_window:
                    self.preview_window.destroy()
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        save_btn = ttk.Button(button_frame, text="💾 Save", command=save_changes)
        save_btn.pack(side="left", padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=edit_window.destroy)
        cancel_btn.pack(side="right", padx=5)
    
    def remove_attachment(self, attachment):
        """Remove an attachment"""
        if attachment in self.attachments:
            self.attachments.remove(attachment)
            return True
        return False
    
    def clear_attachments(self):
        """Clear all attachments"""
        self.attachments.clear()
        self.attachment_widgets.clear()
    
    def get_attachment_info(self):
        """Get information about all attachments"""
        return [
            {
                'name': att['name'],
                'path': att['path'],
                'size': att['size'],
                'type': att['type']
            }
            for att in self.attachments
        ]
    
    def cleanup_tmp_files(self):
        """Clean up temporary files"""
        try:
            if os.path.exists(self.tmp_dir):
                shutil.rmtree(self.tmp_dir)
        except Exception as e:
            print(f"Warning: Failed to cleanup tmp files: {e}")
