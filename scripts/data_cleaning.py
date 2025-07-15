#!/usr/bin/env python3
"""
Data Cleaning and Processing for Telegram Data

This script cleans and processes raw Telegram data, extracting business information,
standardizing formats, and preparing data for database insertion.

Enhanced version based on Kara-Solutions implementation.
"""

import os
import sys
import json
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime
import argparse
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlalchemy.orm import Session
from src.database.config import db_config
from src.database.models import TelegramChannel, TelegramMessage, MediaFile, BusinessInfo
from api.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_cleaning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BusinessExtraction:
    """Data class for extracted business information"""
    business_name: Optional[str] = None
    product_name: Optional[str] = None
    price: Optional[str] = None
    contact_info: Optional[str] = None
    address: Optional[str] = None
    opening_hours: Optional[str] = None
    delivery_info: Optional[str] = None

class TelegramDataCleaner:
    """
    Comprehensive data cleaning and processing for Telegram data.
    """
    
    def __init__(self, raw_data_path: str = "./data/raw/telegram_messages"):
        """
        Initialize the data cleaner.
        
        Args:
            raw_data_path: Path to raw Telegram data files
        """
        self.raw_data_path = Path(raw_data_path)
        self.db = db_config.get_session()
        
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)
        
        # Business extraction patterns
        self.business_patterns = {
            'phone': re.compile(r'(?:\+251|0)[79]\d{8}|\b\d{10}\b'),
            'price': re.compile(r'(?:ብር|birr|ETB|\$)\s*\d+(?:[.,]\d+)?|\d+(?:[.,]\d+)?\s*(?:ብር|birr|ETB|\$)', re.IGNORECASE),
            'address': re.compile(r'(?:አዲስ\s*አበባ|addis\s*ababa|ቦሌ|bole|ፒያሳ|piassa|መርካቶ|mercato)', re.IGNORECASE),
            'time': re.compile(r'\d{1,2}:\d{2}(?:\s*(?:AM|PM|ጠዋት|ማታ))?', re.IGNORECASE),
            'delivery': re.compile(r'(?:delivery|ዴሊቨሪ|መላክ|ማድረስ)', re.IGNORECASE)
        }
        
        logger.info(f"🔧 Initialized TelegramDataCleaner with data path: {raw_data_path}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep Amharic
        text = re.sub(r'[^\w\s\u1200-\u137F.,!?@#$%&*()\-+=<>\[\]{}|;:\'"\n]', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def extract_business_info(self, text: str) -> BusinessExtraction:
        """
        Extract business information from message text.
        
        Args:
            text: Message text to analyze
            
        Returns:
            BusinessExtraction object with extracted information
        """
        if not text:
            return BusinessExtraction()
        
        extraction = BusinessExtraction()
        
        # Extract phone numbers
        phone_matches = self.business_patterns['phone'].findall(text)
        if phone_matches:
            extraction.contact_info = ', '.join(phone_matches)
        
        # Extract prices
        price_matches = self.business_patterns['price'].findall(text)
        if price_matches:
            extraction.price = ', '.join(price_matches)
        
        # Extract addresses
        address_matches = self.business_patterns['address'].findall(text)
        if address_matches:
            extraction.address = ', '.join(address_matches)
        
        # Extract opening hours
        time_matches = self.business_patterns['time'].findall(text)
        if time_matches:
            extraction.opening_hours = ', '.join(time_matches)
        
        # Extract delivery information
        if self.business_patterns['delivery'].search(text):
            extraction.delivery_info = "Delivery available"
        
        # Try to extract business/product names (simple heuristics)
        lines = text.split('\n')
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            if len(line) > 5 and len(line) < 100:  # Reasonable length
                if not extraction.business_name and any(char.isalpha() for char in line):
                    extraction.business_name = line
                elif not extraction.product_name and extraction.business_name != line:
                    extraction.product_name = line
        
        return extraction
    
    def process_json_file(self, json_file_path: Path) -> Tuple[Dict, List[Dict], List[Dict]]:
        """
        Process a single JSON file containing Telegram data.
        
        Args:
            json_file_path: Path to the JSON file
            
        Returns:
            Tuple of (channel_info, messages_data, media_data)
        """
        logger.info(f"📄 Processing JSON file: {json_file_path.name}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract channel information
            channel_info = {
                'channel_name': data.get('name', json_file_path.stem),
                'channel_url': f"https://t.me/{data.get('name', json_file_path.stem)}",
                'channel_id': str(data.get('id', '')),
                'title': data.get('name', ''),
                'description': data.get('about', ''),
                'participants_count': data.get('participants_count', 0)
            }
            
            messages_data = []
            media_data = []
            
            # Process messages
            for msg in data.get('messages', []):
                try:
                    # Clean message text
                    message_text = ''
                    if 'text' in msg:
                        if isinstance(msg['text'], str):
                            message_text = self.clean_text(msg['text'])
                        elif isinstance(msg['text'], list):
                            # Handle text entities
                            text_parts = []
                            for part in msg['text']:
                                if isinstance(part, str):
                                    text_parts.append(part)
                                elif isinstance(part, dict) and 'text' in part:
                                    text_parts.append(part['text'])
                            message_text = self.clean_text(' '.join(text_parts))
                    
                    # Parse date
                    date_str = msg.get('date', '')
                    try:
                        if 'T' in date_str:
                            message_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        else:
                            message_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    except:
                        message_date = datetime.utcnow()
                    
                    # Determine media presence
                    has_media = bool(msg.get('photo') or msg.get('video') or msg.get('document'))
                    media_type = None
                    
                    if msg.get('photo'):
                        media_type = 'photo'
                    elif msg.get('video'):
                        media_type = 'video'
                    elif msg.get('document'):
                        media_type = 'document'
                    
                    message_data = {
                        'message_id': msg.get('id', 0),
                        'sender_id': str(msg.get('from_id', '')),
                        'message_text': message_text,
                        'date': message_date,
                        'views': msg.get('views', 0),
                        'forwards': msg.get('forwards', 0),
                        'replies': msg.get('replies', {}).get('replies', 0) if msg.get('replies') else 0,
                        'is_reply': bool(msg.get('reply_to_message_id')),
                        'reply_to_msg_id': msg.get('reply_to_message_id'),
                        'has_media': has_media,
                        'media_type': media_type
                    }
                    
                    messages_data.append(message_data)
                    
                    # Process media files
                    if has_media:
                        media_info = msg.get('photo') or msg.get('video') or msg.get('document')
                        if media_info:
                            # Generate file path (this would be set during actual file download)
                            file_name = f"{channel_info['channel_name']}_{msg.get('id', 0)}"
                            if msg.get('photo'):
                                file_name += ".jpg"
                            elif msg.get('video'):
                                file_name += ".mp4"
                            else:
                                file_name += ".file"
                            
                            media_file_data = {
                                'message_id': msg.get('id', 0),
                                'file_name': file_name,
                                'file_path': f"./data/raw/media/{channel_info['channel_name']}/{file_name}",
                                'file_size': media_info.get('file_size', 0) if isinstance(media_info, dict) else 0,
                                'file_type': media_type,
                                'mime_type': media_info.get('mime_type', '') if isinstance(media_info, dict) else '',
                                'width': media_info.get('width', 0) if isinstance(media_info, dict) else 0,
                                'height': media_info.get('height', 0) if isinstance(media_info, dict) else 0,
                                'duration': media_info.get('duration', 0.0) if isinstance(media_info, dict) else 0.0
                            }
                            
                            media_data.append(media_file_data)
                
                except Exception as e:
                    logger.warning(f"⚠️ Error processing message {msg.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Processed {len(messages_data)} messages and {len(media_data)} media files")
            return channel_info, messages_data, media_data
            
        except Exception as e:
            logger.error(f"❌ Error processing JSON file {json_file_path}: {e}")
            return {}, [], []
    
    def process_csv_file(self, csv_file_path: Path) -> List[Dict]:
        """
        Process a CSV file containing cleaned Telegram data.
        
        Args:
            csv_file_path: Path to the CSV file
            
        Returns:
            List of processed message data
        """
        logger.info(f"📄 Processing CSV file: {csv_file_path.name}")
        
        try:
            df = pd.read_csv(csv_file_path)
            
            messages_data = []
            for _, row in df.iterrows():
                try:
                    # Parse date
                    try:
                        message_date = pd.to_datetime(row.get('date', datetime.utcnow()))
                    except:
                        message_date = datetime.utcnow()
                    
                    message_data = {
                        'message_text': self.clean_text(str(row.get('text', ''))),
                        'date': message_date,
                        'sender_id': str(row.get('sender', '')),
                        'views': int(row.get('views', 0)) if pd.notna(row.get('views')) else 0,
                        'forwards': int(row.get('forwards', 0)) if pd.notna(row.get('forwards')) else 0,
                        'replies': int(row.get('replies', 0)) if pd.notna(row.get('replies')) else 0,
                        'has_media': bool(row.get('has_media', False)),
                        'media_type': row.get('media_type') if pd.notna(row.get('media_type')) else None
                    }
                    
                    messages_data.append(message_data)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error processing CSV row: {e}")
                    continue
            
            logger.info(f"✅ Processed {len(messages_data)} messages from CSV")
            return messages_data
            
        except Exception as e:
            logger.error(f"❌ Error processing CSV file {csv_file_path}: {e}")
            return []
    
    def save_to_database(self, channel_info: Dict, messages_data: List[Dict], media_data: List[Dict]) -> bool:
        """
        Save processed data to the database.
        
        Args:
            channel_info: Channel information
            messages_data: List of message data
            media_data: List of media file data
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"💾 Saving data to database for channel: {channel_info.get('channel_name', 'Unknown')}")
            
            # Create or get channel
            existing_channel = self.db.query(TelegramChannel).filter(
                TelegramChannel.channel_name == channel_info['channel_name']
            ).first()
            
            if existing_channel:
                channel = existing_channel
                logger.info(f"📍 Using existing channel: {channel.channel_name}")
            else:
                channel = TelegramChannel(**channel_info)
                self.db.add(channel)
                self.db.commit()
                self.db.refresh(channel)
                logger.info(f"➕ Created new channel: {channel.channel_name}")
            
            # Save messages
            saved_messages = 0
            for msg_data in messages_data:
                try:
                    # Check if message already exists
                    existing_msg = self.db.query(TelegramMessage).filter(
                        TelegramMessage.message_id == msg_data['message_id'],
                        TelegramMessage.channel_id == channel.id
                    ).first()
                    
                    if not existing_msg:
                        msg_data['channel_id'] = channel.id
                        message = TelegramMessage(**msg_data)
                        self.db.add(message)
                        
                        # Extract and save business information
                        if msg_data.get('message_text'):
                            business_info = self.extract_business_info(msg_data['message_text'])
                            if any([business_info.business_name, business_info.product_name, 
                                   business_info.price, business_info.contact_info]):
                                business_data = BusinessInfo(
                                    message_id=message.id,
                                    business_name=business_info.business_name,
                                    product_name=business_info.product_name,
                                    price=business_info.price,
                                    contact_info=business_info.contact_info,
                                    address=business_info.address,
                                    opening_hours=business_info.opening_hours,
                                    delivery_info=business_info.delivery_info
                                )
                                self.db.add(business_data)
                        
                        saved_messages += 1
                
                except Exception as e:
                    logger.warning(f"⚠️ Error saving message: {e}")
                    continue
            
            # Save media files
            saved_media = 0
            for media_data_item in media_data:
                try:
                    # Find the corresponding message
                    message = self.db.query(TelegramMessage).filter(
                        TelegramMessage.message_id == media_data_item['message_id'],
                        TelegramMessage.channel_id == channel.id
                    ).first()
                    
                    if message:
                        # Check if media file already exists
                        existing_media = self.db.query(MediaFile).filter(
                            MediaFile.message_id == message.id,
                            MediaFile.file_name == media_data_item['file_name']
                        ).first()
                        
                        if not existing_media:
                            media_data_item['message_id'] = message.id
                            media_file = MediaFile(**media_data_item)
                            self.db.add(media_file)
                            saved_media += 1
                
                except Exception as e:
                    logger.warning(f"⚠️ Error saving media file: {e}")
                    continue
            
            self.db.commit()
            
            logger.info(f"✅ Saved {saved_messages} messages and {saved_media} media files")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving to database: {e}")
            self.db.rollback()
            return False
    
    def process_all_files(self) -> Dict[str, int]:
        """
        Process all data files in the raw data directory.
        
        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"🚀 Starting data cleaning process...")
        
        stats = {
            'files_processed': 0,
            'channels_created': 0,
            'messages_saved': 0,
            'media_files_saved': 0,
            'errors': 0
        }
        
        if not self.raw_data_path.exists():
            logger.error(f"❌ Raw data path does not exist: {self.raw_data_path}")
            return stats
        
        # Process JSON files
        json_files = list(self.raw_data_path.glob('*.json'))
        for json_file in json_files:
            try:
                channel_info, messages_data, media_data = self.process_json_file(json_file)
                
                if channel_info and messages_data:
                    if self.save_to_database(channel_info, messages_data, media_data):
                        stats['files_processed'] += 1
                        stats['channels_created'] += 1
                        stats['messages_saved'] += len(messages_data)
                        stats['media_files_saved'] += len(media_data)
                    else:
                        stats['errors'] += 1
                else:
                    stats['errors'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing {json_file}: {e}")
                stats['errors'] += 1
        
        # Process CSV files
        csv_files = list(self.raw_data_path.glob('*.csv'))
        for csv_file in csv_files:
            try:
                messages_data = self.process_csv_file(csv_file)
                
                if messages_data:
                    # Create a generic channel for CSV data
                    channel_info = {
                        'channel_name': csv_file.stem,
                        'channel_url': f"https://t.me/{csv_file.stem}",
                        'channel_id': csv_file.stem,
                        'title': csv_file.stem.replace('_', ' ').title(),
                        'description': f"Data imported from {csv_file.name}",
                        'participants_count': 0
                    }
                    
                    if self.save_to_database(channel_info, messages_data, []):
                        stats['files_processed'] += 1
                        stats['channels_created'] += 1
                        stats['messages_saved'] += len(messages_data)
                    else:
                        stats['errors'] += 1
                else:
                    stats['errors'] += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing {csv_file}: {e}")
                stats['errors'] += 1
        
        logger.info(f"✅ Data cleaning completed!")
        logger.info(f"📊 Statistics: {stats}")
        
        return stats
    
    def export_cleaned_data(self, output_dir: str = "data/processed") -> bool:
        """
        Export cleaned data to CSV files.
        
        Args:
            output_dir: Directory to save cleaned data
            
        Returns:
            bool: True if successful
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📤 Exporting cleaned data to {output_dir}")
            
            # Export channels
            channels_query = """
            SELECT * FROM telegram_channels
            ORDER BY created_at
            """
            channels_df = pd.read_sql_query(channels_query, self.db.bind)
            channels_df.to_csv(output_path / "cleaned_channels.csv", index=False)
            
            # Export messages
            messages_query = """
            SELECT 
                tm.*,
                tc.channel_name
            FROM telegram_messages tm
            JOIN telegram_channels tc ON tm.channel_id = tc.id
            ORDER BY tm.date
            """
            messages_df = pd.read_sql_query(messages_query, self.db.bind)
            messages_df.to_csv(output_path / "cleaned_messages.csv", index=False)
            
            # Export business information
            business_query = """
            SELECT 
                bi.*,
                tc.channel_name,
                tm.message_text,
                tm.date as message_date
            FROM business_info bi
            JOIN telegram_messages tm ON bi.message_id = tm.id
            JOIN telegram_channels tc ON tm.channel_id = tc.id
            ORDER BY bi.extracted_at
            """
            business_df = pd.read_sql_query(business_query, self.db.bind)
            business_df.to_csv(output_path / "extracted_businesses.csv", index=False)
            
            logger.info(f"✅ Exported cleaned data to {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error exporting cleaned data: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Clean and process Telegram data")
    parser.add_argument("--input", default="./data/raw/telegram_messages", help="Input directory path")
    parser.add_argument("--export", action="store_true", help="Export cleaned data to CSV")
    parser.add_argument("--output", default="data/processed", help="Output directory for exports")
    
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    # Create cleaner
    cleaner = TelegramDataCleaner(raw_data_path=args.input)
    
    try:
        # Process all files
        stats = cleaner.process_all_files()
        
        print("\n📊 DATA CLEANING RESULTS")
        print("=" * 40)
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Export if requested
        if args.export:
            cleaner.export_cleaned_data(args.output)
        
    finally:
        cleaner.close()

if __name__ == "__main__":
    main()