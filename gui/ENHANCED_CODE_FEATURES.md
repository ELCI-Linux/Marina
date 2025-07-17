# Enhanced Code Block Features - Smart Code Pane

## Overview
The Marina LLM Chat GUI now includes comprehensive enhanced code block detection and management features. These improvements provide intelligent file type identification, suggested file names, and a smart code pane for examining and navigating through generated code blocks.

## 🆕 New Features

### 1. **Enhanced Code Block Detection**
- **Intelligent File Type Detection**: Automatically identifies code types based on both language tags and content analysis
- **Smart Filename Generation**: Suggests meaningful filenames based on code content (function names, class names, comments, etc.)
- **Comprehensive Language Support**: Supports Python, Shell/Bash, HTML, CSS, JavaScript, JSON, YAML, XML, SQL, Dockerfile, and Makefile

### 2. **Smart Code Pane**
- **Centralized Code View**: Displays all generated code blocks in a dedicated, navigable pane
- **Navigation Controls**: Previous/Next buttons to browse through all code blocks
- **Detailed Information**: Shows file type, suggested filename, source LLM, and code description
- **Integrated Actions**: Run, Save, and Copy buttons directly in the code pane

### 3. **Enhanced Button Interface**
- **File Information Display**: Shows suggested filename and file type next to each code block
- **Smart Save Dialog**: Pre-populates filename and sets appropriate file type filters
- **View in Code Pane**: New button to display code in the dedicated smart pane

## 🔧 Technical Implementation

### Enhanced Code Block Processing
```python
def analyze_code_block(self, code_block, sender):
    """Analyze a code block to determine type, filename, and other metadata"""
    # Extracts language tags, detects content type, generates smart filenames
    return {
        'code': code_content,
        'language': detected_language,
        'type': code_type,
        'filename': suggested_filename,
        'extension': file_extension,
        'description': file_description,
        'sender': sender,
        'timestamp': timestamp
    }
```

### Intelligent Filename Generation
The system generates meaningful filenames based on:

#### Python Code:
- Function names: `def calculate_sum()` → `calculate_sum.py`
- Class names: `class DataProcessor` → `DataProcessor.py`
- Default: `script_[timestamp].py`

#### Shell Scripts:
- Comment-based names: `# backup script` → `backup_script.sh`
- Shebang detection: `#!/bin/bash` → `script.sh`
- Default: `script_[timestamp].sh`

#### HTML Files:
- Title extraction: `<title>My Page</title>` → `my_page.html`
- Default: `page_[timestamp].html`

#### JavaScript:
- Function names: `function validateForm()` → `validateForm.js`
- Default: `script_[timestamp].js`

#### Configuration Files:
- JSON: `data_[timestamp].json`
- YAML: `config_[timestamp].yaml`
- Docker: `Dockerfile`
- Makefile: `Makefile`

### Smart Code Pane Features
```python
def build_code_pane(self):
    """Build the smart code pane for displaying and navigating code blocks"""
    # Creates a comprehensive code viewing interface with:
    # - Navigation controls (Previous/Next)
    # - File information display
    # - Action buttons (Run/Save/Copy)
    # - Syntax-highlighted code display with line numbers
    # - Scrollable interface with theme support
```

## 🎯 User Interface Changes

### Updated Button Layout
Each code block now shows:
```
[🏃 Run] [💾 Save] [👁️ View] 📄 filename.py (Python script)
```

