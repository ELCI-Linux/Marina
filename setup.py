#!/usr/bin/env python3
"""
Setup script for Marina's Spectra - Autonomous Browser System
"""

from setuptools import setup, find_packages
import os

# Read version from __init__.py
version_file = os.path.join(os.path.dirname(__file__), 'spectra', '__init__.py')
with open(version_file, 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip('"\'')
            break
    else:
        version = "1.0.0"

# Read long description from README
readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_file):
    with open(readme_file, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = "Marina's Spectra - Autonomous Browser System"

# Define core dependencies (minimal for basic functionality)
core_deps = [
    # Core Browser Automation
    "playwright>=1.40.0",
    "selenium>=4.15.0",
    "undetected-chromedriver>=3.5.0",
    
    # Async Programming & Utilities
    "asyncio-throttle>=1.0.2",
    "aiofiles>=23.2.1",
    "aiohttp>=3.9.1",
    "uvloop>=0.19.0; sys_platform != 'win32'",
    
    # Core Dependencies (Required)
    "nltk>=3.8.1",
    "Pillow>=10.1.0",
    "numpy>=1.24.3",
    
    # Database & Storage
    "redis>=5.0.1",
    "psycopg2-binary>=2.9.9",
    "sqlalchemy>=2.0.23",
    
    # Security & Encryption
    "cryptography>=41.0.7",
    "keyring>=24.3.0",
    "argon2-cffi>=23.1.0",
    "bcrypt>=4.1.2",
    
    # Configuration & Serialization
    "PyYAML>=6.0.1",
    "python-dotenv>=1.0.0",
    "pydantic>=2.5.0",
    "marshmallow>=3.20.1",
    
    # HTTP & API
    "requests>=2.31.0",
    "httpx>=0.25.2",
    "urllib3>=2.1.0",
    
    # Monitoring & Metrics
    "prometheus-client>=0.19.0",
    "psutil>=5.9.6",
    "py-cpuinfo>=9.0.0",
    
    # Error Tracking & Logging
    "sentry-sdk>=1.38.0",
    "structlog>=23.2.0",
    "colorlog>=6.8.0",
    
    # Utility Libraries
    "tqdm>=4.66.1",
    "click>=8.1.7",
    "rich>=13.7.0",
    "python-dateutil>=2.8.2",
    "pytz>=2023.3",
    
    # Performance & Optimization
    "cachetools>=5.3.2",
    "diskcache>=5.6.3",
    
    # File Processing
    "python-magic>=0.4.27",
    "chardet>=5.2.0",
    
    # Web Scraping Utilities
    "beautifulsoup4>=4.12.2",
    "lxml>=4.9.3",
    "cssselect>=1.2.0",
    
    # Validation & Parsing
    "jsonschema>=4.20.0",
    "cerberus>=1.3.5",
    "python-slugify>=8.0.1",
]

# Define optional dependencies
ml_deps = [
    "spacy>=3.7.2",
    "transformers>=4.35.0",
    "torch>=2.1.0",
    "sentence-transformers>=2.2.2",
    "scikit-learn>=1.3.2",
    "joblib>=1.3.2",
    "xgboost>=2.0.2",
    "lightgbm>=4.1.0",
]

cv_deps = [
    "opencv-python>=4.8.1.78",
    "scikit-image>=0.22.0",
    "imagehash>=4.3.1",
]

ocr_deps = [
    "easyocr>=1.7.0",
    "pytesseract>=0.3.10",
    "pdf2image>=1.16.3",
]

audio_deps = [
    "whisper>=1.1.10",
    "librosa>=0.10.1",
    "soundfile>=0.12.1",
]

face_deps = [
    "face-recognition>=1.3.0",
    "dlib>=19.24.2",
]

dev_deps = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.1",
    "pytest-mock>=3.12.0",
    "pytest-cov>=4.1.0",
    "pytest-xdist>=3.5.0",
    "black>=23.11.0",
    "flake8>=6.1.0",
    "mypy>=1.7.1",
    "pre-commit>=3.6.0",
]

docs_deps = [
    "sphinx>=7.2.6",
    "sphinx-rtd-theme>=1.3.0",
    "myst-parser>=2.0.0",
]

all_deps = core_deps + ml_deps + cv_deps + ocr_deps + audio_deps + face_deps

setup(
    name="marina-spectra",
    version=version,
    description="Marina's Spectra - Autonomous Browser System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Marina Development Team",
    author_email="dev@marina.ai",
    url="https://github.com/marina-ai/spectra",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=core_deps,
    extras_require={
        "ml": ml_deps,
        "cv": cv_deps,
        "ocr": ocr_deps,
        "audio": audio_deps,
        "face": face_deps,
        "dev": dev_deps,
        "docs": docs_deps,
        "all": all_deps,
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="browser automation ai autonomous web scraping",
    entry_points={
        "console_scripts": [
            "spectra=spectra.spectra_core:main",
        ],
    },
)
