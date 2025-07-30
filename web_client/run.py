#!/usr/bin/env python3
"""
Marina Web Client Startup Script

This script starts the Marina web client with proper configuration and logging.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import app

def setup_logging(debug=False):
    """Set up logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('marina_web_client.log')
        ]
    )

def main():
    parser = argparse.ArgumentParser(description='Marina Web Client')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--ssl', action='store_true', help='Enable SSL (requires cert files)')
    parser.add_argument('--cert', help='SSL certificate file')
    parser.add_argument('--key', help='SSL private key file')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Marina Web Client")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Debug: {args.debug}")
    
    # Configure Flask app
    app.config['DEBUG'] = args.debug
    
    # SSL context
    ssl_context = None
    if args.ssl:
        if args.cert and args.key:
            ssl_context = (args.cert, args.key)
            logger.info("SSL enabled with provided certificate files")
        else:
            ssl_context = 'adhoc'
            logger.info("SSL enabled with adhoc certificate")
    
    try:
        # Start the Flask application
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            ssl_context=ssl_context,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down Marina Web Client")
    except Exception as e:
        logger.error(f"Failed to start Marina Web Client: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
