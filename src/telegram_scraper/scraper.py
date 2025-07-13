import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, MessageMediaVideo
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from sqlalchemy.orm import Session
from loguru import logger
import aiofiles
from dotenv import load_dotenv

from ..database.config import get_db, db_config
from ..database.models import TelegramChannel, TelegramMessage, MediaFile, BusinessInfo

load_dotenv()

class TelegramScraper:
    """Telegram scraper for collecting data from medical business channels"""
    
    def __init__(self):
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.phone_number = os.getenv('PHONE_NUMBER')
        self.data_path = os.getenv('DATA_LAKE_PATH', './data')
        
        if not all([self.api_id, self.api_hash, self.phone_number]):
            raise ValueError("Missing required Telegram API credentials in .env file")
        
        self.client = TelegramClient('telegram_scraper', self.api_id, self.api_hash)
        self.channels = [
            'CheMed123',
            'lobelia4cosmetics', 
            'tikvahpharma',
            'zoepharmacy'
        ]
        
        # Ensure data directories exist
        os.makedirs(f"{self.data_path}/raw/telegram_messages", exist_ok=True)
        os.makedirs(f"{self.data_path}/raw/media", exist_ok=True)
    
    async def start_client(self):
        """Start Telegram client and authenticate"""
        try:
            await self.client.start(phone=self.phone_number)
            logger.info("Telegram client started successfully")
            
            if not await self.client.is_user_authorized():
                logger.info("User not authorized, requesting code...")
                await self.client.send_code_request(self.phone_number)
                code = input('Enter the code you received: ')
                await self.client.sign_in(self.phone_number, code)
                
        except SessionPasswordNeededError:
            password = input('Two-factor authentication enabled. Please enter your password: ')
            await self.client.sign_in(password=password)
        except Exception as e:
            logger.error(f"Failed to start Telegram client: {e}")
            raise
    
    async def get_channel_info(self, channel_username: str) -> Optional[Dict[str, Any]]:
        """Get channel information"""
        try:
            entity = await self.client.get_entity(channel_username)
            return {
                'channel_name': channel_username,
                'channel_url': f'https://t.me/{channel_username}',
                'channel_id': str(entity.id),
                'title': getattr(entity, 'title', ''),
                'description': getattr(entity, 'about', ''),
                'participants_count': getattr(entity, 'participants_count', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get channel info for {channel_username}: {e}")
            return None
    
    async def save_media_file(self, message, media_dir: str) -> Optional[Dict[str, Any]]:
        """Download and save media file"""
        try:
            if not message.media:
                return None
            
            # Generate filename
            timestamp = message.date.strftime('%Y%m%d_%H%M%S')
            file_extension = ''
            file_type = 'unknown'
            
            if isinstance(message.media, MessageMediaPhoto):
                file_extension = '.jpg'
                file_type = 'image'
            elif isinstance(message.media, MessageMediaDocument):
                if message.media.document.mime_type:
                    if 'image' in message.media.document.mime_type:
                        file_type = 'image'
                        file_extension = '.jpg' if 'jpeg' in message.media.document.mime_type else '.png'
                    elif 'video' in message.media.document.mime_type:
                        file_type = 'video'
                        file_extension = '.mp4'
                    else:
                        file_type = 'document'
                        file_extension = '.bin'
            elif isinstance(message.media, MessageMediaVideo):
                file_type = 'video'
                file_extension = '.mp4'
            
            filename = f"{message.chat.username}_{message.id}_{timestamp}{file_extension}"
            file_path = os.path.join(media_dir, filename)
            
            # Download file
            await self.client.download_media(message.media, file_path)
            
            # Get file info
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            return {
                'file_name': filename,
                'file_path': file_path,
                'file_size': file_size,
                'file_type': file_type,
                'mime_type': getattr(message.media.document, 'mime_type', '') if hasattr(message.media, 'document') else ''
            }
            
        except Exception as e:
            logger.error(f"Failed to save media file: {e}")
            return None
    
    def extract_business_info(self, message_text: str) -> Dict[str, Any]:
        """Extract business information from message text using simple patterns"""
        import re
        
        business_info = {
            'business_name': None,
            'product_name': None,
            'price': None,
            'contact_info': None,
            'address': None,
            'opening_hours': None,
            'delivery_info': None
        }
        
        if not message_text:
            return business_info
        
        # Extract price patterns
        price_patterns = [
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:birr|ETB|br)',
            r'(?:price|ዋጋ)\s*:?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:ብር)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, message_text, re.IGNORECASE)
            if match:
                business_info['price'] = match.group(1)
                break
        
        # Extract contact information
        contact_patterns = [
            r'(?:call|contact|phone|tel)\s*:?\s*([+]?\d[\d\s\-\(\)]{8,})',
            r'([+]?251[\d\s\-]{8,})',
            r'(09\d{8})'
        ]
        
        for pattern in contact_patterns:
            match = re.search(pattern, message_text, re.IGNORECASE)
            if match:
                business_info['contact_info'] = match.group(1)
                break
        
        # Extract delivery information
        delivery_keywords = ['delivery', 'shipping', 'transport', 'መላክ', 'ማድረስ']
        for keyword in delivery_keywords:
            if keyword.lower() in message_text.lower():
                # Extract sentence containing delivery info
                sentences = message_text.split('.')
                for sentence in sentences:
                    if keyword.lower() in sentence.lower():
                        business_info['delivery_info'] = sentence.strip()
                        break
                break
        
        return business_info
    
    async def scrape_channel_messages(self, channel_username: str, limit: int = 100, days_back: int = 30) -> List[Dict[str, Any]]:
        """Scrape messages from a specific channel"""
        messages_data = []
        
        try:
            entity = await self.client.get_entity(channel_username)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            logger.info(f"Scraping messages from {channel_username} (last {days_back} days, limit: {limit})")
            
            async for message in self.client.iter_messages(entity, limit=limit, offset_date=end_date):
                if message.date < start_date:
                    break
                
                # Save media if present
                media_info = None
                if message.media:
                    media_dir = f"{self.data_path}/raw/media/{channel_username}"
                    os.makedirs(media_dir, exist_ok=True)
                    media_info = await self.save_media_file(message, media_dir)
                
                # Extract business information
                business_info = self.extract_business_info(message.text or '')
                
                message_data = {
                    'message_id': message.id,
                    'sender_id': str(message.sender_id) if message.sender_id else None,
                    'message_text': message.text,
                    'date': message.date,
                    'views': getattr(message, 'views', 0),
                    'forwards': getattr(message, 'forwards', 0),
                    'replies': getattr(message.replies, 'replies', 0) if message.replies else 0,
                    'is_reply': message.is_reply,
                    'reply_to_msg_id': message.reply_to_msg_id,
                    'has_media': bool(message.media),
                    'media_type': type(message.media).__name__ if message.media else None,
                    'media_info': media_info,
                    'business_info': business_info
                }
                
                messages_data.append(message_data)
                
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.1)
            
            logger.info(f"Scraped {len(messages_data)} messages from {channel_username}")
            
        except FloodWaitError as e:
            logger.warning(f"Rate limited for {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Failed to scrape messages from {channel_username}: {e}")
        
        return messages_data
    
    async def save_to_database(self, channel_info: Dict[str, Any], messages_data: List[Dict[str, Any]]):
        """Save scraped data to database"""
        db = db_config.get_session()
        
        try:
            # Save or update channel info
            channel = db.query(TelegramChannel).filter_by(channel_name=channel_info['channel_name']).first()
            
            if not channel:
                channel = TelegramChannel(**channel_info)
                db.add(channel)
                db.flush()  # Get the ID
            else:
                for key, value in channel_info.items():
                    setattr(channel, key, value)
                channel.updated_at = datetime.utcnow()
            
            db.commit()
            
            # Save messages
            for msg_data in messages_data:
                # Check if message already exists
                existing_msg = db.query(TelegramMessage).filter_by(
                    message_id=msg_data['message_id'],
                    channel_id=channel.id
                ).first()
                
                if existing_msg:
                    continue  # Skip existing messages
                
                # Create message record
                message = TelegramMessage(
                    message_id=msg_data['message_id'],
                    channel_id=channel.id,
                    sender_id=msg_data['sender_id'],
                    message_text=msg_data['message_text'],
                    date=msg_data['date'],
                    views=msg_data['views'],
                    forwards=msg_data['forwards'],
                    replies=msg_data['replies'],
                    is_reply=msg_data['is_reply'],
                    reply_to_msg_id=msg_data['reply_to_msg_id'],
                    has_media=msg_data['has_media'],
                    media_type=msg_data['media_type']
                )
                
                db.add(message)
                db.flush()  # Get the message ID
                
                # Save media file info
                if msg_data['media_info']:
                    media_file = MediaFile(
                        message_id=message.id,
                        **msg_data['media_info']
                    )
                    db.add(media_file)
                
                # Save business info
                business_info = msg_data['business_info']
                if any(business_info.values()):
                    business = BusinessInfo(
                        message_id=message.id,
                        **business_info
                    )
                    db.add(business)
            
            db.commit()
            logger.info(f"Saved {len(messages_data)} messages to database for channel {channel_info['channel_name']}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save data to database: {e}")
            raise
        finally:
            db.close()
    
    async def scrape_all_channels(self, limit: int = 100, days_back: int = 30):
        """Scrape all configured channels"""
        await self.start_client()
        
        try:
            for channel_username in self.channels:
                logger.info(f"Processing channel: {channel_username}")
                
                # Get channel info
                channel_info = await self.get_channel_info(channel_username)
                if not channel_info:
                    continue
                
                # Scrape messages
                messages_data = await self.scrape_channel_messages(channel_username, limit, days_back)
                
                # Save to database
                if messages_data:
                    await self.save_to_database(channel_info, messages_data)
                
                # Add delay between channels
                await asyncio.sleep(2)
            
            logger.info("Completed scraping all channels")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise
        finally:
            await self.client.disconnect()

# Convenience function for running the scraper
async def run_telegram_scraper(limit: int = 100, days_back: int = 30):
    """Run the Telegram scraper"""
    scraper = TelegramScraper()
    await scraper.scrape_all_channels(limit=limit, days_back=days_back)