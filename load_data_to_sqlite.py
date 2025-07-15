#!/usr/bin/env python3
"""
Load Telegram JSON data into SQLite database for dbt processing

This script loads the scraped JSON data into SQLite tables that can be processed by dbt.
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramDataLoader:
    """Load Telegram JSON data into SQLite database"""
    
    def __init__(self, db_path: str = "telegram_data.db"):
        self.db_path = db_path
        self.data_dir = Path("data/raw")
        
    def create_tables(self) -> None:
        """Create the required tables in SQLite"""
        logger.info("🗄️ Creating database tables...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create telegram_channels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telegram_channels (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    title TEXT,
                    about TEXT,
                    participants_count INTEGER,
                    is_broadcast BOOLEAN,
                    is_megagroup BOOLEAN,
                    created_date TIMESTAMP,
                    scraped_at TIMESTAMP
                )
            """)
            
            # Create telegram_messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telegram_messages (
                    id INTEGER,
                    channel_username TEXT,
                    date TIMESTAMP,
                    text TEXT,
                    sender_id INTEGER,
                    sender_username TEXT,
                    sender_first_name TEXT,
                    sender_last_name TEXT,
                    views INTEGER,
                    forwards INTEGER,
                    replies INTEGER,
                    is_reply BOOLEAN,
                    reply_to_msg_id INTEGER,
                    has_media BOOLEAN,
                    media_type TEXT,
                    media_file_path TEXT,
                    raw_data TEXT,
                    PRIMARY KEY (id, channel_username)
                )
            """)
            
            # Create business_info table (extracted from messages)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS business_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_username TEXT,
                    message_id INTEGER,
                    business_name TEXT,
                    phone_number TEXT,
                    service_type TEXT,
                    location TEXT,
                    extracted_at TIMESTAMP,
                    FOREIGN KEY (message_id, channel_username) REFERENCES telegram_messages(id, channel_username)
                )
            """)
            
            # Create media_files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS media_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_username TEXT,
                    message_id INTEGER,
                    file_path TEXT,
                    media_type TEXT,
                    file_size INTEGER,
                    created_at TIMESTAMP,
                    FOREIGN KEY (message_id, channel_username) REFERENCES telegram_messages(id, channel_username)
                )
            """)
            
            conn.commit()
            logger.info("✅ Database tables created successfully")
    
    def extract_business_info(self, text: str, channel: str, msg_id: int) -> List[Dict[str, Any]]:
        """Extract business information from message text"""
        business_records = []
        
        # Simple extraction logic for demo purposes
        if any(keyword in text.lower() for keyword in ['medical', 'hospital', 'clinic', 'pharmacy', 'health']):
            # Extract phone numbers
            import re
            phone_pattern = r'\+?251[\-\s]?\d{2}[\-\s]?\d{3}[\-\s]?\d{4}'
            phones = re.findall(phone_pattern, text)
            
            # Determine service type
            service_type = 'general_medical'
            if 'pharmacy' in text.lower():
                service_type = 'pharmacy'
            elif 'emergency' in text.lower():
                service_type = 'emergency'
            elif 'vaccination' in text.lower():
                service_type = 'vaccination'
            elif 'checkup' in text.lower():
                service_type = 'checkup'
            
            business_name = channel.replace('_', ' ').title()
            
            for phone in phones:
                business_records.append({
                    'channel_username': channel,
                    'message_id': msg_id,
                    'business_name': business_name,
                    'phone_number': phone,
                    'service_type': service_type,
                    'location': 'Addis Ababa',  # Default for demo
                    'extracted_at': datetime.utcnow().isoformat()
                })
        
        return business_records
    
    def load_json_files(self) -> None:
        """Load all JSON files from the data directory"""
        logger.info("📊 Loading JSON files into database...")
        
        json_files = list(self.data_dir.rglob("*.json"))
        logger.info(f"Found {len(json_files)} JSON files to process")
        
        channels_data = {}
        messages_data = []
        business_data = []
        media_data = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                channel_info = data['channel_info']
                channel_username = channel_info['username']
                
                # Store unique channel info
                if channel_username not in channels_data:
                    channels_data[channel_username] = channel_info
                
                # Process messages
                for message in data['messages']:
                    message['channel_username'] = channel_username
                    message['raw_data'] = json.dumps(message['raw_data'])
                    messages_data.append(message)
                    
                    # Extract business info
                    business_records = self.extract_business_info(
                        message['text'], channel_username, message['id']
                    )
                    business_data.extend(business_records)
                    
                    # Process media files
                    if message['has_media'] and message['media_file_path']:
                        media_data.append({
                            'channel_username': channel_username,
                            'message_id': message['id'],
                            'file_path': message['media_file_path'],
                            'media_type': message['media_type'],
                            'file_size': 1024,  # Demo value
                            'created_at': message['date']
                        })
                
                logger.info(f"✅ Processed {json_file.name}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {json_file}: {e}")
        
        # Insert data into database
        self._insert_data(channels_data, messages_data, business_data, media_data)
    
    def _insert_data(self, channels_data: Dict, messages_data: List, 
                    business_data: List, media_data: List) -> None:
        """Insert data into SQLite tables"""
        logger.info("💾 Inserting data into database...")
        
        with sqlite3.connect(self.db_path) as conn:
            # Insert channels
            for channel_info in channels_data.values():
                conn.execute("""
                    INSERT OR REPLACE INTO telegram_channels 
                    (id, username, title, about, participants_count, is_broadcast, 
                     is_megagroup, created_date, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    channel_info['id'], channel_info['username'], channel_info['title'],
                    channel_info['about'], channel_info['participants_count'],
                    channel_info['is_broadcast'], channel_info['is_megagroup'],
                    channel_info['created_date'], channel_info['scraped_at']
                ))
            
            # Insert messages
            for message in messages_data:
                conn.execute("""
                    INSERT OR REPLACE INTO telegram_messages 
                    (id, channel_username, date, text, sender_id, sender_username,
                     sender_first_name, sender_last_name, views, forwards, replies,
                     is_reply, reply_to_msg_id, has_media, media_type, media_file_path, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    message['id'], message['channel_username'], message['date'],
                    message['text'], message['sender_id'], message['sender_username'],
                    message['sender_first_name'], message['sender_last_name'],
                    message['views'], message['forwards'], message['replies'],
                    message['is_reply'], message['reply_to_msg_id'], message['has_media'],
                    message['media_type'], message['media_file_path'], message['raw_data']
                ))
            
            # Insert business info
            for business in business_data:
                conn.execute("""
                    INSERT INTO business_info 
                    (channel_username, message_id, business_name, phone_number,
                     service_type, location, extracted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    business['channel_username'], business['message_id'],
                    business['business_name'], business['phone_number'],
                    business['service_type'], business['location'],
                    business['extracted_at']
                ))
            
            # Insert media files
            for media in media_data:
                conn.execute("""
                    INSERT INTO media_files 
                    (channel_username, message_id, file_path, media_type, file_size, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    media['channel_username'], media['message_id'],
                    media['file_path'], media['media_type'],
                    media['file_size'], media['created_at']
                ))
            
            conn.commit()
        
        logger.info(f"✅ Inserted {len(channels_data)} channels")
        logger.info(f"✅ Inserted {len(messages_data)} messages")
        logger.info(f"✅ Inserted {len(business_data)} business records")
        logger.info(f"✅ Inserted {len(media_data)} media files")
    
    def get_summary_stats(self) -> Dict[str, int]:
        """Get summary statistics from the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            cursor.execute("SELECT COUNT(*) FROM telegram_channels")
            stats['channels'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM telegram_messages")
            stats['messages'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM business_info")
            stats['business_records'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM media_files")
            stats['media_files'] = cursor.fetchone()[0]
            
            return stats

def main():
    """Main function"""
    print("🚀 Loading Telegram Data into SQLite")
    print("=" * 40)
    
    try:
        loader = TelegramDataLoader()
        
        # Create tables
        loader.create_tables()
        
        # Load JSON data
        loader.load_json_files()
        
        # Get summary
        stats = loader.get_summary_stats()
        
        print("\n📊 DATA LOADING SUMMARY:")
        print(f"   • Channels: {stats['channels']}")
        print(f"   • Messages: {stats['messages']}")
        print(f"   • Business Records: {stats['business_records']}")
        print(f"   • Media Files: {stats['media_files']}")
        
        print("\n✅ Data loading completed successfully!")
        print("\n🔧 Next step: Run 'dbt run' to execute transformations")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())