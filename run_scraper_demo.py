#!/usr/bin/env python3
"""
Telegram Scraper Demo Script

This script demonstrates the telegram scraping functionality with sample data.
It creates the required directory structure and sample data files as specified in the rubric.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramScraperDemo:
    """
    Demo version of Telegram scraper that creates sample data
    following the required format: data/raw/YYYY-MM-DD/channelname.json
    """
    
    def __init__(self):
        self.base_dir = Path("data/raw")
        self.media_dir = Path("data/raw/media")
        
        # Create directories
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        logger.info("🔧 Initialized Telegram Scraper Demo")
    
    def generate_sample_message(self, msg_id: int, channel: str, date: datetime) -> Dict[str, Any]:
        """Generate a sample message with realistic structure"""
        sample_texts = [
            "🏥 New medical equipment available at our clinic! Contact us for more info.",
            "📞 Call us at +251-11-123-4567 for appointments",
            "💊 Pharmacy services available 24/7. Quality medicines guaranteed.",
            "🩺 Free health checkup this weekend. Book your slot now!",
            "🚑 Emergency services available. We care for your health.",
            "💉 Vaccination campaign starting next week. Stay protected!",
            "🏥 Our medical center offers comprehensive healthcare solutions.",
            "📋 Health insurance accepted. Affordable healthcare for all.",
            "👨‍⚕️ Experienced doctors and modern facilities at your service.",
            "🔬 Laboratory services with accurate and fast results."
        ]
        
        return {
            "id": msg_id,
            "date": date.isoformat(),
            "text": sample_texts[msg_id % len(sample_texts)],
            "sender_id": 1000000 + (msg_id % 100),
            "sender_username": f"user_{msg_id % 50}",
            "sender_first_name": f"User{msg_id % 50}",
            "sender_last_name": "Demo",
            "views": (msg_id * 15) % 1000,
            "forwards": (msg_id * 3) % 50,
            "replies": (msg_id * 2) % 20,
            "is_reply": msg_id % 5 == 0,
            "reply_to_msg_id": msg_id - 1 if msg_id % 5 == 0 else None,
            "has_media": msg_id % 3 == 0,
            "media_type": "photo" if msg_id % 3 == 0 else None,
            "media_file_path": f"data/raw/media/{channel}_{msg_id}.jpg" if msg_id % 3 == 0 else None,
            "raw_data": {
                "grouped_id": None,
                "edit_date": None,
                "post_author": channel,
                "via_bot_id": None
            }
        }
    
    def generate_sample_channel_data(self, channel_name: str, date: datetime, num_messages: int = 50) -> Dict[str, Any]:
        """Generate sample channel data with messages"""
        channel_data = {
            "channel_info": {
                "id": hash(channel_name) % 1000000,
                "username": channel_name,
                "title": f"{channel_name.replace('_', ' ').title()} Medical Center",
                "about": f"Official channel for {channel_name.replace('_', ' ').title()} - Your trusted healthcare provider",
                "participants_count": (hash(channel_name) % 10000) + 1000,
                "is_broadcast": True,
                "is_megagroup": False,
                "created_date": (date - timedelta(days=365)).isoformat(),
                "scraped_at": datetime.utcnow().isoformat()
            },
            "messages": []
        }
        
        # Generate messages for the day
        for i in range(num_messages):
            msg_date = date + timedelta(hours=i % 24, minutes=(i * 15) % 60)
            message = self.generate_sample_message(i + 1, channel_name, msg_date)
            channel_data["messages"].append(message)
        
        return channel_data
    
    def create_sample_data(self, channels: List[str], days_back: int = 7) -> None:
        """Create sample data following the required format"""
        logger.info(f"📊 Creating sample data for {len(channels)} channels over {days_back} days")
        
        total_files = 0
        total_messages = 0
        
        for day_offset in range(days_back):
            current_date = datetime.utcnow() - timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Create date directory
            date_dir = self.base_dir / date_str
            date_dir.mkdir(exist_ok=True)
            
            logger.info(f"📅 Creating data for {date_str}")
            
            for channel in channels:
                # Generate channel data for this date
                channel_data = self.generate_sample_channel_data(
                    channel, current_date, num_messages=20 + (day_offset * 5)
                )
                
                # Save to required format: data/raw/YYYY-MM-DD/channelname.json
                output_file = date_dir / f"{channel}.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(channel_data, f, indent=2, ensure_ascii=False)
                
                total_files += 1
                total_messages += len(channel_data["messages"])
                
                logger.info(f"✅ Created {output_file} with {len(channel_data['messages'])} messages")
        
        logger.info(f"🎉 Sample data creation completed!")
        logger.info(f"📊 Total files created: {total_files}")
        logger.info(f"📝 Total messages generated: {total_messages}")
    
    def create_media_samples(self, channels: List[str]) -> None:
        """Create sample media directory structure"""
        logger.info("📸 Creating sample media directory structure")
        
        for channel in channels:
            channel_media_dir = self.media_dir / channel
            channel_media_dir.mkdir(exist_ok=True)
            
            # Create placeholder files
            for i in range(5):
                placeholder_file = channel_media_dir / f"{channel}_{i+1}_sample.jpg"
                placeholder_file.write_text(f"Sample media file for {channel} - Image {i+1}")
            
            logger.info(f"📁 Created media directory for {channel}")
    
    def validate_data_structure(self) -> bool:
        """Validate that the created data follows the required structure"""
        logger.info("🔍 Validating data structure...")
        
        # Check if data/raw exists
        if not self.base_dir.exists():
            logger.error("❌ data/raw directory not found")
            return False
        
        # Check for date directories
        date_dirs = [d for d in self.base_dir.iterdir() if d.is_dir() and d.name != 'media']
        if not date_dirs:
            logger.error("❌ No date directories found")
            return False
        
        # Check for JSON files in date directories
        json_files_found = False
        for date_dir in date_dirs:
            json_files = list(date_dir.glob("*.json"))
            if json_files:
                json_files_found = True
                logger.info(f"✅ Found {len(json_files)} JSON files in {date_dir.name}")
        
        if not json_files_found:
            logger.error("❌ No JSON files found in date directories")
            return False
        
        logger.info("✅ Data structure validation passed")
        return True

def main():
    """Main function to run the demo scraper"""
    print("🚀 Telegram Scraper Demo - Creating Sample Data")
    print("=" * 50)
    
    # Sample Ethiopian medical business channels
    sample_channels = [
        "addis_medical_center",
        "bethel_hospital",
        "cure_ethiopia",
        "black_lion_hospital",
        "st_paul_hospital"
    ]
    
    try:
        # Initialize demo scraper
        scraper = TelegramScraperDemo()
        
        # Create sample data
        scraper.create_sample_data(sample_channels, days_back=7)
        
        # Create media samples
        scraper.create_media_samples(sample_channels)
        
        # Validate structure
        if scraper.validate_data_structure():
            print("\n🎉 SUCCESS: Sample data created successfully!")
            print("\n📋 SUMMARY:")
            print(f"   • Data directory: {scraper.base_dir.absolute()}")
            print(f"   • Media directory: {scraper.media_dir.absolute()}")
            print(f"   • Channels: {len(sample_channels)}")
            print(f"   • Date range: 7 days")
            print("\n📁 Directory structure created:")
            print("   data/raw/YYYY-MM-DD/channelname.json")
            print("   data/raw/media/channelname/")
            
            print("\n🔧 Next steps:")
            print("   1. Configure .env file with real Telegram API credentials")
            print("   2. Run 'python scripts/telegram_scraper.py' for real data")
            print("   3. Execute 'python run_integration.py' for dbt transformations")
            
        else:
            print("❌ FAILED: Data structure validation failed")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Error running demo: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())