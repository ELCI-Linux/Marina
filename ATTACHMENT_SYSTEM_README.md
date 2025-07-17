# Marina LLM Chat GUI - Attachment System

## Overview

The attachment system allows users to attach files to their LLM prompts using a intuitive GUI interface. Files are selected using zenity file picker, displayed with appropriate icons and metadata, and can be previewed, edited, and removed before submission.

## Features

### 📎 File Selection
- Uses `zenity --file --multiple` for native file selection dialog
- Supports multiple file selection
- Cross-platform file picker integration

### 🎨 Rich File Display
- **File Icons**: Each file type gets an appropriate emoji icon
  - 📄 Text files
  - 💻 Code files (Python, JavaScript, etc.)
  - 🖼️ Image files
  - 🎵 Audio files
  - 🎬 Video files
  - 📕 PDF files
  - 📊 Excel/spreadsheet files
  - 📝 Word documents
  - 🗜️ Compressed files
  - 📎 Other files

- **File Metadata**: Shows file name and size
- **Action Buttons**: Preview (👁️) and Remove (❌) buttons for each file

### 👁️ Smart Preview System
- **Text Files**: Full content preview with syntax highlighting
- **Image Files**: Thumbnail preview (requires PIL/Pillow)
- **Binary Files**: Metadata display (name, size, type, path)
- **Resizable Windows**: 800x600 preview windows with proper theming

### ✏️ Edit Capability
- **Text File Editing**: Built-in text editor for text files
- **Temporary File Management**: Edited files saved to `/tmp/marina_attachments_*`
- **Live Updates**: Changes reflected immediately in the attachment system
- **Auto-save**: Modified files automatically use temporary versions

### 🗑️ Attachment Management
- **Individual Removal**: Remove specific attachments
- **Bulk Operations**: Clear all attachments at once
- **Auto-cleanup**: Temporary files cleaned up on application exit

## File Type Support

### Text Files (Editable)
- `.txt`, `.md`, `.rst`
- `.py`, `.js`, `.ts`, `.jsx`, `.tsx`
- `.java`, `.cpp`, `.c`, `.h`, `.hpp`
- `.html`, `.css`, `.scss`, `.xml`
- `.json`, `.yaml`, `.yml`, `.toml`
- `.sql`, `.sh`, `.bash`, `.zsh`
- And many more...

### Image Files (Preview)
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`
- `.tiff`, `.webp`, `.svg`
- Requires PIL/Pillow for preview

### Other Files
- **Audio/Video**: Metadata display
- **PDF**: Metadata display
- **Compressed**: Metadata display
- **Documents**: Metadata display

## Integration with LLM System

### Prompt Enhancement
When attachments are present, the system automatically:
1. Adds attachment metadata to the prompt
2. Includes full text content for text files
3. Provides file information for binary files
4. Maintains proper formatting for LLM consumption

### Multi-LLM Support
- Works with all LLM providers (GPT-4, Gemini, DeepSeek, etc.)
- Consistent attachment handling across different models
- Automatic content formatting for optimal LLM processing

## Usage

### Basic Usage
1. Click the "📎 Attach" button in the input area
2. Select files using the zenity file picker
3. Files appear below the input area with icons and metadata
4. Click 👁️ to preview files
5. Click ❌ to remove files
6. Submit your prompt - attachments are automatically included

### Advanced Features
- **Edit Text Files**: In preview window, click "✏️ Edit" to modify text files
- **Batch Selection**: Select multiple files at once using Ctrl+click
- **Quick Remove**: Remove individual files without opening preview
- **Auto-clear**: Attachments are cleared after successful submission

## Technical Details

### Dependencies
- `zenity` - File selection dialog (install with `sudo apt install zenity`)
- `PIL/Pillow` - Image preview (optional, install with `pip install Pillow`)
- `tkinter` - GUI framework (usually included with Python)

### File Structure
```
gui/components/
├── attachment_manager.py    # Core attachment management
├── input_area.py           # Input area with attachment integration
└── llm_manager.py          # LLM integration with attachments
```

### Temporary Files
- Location: `/tmp/marina_attachments_*`
- Auto-cleanup: Yes, on application exit
- Edited files: Saved with original names in temp directory

### Security
- Files are processed locally
- No external network access for file handling
- Temporary files are properly cleaned up
- File type validation prevents malicious content

## Troubleshooting

### Common Issues

**zenity not found**
```bash
sudo apt install zenity
```

**Image preview not working**
```bash
pip install Pillow
```

**Permission denied**
- Ensure files are readable by the application
- Check file permissions: `ls -la filename`

**Attachment not showing**
- Verify file exists and is not corrupted
- Check console output for error messages
- Try with a different file type

### Debug Mode
Enable debug logging by setting `log_visible` to True in the main GUI to see detailed attachment processing information.

## Testing

Run the test script to verify attachment functionality:
```bash
python3 test_attachment_system.py
```

This creates test files and opens a GUI to test all attachment features.

## Future Enhancements

- **Drag & Drop**: Support for dragging files directly into the GUI
- **Cloud Storage**: Integration with cloud storage providers
- **File Compression**: Automatic compression for large files
- **Version Control**: Track changes to edited files
- **Batch Operations**: Select/remove multiple files at once
- **Preview Plugins**: Extended preview support for more file types
