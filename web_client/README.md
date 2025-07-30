# Marina Web Client

A secure, session-isolated web interface for Marina CLI functionality. This web application provides a user-friendly GUI for interacting with Marina's comprehensive AI assistant capabilities.

## Features

### 🔒 Security & Isolation
- **Session-based isolation**: Each web session gets a dedicated workspace folder
- **Sandboxed file operations**: Users cannot access files outside their session directory
- **Automatic cleanup**: Session workspaces are automatically cleaned up after 24 hours
- **Secure file uploads**: File type restrictions and size limits enforced

### 🧠 Marina CLI Integration
- **LLM Tasks**: Execute tasks using Marina's LLM routing system (GPT, Gemini, Claude, DeepSeek)
- **Context Scanning**: Perform system context analysis for enhanced task execution
- **Model Management**: Manage local AI models (load, suspend, status, recommendations)
- **Knowledge Scraping**: Execute web scraping tasks with multiple extraction pipelines
- **Feedback System**: Provide feedback for continuous system improvement
- **File Management**: Upload, download, and manage session files

### 🎨 User Interface
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Bootstrap-based**: Modern, clean interface with Font Awesome icons
- **Real-time Feedback**: Loading states, progress indicators, and alert messages
- **Session Indicator**: Always visible session ID for workspace identification

## Installation

1. **Install Dependencies**:
   ```bash
   cd /home/adminx/Marina/web_client
   pip install -r requirements.txt
   ```

2. **Verify Marina CLI**: Ensure the Marina CLI (`marina_cli.py`) is accessible from the parent directory.

## Usage

### Starting the Web Client

#### Basic Usage
```bash
python3 run.py
```
This starts the web client on `http://0.0.0.0:5000`

#### With Custom Configuration
```bash
python3 run.py --host 127.0.0.1 --port 8080 --debug
```

#### With SSL (HTTPS)
```bash
python3 run.py --ssl --cert cert.pem --key key.pem
```

#### Command Line Options
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 5000)
- `--debug`: Enable debug mode
- `--ssl`: Enable SSL/HTTPS
- `--cert`: SSL certificate file path
- `--key`: SSL private key file path

### Direct Flask Usage
```bash
python3 app.py
```

## Web Interface Guide

### Dashboard
The main dashboard provides access to all Marina functionality:
- **LLM Tasks**: Submit tasks to Marina's AI models
- **Context Scan**: Analyze system context
- **Models**: Manage AI model loading and status
- **Scraper**: Execute knowledge extraction tasks
- **Feedback**: Provide system feedback
- **Files**: Manage session files and uploads

### LLM Tasks
1. Enter a task description
2. Configure optional parameters:
   - Token limit
   - Specific model selection
   - Output format (text, code, JSON, image)
   - Programming language (for code output)
   - Save options
3. Execute and view results

### Context Scanning
1. Select scan mode:
   - **Inferred**: Balanced scan (default)
   - **Complete**: Deep scan with full analysis
   - **None**: Minimal scan
2. Configure whitelist/blacklist directories
3. Run scan and review context data

### Model Management
- **Status**: View current model status and details
- **Load**: Load models for specific tasks or by name
- **Suspend**: Suspend all models or specific ones
- **Recommendations**: Get model recommendations

### Knowledge Scraping
1. Select scraper type:
   - **General**: Standard web scraping
   - **Enhanced**: 4-engine analysis with LLM revision
   - **Sitemap Alphabetical**: Systematic sitemap crawling
   - **ArchWiki Flatpak**: Specialized ArchWiki scraping
2. Configure parameters:
   - URL to scrape
   - Maximum depth
   - Request delay
   - Time limits
   - Keywords for focus
3. Execute scraping task

### File Management
- **Upload**: Add files to your session workspace
- **Download**: Retrieve files from your workspace
- **Delete**: Remove files from your workspace
- **Session Cleanup**: Clear all files in your workspace

## Security Features

### Session Isolation
Each web session receives a unique UUID-based workspace directory. All file operations are restricted to this directory, preventing access to system files or other users' data.

### File Security
- **Type Restrictions**: Only allowed file extensions can be uploaded
- **Size Limits**: Maximum file size of 16MB per upload
- **Path Validation**: All file paths are validated to prevent directory traversal attacks

### Automatic Cleanup
- Background process removes session workspaces older than 24 hours
- Manual cleanup option available in the file management interface

## API Endpoints

The web client provides a REST API for programmatic access:

### LLM Tasks
- `POST /api/llm/execute` - Execute LLM task

### Context Scanning
- `POST /api/context/scan` - Run context scan

### Model Management
- `GET /api/models/status` - Get model status
- `POST /api/models/load` - Load model
- `POST /api/models/suspend` - Suspend model
- `GET /api/models/recommend` - Get recommendations

### Scraping
- `POST /api/scraper/execute` - Execute scraping task

### Feedback
- `POST /api/feedback/{action}` - Process feedback

### File Management
- `POST /api/files/upload` - Upload file
- `GET /api/files/download/{path}` - Download file
- `DELETE /api/files/delete/{path}` - Delete file

### Session Management
- `GET /api/session/info` - Get session information
- `POST /api/session/cleanup` - Clean session workspace

## Development

### Project Structure
```
web_client/
├── app.py                 # Main Flask application
├── run.py                 # Startup script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── llm.html
│   ├── context.html
│   ├── models.html
│   ├── scraper.html
│   ├── feedback.html
│   ├── files.html
│   └── error.html
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── common.js     # Common JavaScript functions
└── sessions/             # Session workspaces (auto-created)
```

### Adding New Features
1. Add route handlers to `app.py`
2. Create corresponding HTML templates
3. Add client-side JavaScript for interactivity
4. Update navigation in `base.html`

## Troubleshooting

### Common Issues

**Web client won't start:**
- Check if port is already in use
- Verify Python dependencies are installed
- Ensure Marina CLI is accessible

**Marina CLI commands fail:**
- Verify `marina_cli.py` path in `app.py`
- Check Marina CLI dependencies
- Review session environment variables

**File uploads fail:**
- Check file size limits
- Verify allowed file extensions
- Ensure sufficient disk space

### Logs
The web client logs activities to:
- Console output (when using `run.py`)
- `marina_web_client.log` file

### Debug Mode
Enable debug mode for detailed error messages:
```bash
python3 run.py --debug
```

## License

This web client is part of the Marina AI Assistant project. Please refer to the main Marina project for licensing information.

## Support

For issues, improvements, or questions about the Marina Web Client, please refer to the main Marina project documentation or contact the development team.
