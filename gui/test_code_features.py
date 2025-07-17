#!/usr/bin/env python3
"""
Test script to demonstrate the code execution, preview, and save features
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from components.chat_feed import ChatFeed
from themes.themes import ThemeManager
import tkinter as tk

def test_code_features():
    """Test the code execution features"""
    
    # Create a test window
    root = tk.Tk()
    root.title("Test Code Features")
    root.geometry("800x600")
    
    # Initialize theme manager
    theme_manager = ThemeManager(root)
    theme_manager.apply_dark_theme()
    
    # Create chat feed
    chat_feed = ChatFeed(root, theme_manager)
    
    # Test Python code with function
    python_code = """
```python
def greet_user(name):
    '''Greet a user with their name'''
    return f"Hello, {name}!"

# Test the function
if __name__ == "__main__":
    print(greet_user("Marina"))
    for i in range(3):
        print(f"Count: {i}")
```
"""
    
    # Test Shell code with meaningful comment
    shell_code = """
```bash
#!/bin/bash
# System info script
echo "System Information:"
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la
echo "Current user: $(whoami)"
```
"""
    
    # Test HTML code with title
    html_code = """
```html
<!DOCTYPE html>
<html>
<head>
    <title>Marina Test Page</title>
    <style>
        body { font-family: Arial, sans-serif; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Welcome to Marina</h1>
    <p>This is a test HTML page demonstrating the enhanced code features.</p>
    <button onclick="alert('Hello from Marina!')">Click Me</button>
</body>
</html>
```
"""
    
    # Test JavaScript code
    javascript_code = """
```javascript
function calculateSum(a, b) {
    return a + b;
}

// Test the function
const result = calculateSum(5, 3);
console.log(`The sum is: ${result}`);

// More complex example
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(n => n * 2);
console.log('Doubled numbers:', doubled);
```
"""
    
    # Test JSON data
    json_code = """
```json
{
    "name": "Marina",
    "version": "1.0",
    "features": [
        "LLM Integration",
        "Code Execution",
        "Smart Code Pane"
    ],
    "config": {
        "theme": "dark",
        "auto_save": true
    }
}
```
"""
    
    # Add test messages with code blocks
    chat_feed.append_chat("System", "Welcome to Marina Enhanced Code Testing!", "user")
    chat_feed.append_chat("Gemini", f"Here's some Python code to test: {python_code}", "Gemini")
    chat_feed.append_chat("Gemini", f"Here's some Shell code to test: {shell_code}", "Gemini")
    chat_feed.append_chat("Gemini", f"Here's some HTML code to test: {html_code}", "Gemini")
    chat_feed.append_chat("Gemini", f"Here's some JavaScript code to test: {javascript_code}", "Gemini")
    chat_feed.append_chat("Gemini", f"Here's some JSON data to test: {json_code}", "Gemini")
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    test_code_features()