### Smart Code Pane Interface
```
📝 Smart Code Pane                    [⬅️ Previous] [Next ➡️] [❌ Close]
─────────────────────────────────────────────────────────────────────────
Code 1 of 3: 📄 greet_user.py (Python script) | From: Gemini | Type: PYTHON

[🏃 Run Code] [💾 Save Code] [📋 Copy Code]

┌─────────────────────────────────────────────────────────────────────────┐
│   1 │ def greet_user(name):                                             │
│   2 │     '''Greet a user with their name'''                           │
│   3 │     return f"Hello, {name}!"                                     │
│   4 │                                                                   │
│   5 │ # Test the function                                               │
│   6 │ if __name__ == "__main__":                                        │
│   7 │     print(greet_user("Marina"))                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

## 📋 Supported File Types

| Language | Extension | Description | Smart Detection |
|----------|-----------|-------------|----------------|
| Python | `.py` | Python script | Function/class names |
| Shell/Bash | `.sh` | Shell script | Comments, shebang |
| HTML | `.html` | HTML document | Title tag extraction |
| CSS | `.css` | CSS stylesheet | Generic naming |
| JavaScript | `.js` | JavaScript file | Function names |
| JSON | `.json` | JSON data file | Generic naming |
| YAML | `.yaml` | YAML configuration | Generic naming |
| XML | `.xml` | XML document | Generic naming |
| SQL | `.sql` | SQL script | Generic naming |
| Dockerfile | `` | Docker container file | Fixed name |
| Makefile | `` | Build automation file | Fixed name |

## 🚀 Usage Examples

### Example 1: Python Code with Function
```python
```python
def calculate_factorial(n):
    '''Calculate factorial of a number'''
    if n <= 1:
        return 1
    return n * calculate_factorial(n-1)

print(calculate_factorial(5))
```
```

**Result**: 
- Suggested filename: `calculate_factorial.py`
- File type: Python script
- Shows in smart code pane with navigation

### Example 2: Shell Script with Comment
```bash
```bash
#!/bin/bash
# System backup script
echo "Starting backup..."
tar -czf backup.tar.gz /home/user/documents
echo "Backup completed!"
```
```

**Result**:
- Suggested filename: `system_backup_script.sh`
- File type: Shell script
- Pre-configured save dialog for shell scripts

### Example 3: HTML with Title
```html
```html
<!DOCTYPE html>
<html>
<head>
    <title>Marina Dashboard</title>
</head>
<body>
    <h1>Welcome to Marina</h1>
</body>
</html>
```
```

**Result**:
- Suggested filename: `marina_dashboard.html`
- File type: HTML document
- Opens in browser when executed

## 🔧 Configuration and Customization

### Theme Integration
The smart code pane respects the current theme settings:
- **Dark Theme**: Dark background with light text
- **Light Theme**: Light background with dark text
- **Syntax Highlighting**: Monospace font (Consolas) with proper indentation

### File Type Associations
```python
def get_file_types_for_code_type(self, code_type):
    """Get appropriate file types for save dialog based on code type"""
    type_mappings = {
        'python': [('Python files', '*.py'), ('All files', '*.*')],
        'shell': [('Shell scripts', '*.sh'), ('Bash scripts', '*.bash'), ('All files', '*.*')],
        'html': [('HTML files', '*.html'), ('HTM files', '*.htm'), ('All files', '*.*')],
        # ... additional mappings
    }
```

## 🎨 User Experience Enhancements

### Visual Indicators
- **📄 File Icon**: Indicates detected file type
- **🏃 Run Button**: Execute code immediately
- **💾 Save Button**: Save with smart filename suggestion
- **👁️ View Button**: Open in smart code pane
- **Navigation Arrows**: Browse through code blocks

### Accessibility Features
- **Keyboard Navigation**: Full keyboard support in code pane
- **Screen Reader Friendly**: Proper labels and descriptions
- **High Contrast**: Theme-aware color schemes
- **Scalable Interface**: Responsive design

## 🔮 Future Enhancements

### Planned Features
1. **Syntax Highlighting**: Real-time syntax highlighting for different languages
2. **Code Completion**: Auto-completion suggestions in code pane
3. **Code History**: Save and recall previously executed code blocks
4. **Multi-file Projects**: Support for related code files
5. **Export Options**: Export code collections as ZIP files
6. **Search Functionality**: Search through all generated code blocks

### Integration Opportunities
- **Version Control**: Git integration for code tracking
- **Code Quality**: Linting and formatting integration
- **Documentation**: Auto-generation of code documentation
- **Testing**: Unit test generation for code blocks

## 📊 Performance Considerations

### Optimization Features
- **Lazy Loading**: Code blocks loaded on demand
- **Memory Management**: Efficient storage of code metadata
- **Threading**: Non-blocking UI updates
- **Caching**: Smart caching of processed code blocks

### Scalability
- **Large Code Blocks**: Efficient handling of large code files
- **Many Code Blocks**: Optimized navigation for numerous code blocks
- **Real-time Updates**: Smooth updates without UI blocking

## 🛡️ Security Considerations

### Code Execution Safety
- **Sandboxed Execution**: Code runs in user's environment
- **Timeout Protection**: 30-second timeout for Python execution
- **Error Handling**: Comprehensive error catching and reporting
- **User Awareness**: Clear indication of what code is being executed

### File System Safety
- **Temporary Files**: Automatic cleanup of temporary files
- **Permission Checks**: Respects file system permissions
- **Path Validation**: Validates file paths before saving

This enhanced system transforms the Marina GUI into a powerful code development environment, making it easier to work with AI-generated code while maintaining safety and usability.
