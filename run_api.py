#!/usr/bin/env python3
"""
Startup script for the Ethiopian Medical Business Telegram Analytics API

This script initializes the database and starts the FastAPI server.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from api.database import init_db, test_db_connection
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to start the API server
    """
    logger.info("🚀 Starting Ethiopian Medical Business Telegram Analytics API...")
    
    # Create necessary directories
    directories = [
        "data/raw/telegram_messages",
        "data/raw/media",
        "data/processed",
        "data/models",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Created directory: {directory}")
    
    # Initialize database
    logger.info("🗄️ Initializing database...")
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
        
        # Test database connection
        if test_db_connection():
            logger.info("✅ Database connection test passed")
        else:
            logger.error("❌ Database connection test failed")
            return
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return
    
    # Start the API server
    logger.info("🌐 Starting FastAPI server...")
    logger.info("📖 API Documentation will be available at: http://localhost:8000/docs")
    logger.info("🔍 Interactive API explorer at: http://localhost:8000/redoc")
    
    try:
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()