#!/usr/bin/env python3
"""
Complete YOLO Integration Script

This script provides a comprehensive integration of YOLO object detection
with the existing Telegram data pipeline, including:
1. Object detection on images
2. Database storage of detection results
3. dbt model execution for analytics
4. API endpoint testing

Based on the Data Enrichment with Modern Computer Vision documentation.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    import requests
except ImportError:
    print("Installing requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

from sqlalchemy.orm import Session
from src.database.config import db_config, get_db
from src.database.models import DetectedObject, MediaFile, TelegramMessage, Base
from scripts.enhanced_object_detection import EnhancedYOLODetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('yolo_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class YOLOIntegrationPipeline:
    """Complete YOLO integration pipeline"""
    
    def __init__(self):
        self.detector = None
        self.db_session = None
        self.api_base_url = "http://localhost:8000"
        
        # Configuration
        self.input_dir = r"d:\10-Academy\Week7\data\raw\images"
        self.output_dir = r"d:\10-Academy\Week7\data\raw\DETECTED results"
        self.model_path = "yolov8n.pt"
        self.confidence_threshold = 0.5
    
    def setup(self):
        """Initialize the pipeline components"""
        logger.info("Setting up YOLO Integration Pipeline")
        
        # Create database tables
        Base.metadata.create_all(bind=db_config.engine)
        
        # Initialize detector
        self.detector = EnhancedYOLODetector(self.model_path)
        
        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info("Pipeline setup completed")
    
    def get_db_session(self):
        """Get database session"""
        if self.db_session is None:
            self.db_session = db_config.get_session()
        return self.db_session
    
    def close_db_session(self):
        """Close database session"""
        if self.db_session:
            self.db_session.close()
            self.db_session = None
    
    def process_images_with_db_storage(self):
        """Process images and store results in database"""
        logger.info("Starting image processing with database storage")
        
        db = self.get_db_session()
        
        try:
            # Supported image extensions
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
            
            # Process images
            input_path = Path(self.input_dir)
            processed_count = 0
            total_detections = 0
            
            for image_file in input_path.rglob('*'):
                if image_file.suffix.lower() in image_extensions:
                    try:
                        logger.info(f"Processing {image_file}")
                        
                        # Check if media file exists in database
                        media_file = db.query(MediaFile).filter(
                            MediaFile.file_path == str(image_file)
                        ).first()
                        
                        if not media_file:
                            # Create media file record
                            media_file = MediaFile(
                                message_id=1,  # Default message ID
                                file_type='image',
                                file_path=str(image_file),
                                file_size=image_file.stat().st_size,
                                file_name=image_file.name,
                                created_at=datetime.now()
                            )
                            db.add(media_file)
                            db.commit()
                            db.refresh(media_file)
                        
                        # Detect objects
                        detections = self.detector.detect_objects(
                            str(image_file), 
                            self.confidence_threshold
                        )
                        
                        if detections:
                            # Save annotated image
                            output_image_path = Path(self.output_dir) / f"annotated_{image_file.name}"
                            self.detector.save_annotated_image(
                                str(image_file), 
                                detections, 
                                str(output_image_path)
                            )
                            
                            # Save detection results
                            self.detector.save_detection_results(
                                str(image_file), 
                                detections, 
                                self.output_dir
                            )
                            
                            # Store detections in database
                            for detection in detections:
                                detected_object = DetectedObject(
                                    message_id=media_file.message_id,
                                    media_file_id=media_file.id,
                                    object_class=detection['object_class'],
                                    confidence=detection['confidence'],
                                    bbox_x=detection['bbox_x'],
                                    bbox_y=detection['bbox_y'],
                                    bbox_width=detection['bbox_width'],
                                    bbox_height=detection['bbox_height'],
                                    created_at=datetime.now()
                                )
                                db.add(detected_object)
                            
                            db.commit()
                            total_detections += len(detections)
                            
                            logger.info(f"Stored {len(detections)} detections for {image_file}")
                        else:
                            logger.info(f"No objects detected in {image_file}")
                        
                        processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing {image_file}: {e}")
                        db.rollback()
            
            logger.info(f"Image processing completed. Processed {processed_count} images with {total_detections} total detections")
            
        except Exception as e:
            logger.error(f"Error in image processing: {e}")
            db.rollback()
        finally:
            self.close_db_session()
    
    def run_dbt_models(self):
        """Execute dbt models for analytics"""
        logger.info("Running dbt models")
        
        try:
            # Change to dbt project directory
            dbt_dir = Path(project_root) / "dbt_project"
            
            # Run dbt models
            commands = [
                ["dbt", "deps"],
                ["dbt", "run", "--models", "staging"],
                ["dbt", "run", "--models", "analytics"],
                ["dbt", "run", "--models", "marts"],
                ["dbt", "test"]
            ]
            
            for cmd in commands:
                logger.info(f"Running: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    cwd=dbt_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"Successfully executed: {' '.join(cmd)}")
                else:
                    logger.warning(f"Command failed: {' '.join(cmd)}")
                    logger.warning(f"Error: {result.stderr}")
            
            logger.info("dbt model execution completed")
            
        except Exception as e:
            logger.error(f"Error running dbt models: {e}")
    
    def test_api_endpoints(self):
        """Test the API endpoints"""
        logger.info("Testing API endpoints")
        
        endpoints_to_test = [
            "/health",
            "/detections/",
            "/analytics/object-detection-summary",
            "/analytics/object-detection-insights",
            "/analytics/detection-quality-metrics"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                url = f"{self.api_base_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"✓ {endpoint} - Status: {response.status_code}")
                else:
                    logger.warning(f"✗ {endpoint} - Status: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"✗ {endpoint} - Error: {e}")
    
    def generate_summary_report(self):
        """Generate a summary report of the integration"""
        logger.info("Generating summary report")
        
        db = self.get_db_session()
        
        try:
            # Get statistics
            total_detections = db.query(DetectedObject).count()
            total_media_files = db.query(MediaFile).count()
            unique_object_classes = db.query(DetectedObject.object_class).distinct().count()
            
            # Get confidence distribution
            high_confidence = db.query(DetectedObject).filter(
                DetectedObject.confidence >= 0.8
            ).count()
            
            medium_confidence = db.query(DetectedObject).filter(
                DetectedObject.confidence >= 0.5,
                DetectedObject.confidence < 0.8
            ).count()
            
            low_confidence = db.query(DetectedObject).filter(
                DetectedObject.confidence < 0.5
            ).count()
            
            # Generate report
            report = {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_detections": total_detections,
                    "total_media_files": total_media_files,
                    "unique_object_classes": unique_object_classes
                },
                "confidence_distribution": {
                    "high_confidence": high_confidence,
                    "medium_confidence": medium_confidence,
                    "low_confidence": low_confidence
                },
                "directories": {
                    "input_directory": self.input_dir,
                    "output_directory": self.output_dir
                }
            }
            
            # Save report
            report_path = Path(self.output_dir) / "integration_summary.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Summary report saved to {report_path}")
            logger.info(f"Total detections: {total_detections}")
            logger.info(f"Total media files: {total_media_files}")
            logger.info(f"Unique object classes: {unique_object_classes}")
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
        finally:
            self.close_db_session()
    
    def run_complete_pipeline(self):
        """Run the complete integration pipeline"""
        logger.info("Starting Complete YOLO Integration Pipeline")
        
        try:
            # Setup
            self.setup()
            
            # Step 1: Process images and store in database
            self.process_images_with_db_storage()
            
            # Step 2: Run dbt models
            self.run_dbt_models()
            
            # Step 3: Test API endpoints
            self.test_api_endpoints()
            
            # Step 4: Generate summary report
            self.generate_summary_report()
            
            logger.info("Complete YOLO Integration Pipeline finished successfully")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise

def main():
    """Main function"""
    pipeline = YOLOIntegrationPipeline()
    pipeline.run_complete_pipeline()

if __name__ == "__main__":
    main()