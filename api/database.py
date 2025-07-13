#!/usr/bin/env python3
"""
Database configuration and session management for the FastAPI application.

This module provides database connectivity and session management
using SQLAlchemy with support for both PostgreSQL and SQLite.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/telegram_analytics.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Import models after Base is defined
try:
    from src.database.models import (
        TelegramChannel, TelegramMessage, MediaFile, 
        DetectedObject, BusinessInfo
    )
except ImportError:
    logging.warning("Could not import models from src.database.models")
    # Define basic models here if needed
    pass

# Database dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that provides a database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database tables
def init_db() -> None:
    """
    Initialize the database by creating all tables.
    """
    try:
        # Ensure data directory exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logging.info("✅ Database tables created successfully")
        
        # Log database file location for SQLite
        if "sqlite" in DATABASE_URL:
            db_file = DATABASE_URL.replace("sqlite:///", "")
            logging.info(f"📁 Database file: {Path(db_file).absolute()}")
            
    except Exception as e:
        logging.error(f"❌ Error creating database tables: {e}")
        raise

# Test database connection
def test_db_connection() -> bool:
    """
    Test the database connection.
    
    Returns:
        bool: True if connection is successful
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        logging.error(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the database connection
    test_db_connection()
    init_db()