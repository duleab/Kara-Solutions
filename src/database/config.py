import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv
from loguru import logger
from .models import Base

# Load environment variables
load_dotenv()

class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///./telegram_data.db')
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _setup_database(self):
        """Setup database engine and session"""
        try:
            if self.database_url.startswith('sqlite'):
                # SQLite configuration
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=False
                )
            else:
                # PostgreSQL configuration
                self.engine = create_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False
                )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"Database configured successfully: {self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url}")
            
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise
    
    def create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_connection(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")

# Global database instance
db_config = DatabaseConfig()

def get_db():
    """Dependency for getting database session"""
    db = db_config.get_session()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with tables"""
    db_config.create_tables()
    logger.info("Database initialized successfully")