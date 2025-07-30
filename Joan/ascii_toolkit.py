#!/usr/bin/env python3
"""
ASCII Toolkit for Joan - Comprehensive ASCII Art and Text Rendering Module
Integrates various ASCII capabilities including:
- Image to ASCII conversion
- Text banners and figlet-style art
- ASCII charts and visualizations
- Decorative borders and frames

Part of Marina AI System
"""

import os
import sys
import math
from pathlib import Path
from PIL import Image
from typing import Optional, List, Dict, Any, Tuple
import subprocess
import shutil

class ASCIIToolkit:
    """Comprehensive ASCII art toolkit for Joan"""
    
    def __init__(self):
        self.ascii_chars = "@%#*+=-:. "  # From light to dark
        self.box_chars = {
            'thin': {'h': '─', 'v': '│', 'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘'},
            'thick': {'h': '━', 'v': '┃', 'tl': '┏', 'tr': '┓', 'bl': '┗', 'br': '┛'},
            'double': {'h': '═', 'v': '║', 'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝'},
            'rounded': {'h': '─', 'v': '│', 'tl': '╭', 'tr': '╮', 'bl': '╰', 'br': '╯'}
        }
        self.figlet_available = self._check_figlet()
        
    def _check_figlet(self) -> bool:
        """Check if figlet is available on the system"""
        return shutil.which('figlet') is not None
    
    # IMAGE TO ASCII METHODS
    def resize_image(self, image: Image.Image, new_width: int = 100) -> Image.Image:
        """Resize image while maintaining aspect ratio for ASCII conversion"""
        width, height = image.size
        ratio = height / width / 1.65  # Adjust for font aspect ratio
        new_height = int(new_width * ratio)
        return image.resize((new_width, new_height))
    
    def image_to_ascii(self, image_path: str, width: int = 80, 
                      chars: Optional[str] = None) -> Optional[str]:
        """Convert image to ASCII art
        
        Args:
            image_path: Path to image file
            width: Desired width of ASCII output
            chars: Custom ASCII character set (optional)
            
        Returns:
            ASCII art string or None if failed
        """
        if chars is None:
            chars = self.ascii_chars
            
        try:
            image = Image.open(image_path)
            image = self.resize_image(image, width)
            image = image.convert("L")  # Convert to grayscale
            
            pixels = image.getdata()
            ascii_str = "".join(chars[pixel // (256 // len(chars))] for pixel in pixels)
            
            # Break into lines
            ascii_lines = []
            for i in range(0, len(ascii_str), width):
                ascii_lines.append(ascii_str[i:i + width])
                
            return "\n".join(ascii_lines)
            
        except Exception as e:
            print(f"❌ Error converting image to ASCII: {e}")
            return None
    
    # TEXT BANNER METHODS
    def create_text_banner(self, text: str, font: str = "standard", width: int = 80) -> str:
        """Create ASCII text banner using figlet or fallback method
        
        Args:
            text: Text to convert to banner
            font: Figlet font name (if available)
            width: Maximum width for output
            
        Returns:
            ASCII banner text
        """
        if self.figlet_available:
            try:
                result = subprocess.run(
                    ['figlet', '-f', font, '-w', str(width), text],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.rstrip()
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass
        
        # Fallback to simple block letters
        return self._create_simple_banner(text, width)
    
    def _create_simple_banner(self, text: str, width: int = 80) -> str:
        """Create simple ASCII banner without figlet"""
        # Simple block letter patterns for common characters
        patterns = {
            'A': ["  ██  ", " ████ ", "██  ██", "██████", "██  ██"],
            'B': ["██████", "██  ██", "██████", "██████", "██████"],
            'C': [" █████", "██    ", "██    ", "██    ", " █████"],
            'D': ["██████", "██  ██", "██  ██", "██  ██", "██████"],
            'E': ["██████", "██    ", "█████ ", "██    ", "██████"],
            'F': ["██████", "██    ", "█████ ", "██    ", "██    "],
            'G': [" █████", "██    ", "██ ███", "██  ██", " █████"],
            'H': ["██  ██", "██  ██", "██████", "██  ██", "██  ██"],
            'I': ["██████", "  ██  ", "  ██  ", "  ██  ", "██████"],
            'J': ["██████", "    ██", "    ██", "██  ██", " █████"],
            'O': [" █████", "██  ██", "██  ██", "██  ██", " █████"],
            'N': ["██  ██", "███ ██", "██████", "██ ███", "██  ██"],
            ' ': ["      ", "      ", "      ", "      ", "      "]
        }
        
        lines = ["", "", "", "", ""]
        for char in text.upper():
            if char in patterns:
                for i, pattern_line in enumerate(patterns[char]):
                    lines[i] += pattern_line + " "
            else:
                # Unknown character - use placeholder
                for i in range(5):
                    lines[i] += "██████ "
        
        return "\n".join(lines)
    
    # BORDER AND FRAME METHODS
    def create_box(self, content: str, style: str = "thin", padding: int = 1,
                   title: Optional[str] = None) -> str:
        """Create a bordered box around content
        
        Args:
            content: Text content to box
            style: Box style ('thin', 'thick', 'double', 'rounded')
            padding: Internal padding
            title: Optional title for the box
            
        Returns:
            Boxed text
        """
        if style not in self.box_chars:
            style = "thin"
        
        chars = self.box_chars[style]
        lines = content.split('\n')
        
        # Calculate dimensions
        max_width = max(len(line) for line in lines) if lines else 0
        box_width = max_width + (padding * 2)
        
        # Create top border
        top_line = chars['tl'] + chars['h'] * box_width + chars['tr']
        if title:
            title_space = box_width - len(title) - 2
            if title_space >= 0:
                left_pad = title_space // 2
                right_pad = title_space - left_pad
                top_line = (chars['tl'] + chars['h'] * left_pad + 
                           f" {title} " + chars['h'] * right_pad + chars['tr'])
        
        # Create content lines
        content_lines = []
        for line in lines:
            padded_line = line.ljust(max_width)
            content_lines.append(
                chars['v'] + " " * padding + padded_line + " " * padding + chars['v']
            )
        
        # Create bottom border
        bottom_line = chars['bl'] + chars['h'] * box_width + chars['br']
        
        return "\n".join([top_line] + content_lines + [bottom_line])
    
    def create_separator(self, width: int = 80, char: str = "=", 
                        style: str = "simple") -> str:
        """Create a separator line
        
        Args:
            width: Width of separator
            char: Character to use for separator
            style: Style ('simple', 'fancy', 'wave')
            
        Returns:
            Separator string
        """
        if style == "fancy":
            return "┌" + "─" * (width - 2) + "┐"
        elif style == "wave":
            wave_chars = "~∼⋯∿⁓"
            return "".join(wave_chars[i % len(wave_chars)] for i in range(width))
        else:  # simple
            return char * width
    
    # CHART AND VISUALIZATION METHODS
    def create_horizontal_bar_chart(self, data: Dict[str, float], 
                                   width: int = 60, max_bar_width: int = 40) -> str:
        """Create horizontal ASCII bar chart
        
        Args:
            data: Dictionary of label -> value pairs
            width: Total width of chart
            max_bar_width: Maximum width for bars
            
        Returns:
            ASCII bar chart
        """
        if not data:
            return "No data to display"
        
        max_value = max(data.values())
        max_label_len = max(len(label) for label in data.keys())
        
        lines = []
        for label, value in data.items():
            # Calculate bar length
            if max_value > 0:
                bar_length = int((value / max_value) * max_bar_width)
            else:
                bar_length = 0
            
            # Create bar
            bar = "█" * bar_length
            padded_label = label.ljust(max_label_len)
            value_str = f"{value:.1f}"
            
            line = f"{padded_label} │{bar:<{max_bar_width}} {value_str}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def create_vertical_bar_chart(self, data: Dict[str, float], 
                                 height: int = 10, width: int = 60) -> str:
        """Create vertical ASCII bar chart
        
        Args:
            data: Dictionary of label -> value pairs
            height: Height of chart area
            width: Total width of chart
            
        Returns:
            ASCII bar chart
        """
        if not data:
            return "No data to display"
        
        max_value = max(data.values()) if data.values() else 1
        labels = list(data.keys())
        values = list(data.values())
        
        # Calculate bar positions
        bar_width = max(1, width // len(labels))
        
        lines = []
        
        # Create chart from top to bottom
        for row in range(height, 0, -1):
            line = ""
            for i, (label, value) in enumerate(data.items()):
                bar_height = int((value / max_value) * height)
                if row <= bar_height:
                    line += "█" * bar_width
                else:
                    line += " " * bar_width
            lines.append(line)
        
        # Add labels at bottom
        label_line = ""
        for label in labels:
            truncated_label = label[:bar_width]
            label_line += truncated_label.ljust(bar_width)
        lines.append(label_line)
        
        return "\n".join(lines)
    
    # PROGRESS AND STATUS METHODS
    def create_progress_bar(self, current: float, total: float, width: int = 50,
                           show_percentage: bool = True, 
                           fill_char: str = "█", empty_char: str = "░") -> str:
        """Create ASCII progress bar
        
        Args:
            current: Current progress value
            total: Total/maximum value
            width: Width of progress bar
            show_percentage: Whether to show percentage
            fill_char: Character for filled portion
            empty_char: Character for empty portion
            
        Returns:
            Progress bar string
        """
        if total <= 0:
            percentage = 0
        else:
            percentage = min(100, (current / total) * 100)
        
        filled_width = int((percentage / 100) * width)
        empty_width = width - filled_width
        
        bar = fill_char * filled_width + empty_char * empty_width
        
        if show_percentage:
            return f"[{bar}] {percentage:5.1f}%"
        else:
            return f"[{bar}]"
    
    def create_loading_spinner(self, step: int) -> str:
        """Create animated loading spinner character
        
        Args:
            step: Current animation step
            
        Returns:
            Single spinner character
        """
        spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        return spinners[step % len(spinners)]
    
    # UTILITY METHODS
    def wrap_text_in_border(self, text: str, border_style: str = "simple",
                           max_width: int = 80, padding: int = 2) -> str:
        """Wrap text and add border
        
        Args:
            text: Text to wrap and border
            border_style: Style of border
            max_width: Maximum width including border
            padding: Internal padding
            
        Returns:
            Bordered and wrapped text
        """
        # Word wrap the text
        words = text.split()
        lines = []
        current_line = ""
        content_width = max_width - (padding * 2) - 2  # Account for border and padding
        
        for word in words:
            if len(current_line + " " + word) <= content_width:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        wrapped_text = "\n".join(lines)
        return self.create_box(wrapped_text, border_style, padding)
    
    def center_text(self, text: str, width: int = 80, fill_char: str = " ") -> str:
        """Center text within given width
        
        Args:
            text: Text to center
            width: Total width
            fill_char: Character to use for padding
            
        Returns:
            Centered text
        """
        lines = text.split('\n')
        centered_lines = []
        
        for line in lines:
            if len(line) >= width:
                centered_lines.append(line)
            else:
                padding = width - len(line)
                left_pad = padding // 2
                right_pad = padding - left_pad
                centered_lines.append(fill_char * left_pad + line + fill_char * right_pad)
        
        return "\n".join(centered_lines)
    
    # INTEGRATION METHODS FOR JOAN
    def generate_welcome_screen(self, username: str = "User") -> str:
        """Generate Joan's welcome screen with ASCII art
        
        Args:
            username: Name to display in welcome
            
        Returns:
            Complete welcome screen
        """
        # Create Joan banner
        joan_banner = self.create_text_banner("JOAN", "standard", 80)
        
        # Create welcome message
        welcome_msg = f"Welcome back, {username}!\nMarina's ASCII Interface Assistant"
        welcome_box = self.create_box(welcome_msg, "rounded", 2, "Marina AI System")
        
        # Create separator
        separator = self.create_separator(80, "~", "wave")
        
        # Combine elements
        return f"{joan_banner}\n\n{welcome_box}\n{separator}\n"
    
    def display_system_status(self, status_data: Dict[str, Any]) -> str:
        """Display system status with ASCII visualization
        
        Args:
            status_data: Dictionary containing system metrics
            
        Returns:
            ASCII formatted system status
        """
        output_lines = []
        
        # CPU usage bar
        if 'cpu_percent' in status_data:
            cpu_bar = self.create_progress_bar(
                status_data['cpu_percent'], 100, 30, True, "█", "░"
            )
            output_lines.append(f"CPU Usage: {cpu_bar}")
        
        # Memory usage bar
        if 'memory_percent' in status_data:
            mem_bar = self.create_progress_bar(
                status_data['memory_percent'], 100, 30, True, "█", "░"
            )
            output_lines.append(f"Memory:    {mem_bar}")
        
        # Disk usage if available
        if 'disk_usage' in status_data:
            disk_data = {}
            for mount, usage in status_data['disk_usage'].items():
                disk_data[mount] = usage
            disk_chart = self.create_horizontal_bar_chart(disk_data, 50, 25)
            output_lines.append(f"\nDisk Usage:\n{disk_chart}")
        
        return "\n".join(output_lines)

# Convenience functions for Joan integration
def render_image_as_ascii(image_path: str, width: int = 80) -> Optional[str]:
    """Quick function to render image as ASCII"""
    toolkit = ASCIIToolkit()
    return toolkit.image_to_ascii(image_path, width)

def create_banner(text: str, style: str = "standard") -> str:
    """Quick function to create text banner"""
    toolkit = ASCIIToolkit()
    return toolkit.create_text_banner(text, style)

def create_bordered_text(text: str, style: str = "thin") -> str:
    """Quick function to create bordered text"""
    toolkit = ASCIIToolkit()
    return toolkit.create_box(text, style)

def show_progress(current: float, total: float, width: int = 50) -> str:
    """Quick function to show progress bar"""
    toolkit = ASCIIToolkit()
    return toolkit.create_progress_bar(current, total, width)

# Main execution
if __name__ == "__main__":
    # Demo the ASCII toolkit
    toolkit = ASCIIToolkit()
    
    print("ASCII Toolkit Demo for Joan")
    print("=" * 50)
    
    # Banner demo
    print("\n1. Text Banner:")
    print(toolkit.create_text_banner("HELLO"))
    
    # Box demo
    print("\n2. Bordered Text:")
    sample_text = "This is a sample text\nthat spans multiple lines\nfor demonstration purposes."
    print(toolkit.create_box(sample_text, "rounded", 2, "Sample Box"))
    
    # Progress bar demo
    print("\n3. Progress Bars:")
    for i in range(0, 101, 25):
        print(toolkit.create_progress_bar(i, 100, 40))
    
    # Chart demo
    print("\n4. Bar Chart:")
    sample_data = {"CPU": 75.5, "Memory": 60.2, "Disk": 45.8, "Network": 23.1}
    print(toolkit.create_horizontal_bar_chart(sample_data, 60, 30))
    
    print("\n" + "=" * 50)
    print("ASCII Toolkit Ready for Joan Integration!")
