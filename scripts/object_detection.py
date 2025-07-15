#!/usr/bin/env python3
"""
YOLO Object Detection for Telegram Media Files

This script performs object detection on images from Telegram channels
using YOLOv8, stores results in the database, and provides analytics.

Based on the Kara-Solutions implementation with enhancements.
"""

import os
import sys
import cv2
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from ultralytics import YOLO
except ImportError:
    print("❌ ultralytics not installed. Install with: pip install ultralytics")
    sys.exit(1)

from sqlalchemy.orm import Session
from src.database.config import db_config
from src.database.models import MediaFile, DetectedObject, TelegramMessage
from api.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/object_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramObjectDetector:
    """
    YOLO-based object detection for Telegram media files.
    """
    
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.5):
        """
        Initialize the object detector.
        
        Args:
            model_path: Path to YOLO model file
            confidence_threshold: Minimum confidence for detections
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.db = db_config.SessionLocal()
        
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)
        
        logger.info(f"🔧 Initializing TelegramObjectDetector with model: {model_path}")
        
    def load_model(self) -> bool:
        """
        Load the YOLO model.
        
        Returns:
            bool: True if model loaded successfully
        """
        try:
            logger.info(f"📥 Loading YOLO model: {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.info("✅ YOLO model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO model: {e}")
            return False
    
    def detect_objects_in_image(self, image_path: str) -> List[Dict]:
        """
        Detect objects in a single image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of detected objects with their properties
        """
        if not self.model:
            logger.error("❌ Model not loaded. Call load_model() first.")
            return []
        
        if not os.path.exists(image_path):
            logger.warning(f"⚠️ Image not found: {image_path}")
            return []
        
        try:
            # Run YOLO detection
            results = self.model(image_path, conf=self.confidence_threshold)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        class_name = self.model.names[class_id]
                        
                        detection = {
                            'object_class': class_name,
                            'confidence': confidence,
                            'bbox_x': float(x1),
                            'bbox_y': float(y1),
                            'bbox_width': float(x2 - x1),
                            'bbox_height': float(y2 - y1)
                        }
                        detections.append(detection)
            
            logger.info(f"🔍 Detected {len(detections)} objects in {Path(image_path).name}")
            return detections
            
        except Exception as e:
            logger.error(f"❌ Error detecting objects in {image_path}: {e}")
            return []
    
    def process_media_files(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Process all media files in the database for object detection.
        
        Args:
            limit: Maximum number of files to process (None for all)
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info("🚀 Starting object detection on media files...")
        
        # Get media files that haven't been processed yet
        query = self.db.query(MediaFile).filter(
            MediaFile.file_type == 'image'
        ).outerjoin(
            DetectedObject, MediaFile.id == DetectedObject.media_file_id
        ).filter(
            DetectedObject.id.is_(None)  # Only unprocessed files
        )
        
        if limit:
            query = query.limit(limit)
        
        media_files = query.all()
        
        stats = {
            'total_files': len(media_files),
            'processed': 0,
            'failed': 0,
            'total_detections': 0
        }
        
        logger.info(f"📊 Found {stats['total_files']} unprocessed image files")
        
        for media_file in media_files:
            try:
                # Check if file exists
                if not os.path.exists(media_file.file_path):
                    logger.warning(f"⚠️ File not found: {media_file.file_path}")
                    stats['failed'] += 1
                    continue
                
                # Detect objects
                detections = self.detect_objects_in_image(media_file.file_path)
                
                # Save detections to database
                for detection in detections:
                    db_detection = DetectedObject(
                        message_id=media_file.message_id,
                        media_file_id=media_file.id,
                        **detection
                    )
                    self.db.add(db_detection)
                
                self.db.commit()
                
                stats['processed'] += 1
                stats['total_detections'] += len(detections)
                
                if stats['processed'] % 10 == 0:
                    logger.info(f"📈 Processed {stats['processed']}/{stats['total_files']} files")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {media_file.file_path}: {e}")
                stats['failed'] += 1
                self.db.rollback()
        
        logger.info(f"✅ Object detection completed!")
        logger.info(f"📊 Statistics: {stats}")
        
        return stats
    
    def process_specific_channels(self, channel_names: List[str]) -> Dict[str, int]:
        """
        Process media files from specific channels only.
        
        Args:
            channel_names: List of channel names to process
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"🎯 Processing channels: {channel_names}")
        
        # Get media files from specific channels
        media_files = self.db.query(MediaFile).join(
            TelegramMessage, MediaFile.message_id == TelegramMessage.id
        ).join(
            TelegramMessage.channel
        ).filter(
            MediaFile.file_type == 'image',
            TelegramMessage.channel.has(
                channel_name=channel_names[0] if len(channel_names) == 1 
                else TelegramMessage.channel.channel_name.in_(channel_names)
            )
        ).outerjoin(
            DetectedObject, MediaFile.id == DetectedObject.media_file_id
        ).filter(
            DetectedObject.id.is_(None)
        ).all()
        
        stats = {
            'total_files': len(media_files),
            'processed': 0,
            'failed': 0,
            'total_detections': 0
        }
        
        logger.info(f"📊 Found {stats['total_files']} unprocessed files in specified channels")
        
        for media_file in media_files:
            try:
                detections = self.detect_objects_in_image(media_file.file_path)
                
                for detection in detections:
                    db_detection = DetectedObject(
                        message_id=media_file.message_id,
                        media_file_id=media_file.id,
                        **detection
                    )
                    self.db.add(db_detection)
                
                self.db.commit()
                
                stats['processed'] += 1
                stats['total_detections'] += len(detections)
                
            except Exception as e:
                logger.error(f"❌ Error processing {media_file.file_path}: {e}")
                stats['failed'] += 1
                self.db.rollback()
        
        return stats
    
    def export_detection_results(self, output_path: str = "data/processed/detection_results.csv") -> bool:
        """
        Export detection results to CSV file.
        
        Args:
            output_path: Path for the output CSV file
            
        Returns:
            bool: True if export successful
        """
        try:
            logger.info(f"📤 Exporting detection results to {output_path}")
            
            # Query all detection results with related information
            query = """
            SELECT 
                do.id as detection_id,
                do.object_class,
                do.confidence,
                do.bbox_x,
                do.bbox_y,
                do.bbox_width,
                do.bbox_height,
                do.created_at as detection_date,
                mf.file_name,
                mf.file_path,
                mf.file_type,
                tm.message_id,
                tm.date as message_date,
                tc.channel_name
            FROM detected_objects do
            JOIN media_files mf ON do.media_file_id = mf.id
            JOIN telegram_messages tm ON do.message_id = tm.id
            JOIN telegram_channels tc ON tm.channel_id = tc.id
            ORDER BY do.created_at DESC
            """
            
            df = pd.read_sql_query(query, db_config.engine)
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Export to CSV
            df.to_csv(output_path, index=False)
            
            logger.info(f"✅ Exported {len(df)} detection results to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error exporting detection results: {e}")
            return False
    
    def get_detection_summary(self) -> Dict[str, any]:
        """
        Get summary statistics of object detection results.
        
        Returns:
            Dictionary with summary statistics
        """
        try:
            # Total detections
            total_detections = self.db.query(DetectedObject).count()
            
            # Unique object classes
            unique_classes = self.db.query(DetectedObject.object_class).distinct().count()
            
            # Most common objects
            common_objects = self.db.query(
                DetectedObject.object_class,
                func.count(DetectedObject.id).label('count')
            ).group_by(
                DetectedObject.object_class
            ).order_by(
                func.count(DetectedObject.id).desc()
            ).limit(10).all()
            
            # Average confidence
            avg_confidence = self.db.query(
                func.avg(DetectedObject.confidence)
            ).scalar() or 0
            
            summary = {
                'total_detections': total_detections,
                'unique_classes': unique_classes,
                'average_confidence': round(float(avg_confidence), 3),
                'most_common_objects': [
                    {'class': obj.object_class, 'count': obj.count} 
                    for obj in common_objects
                ]
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error getting detection summary: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="YOLO Object Detection for Telegram Media")
    parser.add_argument("--model", default="yolov8n.pt", help="YOLO model path")
    parser.add_argument("--confidence", type=float, default=0.5, help="Confidence threshold")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    parser.add_argument("--channels", nargs="+", help="Specific channels to process")
    parser.add_argument("--export", action="store_true", help="Export results to CSV")
    parser.add_argument("--summary", action="store_true", help="Show detection summary")
    
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    # Create detector
    detector = TelegramObjectDetector(
        model_path=args.model,
        confidence_threshold=args.confidence
    )
    
    try:
        # Load model
        if not detector.load_model():
            logger.error("❌ Failed to load YOLO model")
            return
        
        # Process files
        if args.channels:
            stats = detector.process_specific_channels(args.channels)
        else:
            stats = detector.process_media_files(limit=args.limit)
        
        print("\n📊 OBJECT DETECTION RESULTS")
        print("=" * 40)
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Export results if requested
        if args.export:
            detector.export_detection_results()
        
        # Show summary if requested
        if args.summary:
            summary = detector.get_detection_summary()
            print("\n📈 DETECTION SUMMARY")
            print("=" * 40)
            for key, value in summary.items():
                if key == 'most_common_objects':
                    print(f"{key.replace('_', ' ').title()}:")
                    for obj in value[:5]:  # Show top 5
                        print(f"  - {obj['class']}: {obj['count']}")
                else:
                    print(f"{key.replace('_', ' ').title()}: {value}")
        
    finally:
        detector.close()

if __name__ == "__main__":
    main()