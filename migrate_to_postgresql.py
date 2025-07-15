#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL for Telegram Analytics

This script helps migrate your existing SQLite data to PostgreSQL.
Make sure to:
1. Install PostgreSQL and create the database
2. Run setup_postgresql.sql to create tables
3. Update your .env file with correct PostgreSQL credentials
4. Install required packages: pip install psycopg2-binary
"""

import sqlite3
import psycopg2
import os
from dotenv import load_dotenv
import logging
from typing import List, Tuple

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_sqlite_connection(db_path: str) -> sqlite3.Connection:
    """Connect to SQLite database"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to SQLite: {e}")
        raise

def get_postgresql_connection() -> psycopg2.extensions.connection:
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'telegram_warehouse'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD')
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise

def migrate_table(sqlite_conn: sqlite3.Connection, 
                 pg_conn: psycopg2.extensions.connection,
                 table_name: str,
                 columns: List[str],
                 batch_size: int = 1000) -> int:
    """Migrate data from SQLite table to PostgreSQL table"""
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get total count
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = sqlite_cursor.fetchone()[0]
    
    if total_rows == 0:
        logger.info(f"No data found in {table_name}")
        return 0
    
    logger.info(f"Migrating {total_rows} rows from {table_name}")
    
    # Clear existing data in PostgreSQL table
    pg_cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
    
    # Prepare insert statement
    placeholders = ','.join(['%s'] * len(columns))
    insert_sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
    
    # Fetch and insert data in batches
    offset = 0
    migrated_rows = 0
    
    while offset < total_rows:
        # Fetch batch from SQLite
        sqlite_cursor.execute(
            f"SELECT {','.join(columns)} FROM {table_name} LIMIT {batch_size} OFFSET {offset}"
        )
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            break
            
        # Convert rows to tuples
        data_tuples = [tuple(row) for row in rows]
        
        # Insert batch into PostgreSQL
        pg_cursor.executemany(insert_sql, data_tuples)
        
        migrated_rows += len(rows)
        offset += batch_size
        
        logger.info(f"Migrated {migrated_rows}/{total_rows} rows from {table_name}")
    
    pg_conn.commit()
    return migrated_rows

def main():
    """Main migration function"""
    
    # Database paths
    sqlite_db_path = "telegram_data.db"
    
    if not os.path.exists(sqlite_db_path):
        logger.error(f"SQLite database not found: {sqlite_db_path}")
        return
    
    try:
        # Connect to databases
        logger.info("Connecting to databases...")
        sqlite_conn = get_sqlite_connection(sqlite_db_path)
        pg_conn = get_postgresql_connection()
        
        # Define tables and their columns to migrate
        tables_to_migrate = {
            'telegram_channels': [
                'id', 'username', 'title', 'about', 'participants_count',
                'is_broadcast', 'is_megagroup', 'created_date', 'scraped_at'
            ],
            'telegram_messages': [
                'id', 'channel_username', 'sender_id', 'text', 'date',
                'sender_username', 'sender_first_name', 'sender_last_name',
                'views', 'forwards', 'replies', 'is_reply', 'reply_to_msg_id',
                'has_media', 'media_type', 'media_file_path', 'raw_data'
            ],
            'business_info': [
                'id', 'channel_username', 'message_id', 'business_name',
                'phone_number', 'service_type', 'location', 'extracted_at'
            ],
            'media_files': [
                'id', 'channel_username', 'message_id', 'file_path',
                'media_type', 'file_size', 'created_at'
            ],
            'detected_objects': [
                'id', 'message_id', 'media_file_id', 'object_class',
                'confidence', 'bbox_x', 'bbox_y', 'bbox_width',
                'bbox_height', 'created_at'
            ]
        }
        
        # Migrate each table
        total_migrated = 0
        for table_name, columns in tables_to_migrate.items():
            try:
                migrated = migrate_table(sqlite_conn, pg_conn, table_name, columns)
                total_migrated += migrated
                logger.info(f"Successfully migrated {migrated} rows from {table_name}")
            except Exception as e:
                logger.error(f"Failed to migrate {table_name}: {e}")
                continue
        
        logger.info(f"Migration completed! Total rows migrated: {total_migrated}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        # Close connections
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    main()