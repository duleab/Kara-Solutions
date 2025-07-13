#!/usr/bin/env python3
"""
Telegram Data Scraper

This script scrapes data from Telegram channels using the Telethon library.
It collects messages, media files, and metadata for analysis.

Enhanced version based on Kara-Solutions implementation.
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import argparse
from dataclasses import dataclass, asdict
import aiofiles
import aiohttp

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import (
        MessageMediaPhoto, MessageMediaDocument, MessageMediaVideo,
        PeerChannel, PeerUser, PeerChat
    )
    from telethon.errors import (
        SessionPasswordNeededError, FloodWaitError, 
        ChannelPrivateError, UsernameNotOccupiedError
    )
except ImportError:
    print("❌ Telethon not installed. Install with: pip install telethon")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ScrapingConfig:
    """Configuration for scraping parameters"""
    api_id: int
    api_hash: str
    phone_number: str
    session_name: str = "scraper_session"
    max_messages: int = 1000
    days_back: int = 30
    download_media: bool = True
    media_types: List[str] = None
    output_dir: str = "data/raw/telegram_messages"
    media_dir: str = "data/raw/media"
    
    def __post_init__(self):
        if self.media_types is None:
            self.media_types = ['photo', 'video', 'document']

@dataclass
class MessageData:
    """Data structure for scraped messages"""
    id: int
    date: datetime
    text: str
    sender_id: Optional[int]
    sender_username: Optional[str]
    sender_first_name: Optional[str]
    sender_last_name: Optional[str]
    views: Optional[int]
    forwards: Optional[int]
    replies: Optional[int]
    is_reply: bool
    reply_to_msg_id: Optional[int]
    has_media: bool
    media_type: Optional[str]
    media_file_path: Optional[str]
    raw_data: Dict[str, Any]

@dataclass
class ChannelData:
    """Data structure for channel information"""
    id: int
    username: str
    title: str
    about: Optional[str]
    participants_count: Optional[int]
    is_broadcast: bool
    is_megagroup: bool
    created_date: Optional[datetime]
    scraped_at: datetime
    messages: List[MessageData]

class TelegramScraper:
    """
    Comprehensive Telegram data scraper using Telethon.
    """
    
    def __init__(self, config: ScrapingConfig):
        """
        Initialize the Telegram scraper.
        
        Args:
            config: Scraping configuration
        """
        self.config = config
        self.client = None
        
        # Ensure directories exist
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.media_dir).mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        logger.info(f"🔧 Initialized TelegramScraper")
        logger.info(f"📁 Output directory: {self.config.output_dir}")
        logger.info(f"📁 Media directory: {self.config.media_dir}")
    
    async def initialize_client(self) -> bool:
        """
        Initialize and authenticate the Telegram client.
        
        Returns:
            bool: True if successful
        """
        try:
            logger.info("🔐 Initializing Telegram client...")
            
            self.client = TelegramClient(
                self.config.session_name,
                self.config.api_id,
                self.config.api_hash
            )
            
            await self.client.start(phone=self.config.phone_number)
            
            if not await self.client.is_user_authorized():
                logger.error("❌ User not authorized")
                return False
            
            me = await self.client.get_me()
            logger.info(f"✅ Authenticated as: {me.first_name} {me.last_name or ''}")
            
            return True
            
        except SessionPasswordNeededError:
            logger.error("❌ Two-factor authentication enabled. Please provide password.")
            return False
        except Exception as e:
            logger.error(f"❌ Error initializing client: {e}")
            return False
    
    async def get_channel_info(self, channel_username: str) -> Optional[ChannelData]:
        """
        Get information about a Telegram channel.
        
        Args:
            channel_username: Channel username (without @)
            
        Returns:
            ChannelData object or None if failed
        """
        try:
            logger.info(f"📡 Getting channel info for: @{channel_username}")
            
            entity = await self.client.get_entity(channel_username)
            
            # Get full channel info
            full_channel = await self.client.get_entity(entity)
            
            channel_data = ChannelData(
                id=entity.id,
                username=channel_username,
                title=entity.title,
                about=getattr(full_channel, 'about', None),
                participants_count=getattr(entity, 'participants_count', None),
                is_broadcast=getattr(entity, 'broadcast', False),
                is_megagroup=getattr(entity, 'megagroup', False),
                created_date=getattr(entity, 'date', None),
                scraped_at=datetime.utcnow(),
                messages=[]
            )
            
            logger.info(f"✅ Channel info retrieved: {channel_data.title}")
            logger.info(f"📊 Participants: {channel_data.participants_count}")
            
            return channel_data
            
        except UsernameNotOccupiedError:
            logger.error(f"❌ Channel @{channel_username} not found")
            return None
        except ChannelPrivateError:
            logger.error(f"❌ Channel @{channel_username} is private")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting channel info for @{channel_username}: {e}")
            return None
    
    async def download_media_file(self, message, channel_username: str) -> Optional[str]:
        """
        Download media file from a message.
        
        Args:
            message: Telethon message object
            channel_username: Channel username for organizing files
            
        Returns:
            str: Path to downloaded file or None if failed
        """
        try:
            if not message.media:
                return None
            
            # Create channel-specific media directory
            channel_media_dir = Path(self.config.media_dir) / channel_username
            channel_media_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine file extension
            file_ext = ".unknown"
            if isinstance(message.media, MessageMediaPhoto):
                file_ext = ".jpg"
            elif isinstance(message.media, MessageMediaVideo):
                file_ext = ".mp4"
            elif isinstance(message.media, MessageMediaDocument):
                if hasattr(message.media.document, 'mime_type'):
                    mime_type = message.media.document.mime_type
                    if 'image' in mime_type:
                        file_ext = ".jpg"
                    elif 'video' in mime_type:
                        file_ext = ".mp4"
                    elif 'audio' in mime_type:
                        file_ext = ".mp3"
                    else:
                        file_ext = ".file"
            
            # Generate filename
            filename = f"{channel_username}_{message.id}_{int(message.date.timestamp())}{file_ext}"
            file_path = channel_media_dir / filename
            
            # Download the file
            await self.client.download_media(message, file=str(file_path))
            
            logger.debug(f"📥 Downloaded media: {filename}")
            return str(file_path)
            
        except Exception as e:
            logger.warning(f"⚠️ Error downloading media for message {message.id}: {e}")
            return None
    
    def extract_message_data(self, message, media_file_path: Optional[str] = None) -> MessageData:
        """
        Extract data from a Telethon message object.
        
        Args:
            message: Telethon message object
            media_file_path: Path to downloaded media file
            
        Returns:
            MessageData object
        """
        # Extract sender information
        sender_id = None
        sender_username = None
        sender_first_name = None
        sender_last_name = None
        
        if message.sender:
            sender_id = message.sender.id
            sender_username = getattr(message.sender, 'username', None)
            sender_first_name = getattr(message.sender, 'first_name', None)
            sender_last_name = getattr(message.sender, 'last_name', None)
        
        # Extract message text
        message_text = message.text or ""
        
        # Determine media type
        media_type = None
        has_media = bool(message.media)
        
        if has_media:
            if isinstance(message.media, MessageMediaPhoto):
                media_type = "photo"
            elif isinstance(message.media, MessageMediaVideo):
                media_type = "video"
            elif isinstance(message.media, MessageMediaDocument):
                media_type = "document"
            else:
                media_type = "other"
        
        # Extract engagement metrics
        views = getattr(message, 'views', None)
        forwards = getattr(message, 'forwards', None)
        replies = getattr(message, 'replies', None)
        if replies:
            replies = getattr(replies, 'replies', 0)
        
        return MessageData(
            id=message.id,
            date=message.date,
            text=message_text,
            sender_id=sender_id,
            sender_username=sender_username,
            sender_first_name=sender_first_name,
            sender_last_name=sender_last_name,
            views=views,
            forwards=forwards,
            replies=replies,
            is_reply=bool(message.reply_to_msg_id),
            reply_to_msg_id=message.reply_to_msg_id,
            has_media=has_media,
            media_type=media_type,
            media_file_path=media_file_path,
            raw_data={
                'grouped_id': getattr(message, 'grouped_id', None),
                'edit_date': getattr(message, 'edit_date', None),
                'post_author': getattr(message, 'post_author', None),
                'via_bot_id': getattr(message, 'via_bot_id', None)
            }
        )
    
    async def scrape_channel_messages(self, channel_username: str) -> Optional[ChannelData]:
        """
        Scrape messages from a Telegram channel.
        
        Args:
            channel_username: Channel username (without @)
            
        Returns:
            ChannelData object with scraped messages
        """
        try:
            logger.info(f"🔍 Starting to scrape channel: @{channel_username}")
            
            # Get channel info
            channel_data = await self.get_channel_info(channel_username)
            if not channel_data:
                return None
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=self.config.days_back)
            
            logger.info(f"📅 Scraping messages from {start_date.date()} to {end_date.date()}")
            logger.info(f"📊 Max messages: {self.config.max_messages}")
            
            # Get entity for iteration
            entity = await self.client.get_entity(channel_username)
            
            messages_scraped = 0
            media_downloaded = 0
            
            # Iterate through messages
            async for message in self.client.iter_messages(
                entity,
                limit=self.config.max_messages,
                offset_date=end_date,
                reverse=False
            ):
                try:
                    # Check date range
                    if message.date < start_date:
                        break
                    
                    # Download media if enabled
                    media_file_path = None
                    if (self.config.download_media and 
                        message.media and 
                        self.should_download_media(message)):
                        
                        media_file_path = await self.download_media_file(message, channel_username)
                        if media_file_path:
                            media_downloaded += 1
                    
                    # Extract message data
                    message_data = self.extract_message_data(message, media_file_path)
                    channel_data.messages.append(message_data)
                    
                    messages_scraped += 1
                    
                    if messages_scraped % 100 == 0:
                        logger.info(f"📝 Scraped {messages_scraped} messages...")
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
                    
                except FloodWaitError as e:
                    logger.warning(f"⏳ Rate limited. Waiting {e.seconds} seconds...")
                    await asyncio.sleep(e.seconds)
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ Error processing message {message.id}: {e}")
                    continue
            
            logger.info(f"✅ Scraping completed for @{channel_username}")
            logger.info(f"📊 Messages scraped: {messages_scraped}")
            logger.info(f"📥 Media files downloaded: {media_downloaded}")
            
            return channel_data
            
        except Exception as e:
            logger.error(f"❌ Error scraping channel @{channel_username}: {e}")
            return None
    
    def should_download_media(self, message) -> bool:
        """
        Determine if media should be downloaded based on configuration.
        
        Args:
            message: Telethon message object
            
        Returns:
            bool: True if media should be downloaded
        """
        if not message.media:
            return False
        
        if isinstance(message.media, MessageMediaPhoto) and 'photo' in self.config.media_types:
            return True
        elif isinstance(message.media, MessageMediaVideo) and 'video' in self.config.media_types:
            return True
        elif isinstance(message.media, MessageMediaDocument) and 'document' in self.config.media_types:
            return True
        
        return False
    
    async def save_channel_data(self, channel_data: ChannelData) -> bool:
        """
        Save scraped channel data to JSON file.
        
        Args:
            channel_data: ChannelData object to save
            
        Returns:
            bool: True if successful
        """
        try:
            output_file = Path(self.config.output_dir) / f"{channel_data.username}.json"
            
            # Convert to serializable format
            data_dict = {
                'channel_info': {
                    'id': channel_data.id,
                    'username': channel_data.username,
                    'title': channel_data.title,
                    'about': channel_data.about,
                    'participants_count': channel_data.participants_count,
                    'is_broadcast': channel_data.is_broadcast,
                    'is_megagroup': channel_data.is_megagroup,
                    'created_date': channel_data.created_date.isoformat() if channel_data.created_date else None,
                    'scraped_at': channel_data.scraped_at.isoformat()
                },
                'messages': []
            }
            
            for msg in channel_data.messages:
                msg_dict = {
                    'id': msg.id,
                    'date': msg.date.isoformat(),
                    'text': msg.text,
                    'sender_id': msg.sender_id,
                    'sender_username': msg.sender_username,
                    'sender_first_name': msg.sender_first_name,
                    'sender_last_name': msg.sender_last_name,
                    'views': msg.views,
                    'forwards': msg.forwards,
                    'replies': msg.replies,
                    'is_reply': msg.is_reply,
                    'reply_to_msg_id': msg.reply_to_msg_id,
                    'has_media': msg.has_media,
                    'media_type': msg.media_type,
                    'media_file_path': msg.media_file_path,
                    'raw_data': msg.raw_data
                }
                data_dict['messages'].append(msg_dict)
            
            # Save to file
            async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data_dict, indent=2, ensure_ascii=False))
            
            logger.info(f"💾 Saved channel data to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving channel data: {e}")
            return False
    
    async def scrape_multiple_channels(self, channel_usernames: List[str]) -> Dict[str, Optional[ChannelData]]:
        """
        Scrape multiple channels.
        
        Args:
            channel_usernames: List of channel usernames
            
        Returns:
            Dictionary mapping channel usernames to ChannelData objects
        """
        results = {}
        
        logger.info(f"🚀 Starting to scrape {len(channel_usernames)} channels")
        
        for i, channel_username in enumerate(channel_usernames, 1):
            logger.info(f"📡 [{i}/{len(channel_usernames)}] Processing @{channel_username}")
            
            try:
                channel_data = await self.scrape_channel_messages(channel_username)
                results[channel_username] = channel_data
                
                if channel_data:
                    await self.save_channel_data(channel_data)
                
                # Delay between channels to avoid rate limiting
                if i < len(channel_usernames):
                    logger.info("⏳ Waiting before next channel...")
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"❌ Error processing @{channel_username}: {e}")
                results[channel_username] = None
        
        logger.info(f"✅ Completed scraping {len(channel_usernames)} channels")
        return results
    
    async def close(self):
        """Close the Telegram client"""
        if self.client:
            await self.client.disconnect()
            logger.info("🔌 Telegram client disconnected")

async def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Scrape Telegram channels")
    parser.add_argument("--api-id", required=True, type=int, help="Telegram API ID")
    parser.add_argument("--api-hash", required=True, help="Telegram API Hash")
    parser.add_argument("--phone", required=True, help="Phone number")
    parser.add_argument("--channels", required=True, nargs='+', help="Channel usernames (without @)")
    parser.add_argument("--max-messages", type=int, default=1000, help="Maximum messages per channel")
    parser.add_argument("--days-back", type=int, default=30, help="Days to go back")
    parser.add_argument("--no-media", action="store_true", help="Don't download media files")
    parser.add_argument("--output-dir", default="data/raw/telegram_messages", help="Output directory")
    parser.add_argument("--media-dir", default="data/raw/media", help="Media directory")
    
    args = parser.parse_args()
    
    # Create configuration
    config = ScrapingConfig(
        api_id=args.api_id,
        api_hash=args.api_hash,
        phone_number=args.phone,
        max_messages=args.max_messages,
        days_back=args.days_back,
        download_media=not args.no_media,
        output_dir=args.output_dir,
        media_dir=args.media_dir
    )
    
    # Create scraper
    scraper = TelegramScraper(config)
    
    try:
        # Initialize client
        if not await scraper.initialize_client():
            logger.error("❌ Failed to initialize Telegram client")
            return
        
        # Scrape channels
        results = await scraper.scrape_multiple_channels(args.channels)
        
        # Print summary
        print("\n📊 SCRAPING RESULTS")
        print("=" * 40)
        
        total_messages = 0
        successful_channels = 0
        
        for channel, data in results.items():
            if data:
                successful_channels += 1
                total_messages += len(data.messages)
                print(f"✅ @{channel}: {len(data.messages)} messages")
            else:
                print(f"❌ @{channel}: Failed")
        
        print(f"\nTotal successful channels: {successful_channels}/{len(args.channels)}")
        print(f"Total messages scraped: {total_messages}")
        
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())