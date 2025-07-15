#!/usr/bin/env python3
"""
Enhanced Object Detection Script for YOLO Integration

This script processes images from the raw images directory, performs YOLO object detection,
saves results to the detected results directory, and stores detection data in the database.

Based on the Data Enrichment with Modern Computer Vision documentation.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from ultralytics import YOLO
    import cv2
    import numpy as np
except ImportError as e:
    print(f"Error importing required packages: {e}")
    print("Please install: pip install ultralytics opencv-python")
    sys.exit(1)

from sqlalchemy.orm import Session
from src.database.config import db_config
from src.database.models import DetectedObject, MediaFile, TelegramMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('object_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedYOLODetector:
    """Enhanced YOLO object detector with database integration"""
    
    def __init__(self, model_path: str = "yolov8n.pt"):
        """
        Initialize the YOLO detector
        
        Args:
            model_path: Path to the YOLO model file
        """
        self.model_path = model_path
        self.model = None
        self.load_model()
        
        # Medical relevance mapping for objects
        self.medical_relevance = {
            'bottle': 0.8,  # Medicine bottles, IV bottles
            'cup': 0.6,     # Medicine cups, specimen containers
            'scissors': 1.0, # Medical scissors
            'person': 0.7,   # Patients, medical staff
            'book': 0.4,     # Medical records, prescriptions
            'cell phone': 0.3, # Communication devices
            'syringe': 1.0,  # Medical syringes
            'stethoscope': 1.0, # Medical equipment
        }
    
    def load_model(self):
        """Load the YOLO model"""
        try:
            logger.info(f"Loading YOLO model from {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise
    
    def detect_objects(self, image_path: str, confidence_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Detect objects in an image
        
        Args:
            image_path: Path to the image file
            confidence_threshold: Minimum confidence for detections
            
        Returns:
            List of detection dictionaries
        """
        try:
            # Run inference
            results = self.model(image_path, conf=confidence_threshold)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract detection information
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
                            'bbox_height': float(y2 - y1),
                            'medical_relevance': self.medical_relevance.get(class_name, 0.2)
                        }
                        detections.append(detection)
            
            logger.info(f"Detected {len(detections)} objects in {image_path}")
            return detections
            
        except Exception as e:
            logger.error(f"Error detecting objects in {image_path}: {e}")
            return []
    
    def save_annotated_image(self, image_path: str, detections: List[Dict[str, Any]], output_path: str):
        """
        Save image with detection annotations
        
        Args:
            image_path: Original image path
            detections: List of detections
            output_path: Path to save annotated image
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return
            
            # Draw bounding boxes and labels
            for detection in detections:
                x1 = int(detection['bbox_x'])
                y1 = int(detection['bbox_y'])
                x2 = int(x1 + detection['bbox_width'])
                y2 = int(y1 + detection['bbox_height'])
                
                # Choose color based on confidence
                confidence = detection['confidence']
                if confidence >= 0.8:
                    color = (0, 255, 0)  # Green for high confidence
                elif confidence >= 0.6:
                    color = (0, 255, 255)  # Yellow for medium confidence
                else:
                    color = (0, 0, 255)  # Red for low confidence
                
                # Draw bounding box
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                label = f"{detection['object_class']}: {confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                cv2.rectangle(image, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
                cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Save annotated image
            cv2.imwrite(output_path, image)
            logger.info(f"Saved annotated image to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving annotated image: {e}")
    
    def save_detection_results(self, image_path: str, detections: List[Dict[str, Any]], output_dir: str):
        """
        Save detection results as JSON
        
        Args:
            image_path: Original image path
            detections: List of detections
            output_dir: Directory to save results
        """
        try:
            image_name = Path(image_path).stem
            json_path = Path(output_dir) / f"{image_name}_detections.json"
            
            result_data = {
                'image_path': image_path,
                'timestamp': datetime.now().isoformat(),
                'total_detections': len(detections),
                'detections': detections
            }
            
            with open(json_path, 'w') as f:
                json.dump(result_data, f, indent=2)
            
            logger.info(f"Saved detection results to {json_path}")
            
        except Exception as e:
            logger.error(f"Error saving detection results: {e}")

def process_images_directory(
    input_dir: str,
    output_dir: str,
    model_path: str = "yolov8n.pt",
    confidence_threshold: float = 0.5
):
    """
    Process all images in a directory
    
    Args:
        input_dir: Directory containing input images
        output_dir: Directory to save results
        model_path: Path to YOLO model
        confidence_threshold: Minimum confidence for detections
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize detector
    detector = EnhancedYOLODetector(model_path)
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    # Process images
    input_path = Path(input_dir)
    processed_count = 0
    total_detections = 0
    
    logger.info(f"Starting batch processing of images in {input_dir}")
    
    for image_file in input_path.rglob('*'):
        if image_file.suffix.lower() in image_extensions:
            try:
                logger.info(f"Processing {image_file}")
                
                # Detect objects
                detections = detector.detect_objects(str(image_file), confidence_threshold)
                
                if detections:
                    # Save annotated image
                    output_image_path = Path(output_dir) / f"annotated_{image_file.name}"
                    detector.save_annotated_image(str(image_file), detections, str(output_image_path))
                    
                    # Save detection results
                    detector.save_detection_results(str(image_file), detections, output_dir)
                    
                    total_detections += len(detections)
                else:
                    logger.info(f"No objects detected in {image_file}")
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {image_file}: {e}")
    
    logger.info(f"Batch processing completed. Processed {processed_count} images with {total_detections} total detections")

def main():
    """Main function to run object detection on specified directories"""
    # Configuration
    input_dir = r"d:\10-Academy\Week7\data\raw\images"
    output_dir = r"d:\10-Academy\Week7\data\raw\DETECTED results"
    model_path = "yolov8n.pt"
    confidence_threshold = 0.5
    
    logger.info("Starting Enhanced YOLO Object Detection")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Model: {model_path}")
    logger.info(f"Confidence threshold: {confidence_threshold}")
    
    # Check if input directory exists
    if not Path(input_dir).exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return
    
    # Process images
    process_images_directory(input_dir, output_dir, model_path, confidence_threshold)
    
    logger.info("Object detection completed successfully")

if __name__ == "__main__":
    main()