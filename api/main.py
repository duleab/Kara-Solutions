#!/usr/bin/env python3
"""
Ethiopian Medical Business Telegram Analytics API

A FastAPI application that provides analytical endpoints for Telegram data,
incorporating object detection results and business intelligence insights.

Based on the Kara-Solutions architecture with enhanced features.
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from api.database import get_db
from api import crud, schemas
from src.database.models import Base
from src.database.config import db_config

# Create database tables
Base.metadata.create_all(bind=db_config.engine)

# Initialize FastAPI app
app = FastAPI(
    title="Ethiopian Medical Business Telegram Analytics API",
    description="Analytical API for Telegram data with object detection and business intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "message": "Ethiopian Medical Business Telegram Analytics API",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "api_version": "1.0.0"
    }

# ============================================================================
# TELEGRAM CHANNELS ENDPOINTS
# ============================================================================

@app.get("/channels/", response_model=List[schemas.TelegramChannel], tags=["Channels"])
def get_channels(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all Telegram channels with pagination"""
    channels = crud.get_channels(db, skip=skip, limit=limit)
    return channels

@app.get("/channels/{channel_id}", response_model=schemas.TelegramChannel, tags=["Channels"])
def get_channel(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific channel by ID"""
    channel = crud.get_channel(db, channel_id=channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@app.post("/channels/", response_model=schemas.TelegramChannel, tags=["Channels"])
def create_channel(
    channel: schemas.TelegramChannelCreate,
    db: Session = Depends(get_db)
):
    """Create a new channel"""
    return crud.create_channel(db=db, channel=channel)

# ============================================================================
# TELEGRAM MESSAGES ENDPOINTS
# ============================================================================

@app.get("/messages/", response_model=List[schemas.TelegramMessage], tags=["Messages"])
def get_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    channel_id: Optional[int] = Query(None, description="Filter by channel ID"),
    has_media: Optional[bool] = Query(None, description="Filter by media presence"),
    db: Session = Depends(get_db)
):
    """Get messages with optional filtering"""
    messages = crud.get_messages(
        db, skip=skip, limit=limit, channel_id=channel_id, has_media=has_media
    )
    return messages

@app.get("/messages/{message_id}", response_model=schemas.TelegramMessage, tags=["Messages"])
def get_message(
    message_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific message by ID"""
    message = crud.get_message(db, message_id=message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@app.post("/messages/", response_model=schemas.TelegramMessage, tags=["Messages"])
def create_message(
    message: schemas.TelegramMessageCreate,
    db: Session = Depends(get_db)
):
    """Create a new message"""
    return crud.create_message(db=db, message=message)

# ============================================================================
# MEDIA FILES ENDPOINTS
# ============================================================================

@app.get("/media/", response_model=List[schemas.MediaFile], tags=["Media"])
def get_media_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    file_type: Optional[str] = Query(None, description="Filter by file type (image, video, document)"),
    db: Session = Depends(get_db)
):
    """Get media files with optional filtering"""
    media_files = crud.get_media_files(db, skip=skip, limit=limit, file_type=file_type)
    return media_files

@app.get("/media/{media_id}", response_model=schemas.MediaFile, tags=["Media"])
def get_media_file(
    media_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific media file by ID"""
    media_file = crud.get_media_file(db, media_id=media_id)
    if media_file is None:
        raise HTTPException(status_code=404, detail="Media file not found")
    return media_file

@app.post("/media/", response_model=schemas.MediaFile, tags=["Media"])
def create_media_file(
    media_file: schemas.MediaFileCreate,
    db: Session = Depends(get_db)
):
    """Create a new media file record"""
    return crud.create_media_file(db=db, media_file=media_file)

# ============================================================================
# OBJECT DETECTION ENDPOINTS
# ============================================================================

@app.get("/detections/", response_model=List[schemas.DetectedObject], tags=["Object Detection"])
def get_detected_objects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    object_class: Optional[str] = Query(None, description="Filter by object class"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    db: Session = Depends(get_db)
):
    """Get detected objects with optional filtering"""
    detections = crud.get_detected_objects(
        db, skip=skip, limit=limit, object_class=object_class, min_confidence=min_confidence
    )
    return detections

@app.get("/detections/{detection_id}", response_model=schemas.DetectedObject, tags=["Object Detection"])
def get_detected_object(
    detection_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific detected object by ID"""
    detection = crud.get_detected_object(db, detection_id=detection_id)
    if detection is None:
        raise HTTPException(status_code=404, detail="Detection not found")
    return detection

@app.post("/detections/", response_model=schemas.DetectedObject, tags=["Object Detection"])
def create_detected_object(
    detection: schemas.DetectedObjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new object detection record"""
    return crud.create_detected_object(db=db, detection=detection)

# ============================================================================
# BUSINESS INFORMATION ENDPOINTS
# ============================================================================

@app.get("/businesses/", response_model=List[schemas.BusinessInfo], tags=["Business Intelligence"])
def get_business_info(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    business_name: Optional[str] = Query(None, description="Filter by business name"),
    db: Session = Depends(get_db)
):
    """Get business information with optional filtering"""
    businesses = crud.get_business_info(
        db, skip=skip, limit=limit, business_name=business_name
    )
    return businesses

@app.get("/businesses/{business_id}", response_model=schemas.BusinessInfo, tags=["Business Intelligence"])
def get_business(
    business_id: int,
    db: Session = Depends(get_db)
):
    """Get specific business information by ID"""
    business = crud.get_business(db, business_id=business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return business

@app.post("/businesses/", response_model=schemas.BusinessInfo, tags=["Business Intelligence"])
def create_business_info(
    business: schemas.BusinessInfoCreate,
    db: Session = Depends(get_db)
):
    """Create new business information record"""
    return crud.create_business_info(db=db, business=business)

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics/channel-stats", tags=["Analytics"])
def get_channel_statistics(
    db: Session = Depends(get_db)
):
    """Get comprehensive channel statistics"""
    return crud.get_channel_statistics(db)

@app.get("/analytics/media-distribution", tags=["Analytics"])
def get_media_distribution(
    db: Session = Depends(get_db)
):
    """Get media type distribution across channels"""
    return crud.get_media_distribution(db)

@app.get("/analytics/object-detection-summary", tags=["Analytics"])
def get_object_detection_summary(
    db: Session = Depends(get_db)
):
    """Get object detection summary statistics"""
    return crud.get_object_detection_summary(db)

@app.get("/analytics/object-detection-insights", tags=["Analytics"])
def get_object_detection_insights(
    insight_type: Optional[str] = Query(None, description="Filter by insight type (daily_summary, object_popularity, channel_patterns)"),
    channel_name: Optional[str] = Query(None, description="Filter by channel name"),
    object_category: Optional[str] = Query(None, description="Filter by object category"),
    db: Session = Depends(get_db)
):
    """Get comprehensive object detection insights from dbt models"""
    return crud.get_object_detection_insights(db, insight_type=insight_type, channel_name=channel_name, object_category=object_category)

@app.get("/analytics/medical-relevance-score", tags=["Analytics"])
def get_medical_relevance_analysis(
    min_score: Optional[float] = Query(0.5, ge=0.0, le=1.0, description="Minimum medical relevance score"),
    channel_name: Optional[str] = Query(None, description="Filter by channel name"),
    db: Session = Depends(get_db)
):
    """Get medical relevance analysis for detected objects"""
    return crud.get_medical_relevance_analysis(db, min_score=min_score, channel_name=channel_name)

@app.get("/analytics/detection-quality-metrics", tags=["Analytics"])
def get_detection_quality_metrics(
    db: Session = Depends(get_db)
):
    """Get detection quality metrics and confidence distribution"""
    return crud.get_detection_quality_metrics(db)

@app.get("/analytics/object-trends", tags=["Analytics"])
def get_object_detection_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    object_class: Optional[str] = Query(None, description="Filter by specific object class"),
    db: Session = Depends(get_db)
):
    """Get object detection trends over time"""
    return crud.get_object_detection_trends(db, days=days, object_class=object_class)

@app.get("/analytics/business-insights", tags=["Analytics"])
def get_business_insights(
    db: Session = Depends(get_db)
):
    """Get business intelligence insights"""
    return crud.get_business_insights(db)

@app.get("/analytics/engagement-metrics", tags=["Analytics"])
def get_engagement_metrics(
    channel_id: Optional[int] = Query(None, description="Filter by channel ID"),
    db: Session = Depends(get_db)
):
    """Get engagement metrics (views, forwards, replies)"""
    return crud.get_engagement_metrics(db, channel_id=channel_id)

# ============================================================================
# SPECIFIC BUSINESS ENDPOINTS (As required in Task 4)
# ============================================================================

@app.get("/api/reports/top-products", tags=["Business Reports"])
def get_top_products(
    limit: int = Query(10, ge=1, le=100, description="Number of top products to return"),
    db: Session = Depends(get_db)
):
    """Returns the most frequently mentioned medical products or drugs across all channels"""
    return crud.get_top_mentioned_products(db, limit=limit)

@app.get("/api/channels/{channel_name}/activity", tags=["Business Reports"])
def get_channel_activity(
    channel_name: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Returns the posting activity for a specific channel"""
    return crud.get_channel_activity(db, channel_name=channel_name, days=days)

@app.get("/api/search/messages", tags=["Business Reports"])
def search_messages(
    query: str = Query(..., description="Search term (e.g., 'paracetamol')"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    channel_name: Optional[str] = Query(None, description="Filter by specific channel"),
    db: Session = Depends(get_db)
):
    """Searches for messages containing a specific keyword"""
    return crud.search_messages(db, query=query, limit=limit, channel_name=channel_name)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )