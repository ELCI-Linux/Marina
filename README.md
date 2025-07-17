# 🚀 Marina's Spectra - Autonomous Browser System

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/marina/spectra)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success.svg)](https://github.com/marina/spectra)

> **Spectra** is a comprehensive autonomous browsing system that processes natural language intents and executes them through intelligent web automation with advanced coordination and multi-modal perception.

## 🌟 Overview

Spectra represents the next generation of autonomous web interaction, combining natural language processing, computer vision, session management, and intelligent automation into a unified system. It's designed to understand human intentions and execute complex web workflows with minimal supervision.

### Key Capabilities

- **🧠 Natural Language Intent Processing**: Understands and compiles human language into executable actions
- **🎯 Autonomous Navigation**: Intelligent web traversal with adaptive strategies
- **👁️ Visual & Audio Perception**: Advanced media analysis and content understanding
- **✅ Action Validation**: Real-time verification of action success/failure
- **💾 Session Persistence**: Maintains state across interruptions and restarts
- **🔐 Security & Privacy**: Encrypted sessions, stealth mode, and secure credential management
- **📊 Monitoring & Metrics**: Comprehensive system health and performance tracking

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Spectra Core                            │
│                  (Main Integration Layer)                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────  │
│  │ Navigation  │  │   Action    │  │   Media     │  │  Intent   │
│  │   Engine    │  │ Validator   │  │ Perception  │  │ Compiler  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                Session Manager                              │ │
│  │          (Persistent State & Workflow Management)          │ │
│  └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                     Browser Backends                           │
│              (Playwright, Selenium, WebKit)                    │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/marina/spectra.git
cd spectra

# Install dependencies
pip install -r requirements.txt

# Install browser dependencies (for Playwright)
playwright install
```

### Basic Usage

```python
import asyncio
from spectra import SpectraCore, SpectraConfig

async def main():
    # Initialize Spectra
    config = SpectraConfig()
    spectra = SpectraCore(config)
    
    # Initialize all components
    await spectra.initialize()
    
    # Execute a natural language intent
    result = await spectra.execute_intent(
        "Navigate to https://example.com and take a screenshot"
    )
    
    print(f"Success: {result.success}")
    print(f"Actions performed: {result.actions_performed}")
    print(f"Execution time: {result.execution_time:.2f}s")
    
    # Cleanup
    await spectra.shutdown()

# Run the example
asyncio.run(main())
```

### Configuration

Create a `spectra_config.yaml` file:

```yaml
# Core settings
mode: "autonomous"
max_concurrent_sessions: 10
default_timeout: 300.0

# Components
navigation_backend: "playwright"
enable_media_perception: true
enable_action_validation: true
enable_session_persistence: true

# Storage
storage_dir: "./spectra_data"
session_timeout: 3600
encrypt_sessions: true

# Security
sandbox_mode: true
allow_file_access: false
```

## 🧩 Components

### 1. Navigation Engine (`navigation_core.py`)
- **Purpose**: Core web navigation and automation
- **Features**: Multi-browser support, stealth mode, element detection
- **Backends**: Playwright, Selenium
- **Actions**: Click, type, scroll, navigate, extract data

### 2. Action Validator (`action_validator.py`)
- **Purpose**: Validates action success/failure
- **Features**: Visual comparison, DOM analysis, network monitoring
- **Methods**: Screenshot comparison, element state tracking
- **Outputs**: Success/failure determination with confidence scores

### 3. Media Perception Engine (`media_perception.py`)
- **Purpose**: Visual and audio content analysis
- **Features**: OCR, object detection, accessibility analysis
- **Capabilities**: Text extraction, element classification, quality assessment
- **Outputs**: Content understanding and interaction suggestions

### 4. Intent Compiler (`intent_compiler.py`)
- **Purpose**: Natural language to action sequence compilation
- **Features**: NLP processing, entity extraction, goal decomposition
- **Models**: BERT, spaCy, custom classification
- **Outputs**: Executable action sequences from text descriptions

### 5. Session Manager (`session_manager.py`)
- **Purpose**: Persistent state and workflow management
- **Features**: Encrypted storage, session recovery, credential management
- **Storage**: SQLite, Redis, file system
- **Capabilities**: Session cloning, export/import, workflow persistence

### 6. Spectra Core (`spectra_core.py`)
- **Purpose**: Main integration and orchestration layer
- **Features**: Component coordination, health monitoring, execution management
- **Capabilities**: Priority queuing, performance metrics, graceful shutdown

## 📋 Features

### 🎯 Intent Processing
- Natural language understanding
- Multi-step workflow compilation
- Context-aware action planning
- Error recovery and retry logic

### 🌐 Web Automation
- Multi-browser support (Chrome, Firefox, Safari)
- Stealth mode to avoid detection
- Intelligent element selection
- Dynamic content handling

### 👁️ Visual Intelligence
- Screenshot analysis and comparison
- OCR for text extraction
- UI element recognition
- Accessibility compliance checking

### 💾 State Management
- Persistent session storage
- Encrypted credential management
- Workflow state preservation
- Cross-session continuity

### 🔐 Security & Privacy
- End-to-end encryption
- Secure credential storage
- Sandbox mode execution
- Privacy-focused defaults

### 📊 Monitoring & Metrics
- Real-time health monitoring
- Performance metrics collection
- Prometheus integration
- Comprehensive logging

## 🛠️ Advanced Usage

### Custom Intent Processing

```python
# Define custom intent with specific session
result = await spectra.execute_intent(
    "Login to my account and check the dashboard",
    session_id="user_session_123",
    priority=ExecutionPriority.HIGH,
    timeout=120.0
)
```

### Session Management

```python
# Create a new session
session = await spectra.session_manager.create_session(
    name="E-commerce Automation",
    session_type=SessionType.STANDARD,
    user_id="user_123"
)

# Store credentials
credentials = AuthenticationCredentials(
    domain="shop.example.com",
    username="user@example.com",
    password="secure_password"
)
await spectra.session_manager.store_credentials(session.id, credentials)

# Execute workflow
workflow = Workflow(
    id=str(uuid.uuid4()),
    name="Purchase Flow",
    steps=[
        WorkflowStep(
            id=str(uuid.uuid4()),
            description="Add item to cart",
            action_type="click",
            parameters={"selector": ".add-to-cart"}
        ),
        WorkflowStep(
            id=str(uuid.uuid4()),
            description="Proceed to checkout",
            action_type="click",
            parameters={"selector": ".checkout-button"}
        )
    ]
)
await spectra.session_manager.add_workflow(session.id, workflow)
```

### Media Analysis

```python
# Analyze screenshot
screenshot = await page.screenshot()
analysis = await spectra.media_perception.analyze_media(
    screenshot, 
    MediaType.SCREENSHOT
)

print(f"Detected elements: {len(analysis.detected_elements)}")
print(f"Text regions: {len(analysis.text_regions)}")
print(f"Accessibility level: {analysis.accessibility_level.value}")

# Get interaction suggestions
interactions = spectra.media_perception.get_element_interactions(analysis)
```

## 🔧 Configuration Options

### Core Settings
- `mode`: Operation mode (autonomous, supervised, interactive, testing, headless)
- `max_concurrent_sessions`: Maximum parallel sessions
- `default_timeout`: Default action timeout

### Component Settings
- `navigation_backend`: Browser backend (playwright, selenium)
- `enable_media_perception`: Enable visual analysis
- `enable_action_validation`: Enable action verification
- `enable_session_persistence`: Enable state persistence

### Security Settings
- `sandbox_mode`: Enable sandboxed execution
- `encrypt_sessions`: Encrypt stored sessions
- `allow_file_access`: Allow file system access

### Performance Settings
- `max_memory_usage`: Maximum memory consumption (MB)
- `max_cpu_usage`: Maximum CPU usage (%)
- `cleanup_interval`: Resource cleanup interval (seconds)

## 📊 Monitoring

### System Status
```python
# Get comprehensive system status
status = await spectra.get_system_status()
print(f"Uptime: {status['uptime']:.1f}s")
print(f"Active sessions: {status['active_sessions']}")
print(f"Component health: {status['component_health']}")
```

### Performance Metrics
```python
# Get performance statistics
metrics = spectra.get_performance_metrics()
print(f"Total intents: {metrics['total_intents']}")
print(f"Success rate: {metrics['success_rate']:.2%}")
print(f"Average execution time: {metrics['average_execution_time']:.2f}s")
```

### Prometheus Integration
Spectra provides built-in Prometheus metrics:
- `spectra_intents_total`: Total intents processed
- `spectra_execution_time_seconds`: Execution time histogram
- `spectra_active_sessions`: Current active sessions
- `spectra_component_health`: Component health status

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest tests/

# Run specific component tests
pytest tests/test_navigation_core.py
pytest tests/test_intent_compiler.py
pytest tests/test_media_perception.py
```

### Integration Tests
```bash
# Run integration tests
pytest tests/integration/

# Run end-to-end tests
pytest tests/e2e/
```

## 🔄 Development

### Project Structure
```
spectra/
├── __init__.py              # Package initialization
├── spectra_core.py          # Main integration layer
├── navigation_core.py       # Navigation engine
├── action_validator.py      # Action validation
├── media_perception.py      # Media analysis
├── intent_compiler.py       # Intent processing
├── session_manager.py       # Session management
├── utils.py                 # Utility functions
├── requirements.txt         # Dependencies
└── tests/                   # Test suites
    ├── unit/               # Unit tests
    ├── integration/        # Integration tests
    └── e2e/               # End-to-end tests
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## 📚 API Reference

### Core Classes

#### SpectraCore
Main orchestration engine that coordinates all components.

```python
class SpectraCore:
    async def initialize()
    async def execute_intent(intent_text: str, **kwargs) -> ExecutionResult
    async def get_system_status() -> Dict[str, Any]
    async def shutdown()
```

#### NavigationEngine
Handles web navigation and automation.

```python
class NavigationEngine:
    async def navigate_to(url: str, **kwargs)
    async def click_element(selector: str, **kwargs)
    async def type_text(selector: str, text: str, **kwargs)
    async def extract_data(selector: str, **kwargs)
```

#### IntentCompiler
Processes natural language intents.

```python
class IntentCompiler:
    async def compile_intent(intent_text: str) -> Intent
    def get_intent_suggestions(partial_text: str) -> List[str]
    async def optimize_intent(intent: Intent) -> Intent
```

#### SessionManager
Manages persistent sessions and workflows.

```python
class SessionManager:
    async def create_session(name: str, **kwargs) -> BrowsingSession
    async def get_session(session_id: str) -> BrowsingSession
    async def store_credentials(session_id: str, credentials: AuthenticationCredentials)
    async def add_workflow(session_id: str, workflow: Workflow)
```

## 🔗 Dependencies

### Core Dependencies
- `playwright`: Browser automation
- `selenium`: Alternative browser backend
- `asyncio`: Asynchronous programming
- `aiofiles`: Async file operations
- `cryptography`: Encryption and security
- `sqlite3`: Database operations
- `yaml`: Configuration parsing

### ML/AI Dependencies
- `nltk`: Natural language processing
- `spacy`: Advanced NLP
- `transformers`: ML model inference
- `torch`: Deep learning framework
- `opencv-python`: Computer vision
- `pillow`: Image processing
- `numpy`: Numerical computing

### Optional Dependencies
- `redis`: High-performance caching
- `prometheus_client`: Metrics collection
- `sentry-sdk`: Error tracking
- `psutil`: System resource monitoring

## 🐛 Troubleshooting

### Common Issues

1. **Browser not launching**
   ```bash
   # Install browser dependencies
   playwright install
   # Or for system browsers
   apt-get install chromium-browser firefox
   ```

2. **Permission denied errors**
   ```bash
   # Fix permissions
   chmod +x spectra_data/
   chmod 600 spectra_data/.session_key
   ```

3. **Memory issues**
   ```yaml
   # Reduce memory usage in config
   max_memory_usage: 2048
   max_concurrent_sessions: 5
   cleanup_interval: 60
   ```

4. **SSL certificate errors**
   ```python
   # Disable SSL verification (development only)
   config.navigation_engine.verify_ssl = False
   ```

### Debug Mode
```python
# Enable debug logging
config = SpectraConfig(
    log_level="DEBUG",
    development={
        "debug_mode": True,
        "verbose_logging": True,
        "save_debug_info": True
    }
)
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

- **Marina Development Team** - Core architecture and implementation
- **AI Research Division** - Intent processing and ML models
- **Security Team** - Privacy and security features
- **QA Team** - Testing and quality assurance

## 🚀 Roadmap

### v1.1 (Next Release)
- [ ] VPN integration for geo-restriction bypass
- [ ] Enhanced CAPTCHA solving
- [ ] Multi-language support
- [ ] REST API interface

### v1.2 (Future)
- [ ] Distributed execution across multiple machines
- [ ] Real-time collaboration features
- [ ] Advanced AI model integration
- [ ] Mobile browser support

### v2.0 (Long-term)
- [ ] Self-improving AI agents
- [ ] Blockchain integration
- [ ] IoT device control
- [ ] AR/VR interface support

## 💬 Support

- **Documentation**: [docs.spectra.ai](https://docs.spectra.ai)
- **Issues**: [GitHub Issues](https://github.com/marina/spectra/issues)
- **Discussions**: [GitHub Discussions](https://github.com/marina/spectra/discussions)
- **Email**: support@spectra.ai

---

<div align="center">
<p><strong>🌐 Spectra - Autonomous browsing for the future</strong></p>
<p>Made with ❤️ by the Marina Team</p>
</div>
