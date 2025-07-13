#!/usr/bin/env python3
"""
CRUD (Create, Read, Update, Delete) operations for the FastAPI application.

This module provides database operations for all models, including
analytical queries for business intelligence.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.database.models import (
    TelegramChannel, TelegramMessage, MediaFile, 
    DetectedObject, BusinessInfo
)
from api import schemas

# ============================================================================
# TELEGRAM CHANNELS CRUD
# ============================================================================

def get_channel(db: Session, channel_id: int) -> Optional[TelegramChannel]:
    """Get a channel by ID"""
    return db.query(TelegramChannel).filter(TelegramChannel.id == channel_id).first()

def get_channel_by_name(db: Session, channel_name: str) -> Optional[TelegramChannel]:
    """Get a channel by name"""
    return db.query(TelegramChannel).filter(TelegramChannel.channel_name == channel_name).first()

def get_channels(db: Session, skip: int = 0, limit: int = 100) -> List[TelegramChannel]:
    """Get all channels with pagination"""
    return db.query(TelegramChannel).offset(skip).limit(limit).all()

def create_channel(db: Session, channel: schemas.TelegramChannelCreate) -> TelegramChannel:
    """Create a new channel"""
    db_channel = TelegramChannel(**channel.dict())
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

# ============================================================================
# TELEGRAM MESSAGES CRUD
# ============================================================================

def get_message(db: Session, message_id: int) -> Optional[TelegramMessage]:
    """Get a message by ID"""
    return db.query(TelegramMessage).filter(TelegramMessage.id == message_id).first()

def get_messages(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    channel_id: Optional[int] = None,
    has_media: Optional[bool] = None
) -> List[TelegramMessage]:
    """Get messages with optional filtering"""
    query = db.query(TelegramMessage)
    
    if channel_id is not None:
        query = query.filter(TelegramMessage.channel_id == channel_id)
    
    if has_media is not None:
        query = query.filter(TelegramMessage.has_media == has_media)
    
    return query.offset(skip).limit(limit).all()

def create_message(db: Session, message: schemas.TelegramMessageCreate) -> TelegramMessage:
    """Create a new message"""
    db_message = TelegramMessage(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

# ============================================================================
# MEDIA FILES CRUD
# ============================================================================

def get_media_file(db: Session, media_id: int) -> Optional[MediaFile]:
    """Get a media file by ID"""
    return db.query(MediaFile).filter(MediaFile.id == media_id).first()

def get_media_files(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    file_type: Optional[str] = None
) -> List[MediaFile]:
    """Get media files with optional filtering"""
    query = db.query(MediaFile)
    
    if file_type is not None:
        query = query.filter(MediaFile.file_type == file_type)
    
    return query.offset(skip).limit(limit).all()

def create_media_file(db: Session, media_file: schemas.MediaFileCreate) -> MediaFile:
    """Create a new media file"""
    db_media = MediaFile(**media_file.dict())
    db.add(db_media)
    db.commit()
    db.refresh(db_media)
    return db_media

# ============================================================================
# DETECTED OBJECTS CRUD
# ============================================================================

def get_detected_object(db: Session, detection_id: int) -> Optional[DetectedObject]:
    """Get a detected object by ID"""
    return db.query(DetectedObject).filter(DetectedObject.id == detection_id).first()

def get_detected_objects(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    object_class: Optional[str] = None,
    min_confidence: Optional[float] = None
) -> List[DetectedObject]:
    """Get detected objects with optional filtering"""
    query = db.query(DetectedObject)
    
    if object_class is not None:
        query = query.filter(DetectedObject.object_class == object_class)
    
    if min_confidence is not None:
        query = query.filter(DetectedObject.confidence >= min_confidence)
    
    return query.offset(skip).limit(limit).all()

def create_detected_object(db: Session, detection: schemas.DetectedObjectCreate) -> DetectedObject:
    """Create a new detected object"""
    db_detection = DetectedObject(**detection.dict())
    db.add(db_detection)
    db.commit()
    db.refresh(db_detection)
    return db_detection

# ============================================================================
# BUSINESS INFO CRUD
# ============================================================================

def get_business(db: Session, business_id: int) -> Optional[BusinessInfo]:
    """Get business info by ID"""
    return db.query(BusinessInfo).filter(BusinessInfo.id == business_id).first()

def get_business_info(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    business_name: Optional[str] = None
) -> List[BusinessInfo]:
    """Get business information with optional filtering"""
    query = db.query(BusinessInfo)
    
    if business_name is not None:
        query = query.filter(BusinessInfo.business_name.ilike(f"%{business_name}%"))
    
    return query.offset(skip).limit(limit).all()

def create_business_info(db: Session, business: schemas.BusinessInfoCreate) -> BusinessInfo:
    """Create new business information"""
    db_business = BusinessInfo(**business.dict())
    db.add(db_business)
    db.commit()
    db.refresh(db_business)
    return db_business

# ============================================================================
# ANALYTICS FUNCTIONS
# ============================================================================

def get_channel_statistics(db: Session) -> List[Dict[str, Any]]:
    """Get comprehensive channel statistics"""
    results = db.query(
        TelegramChannel.id.label('channel_id'),
        TelegramChannel.channel_name,
        func.count(TelegramMessage.id).label('total_messages'),
        func.count(MediaFile.id).label('total_media_files'),
        func.count(DetectedObject.id).label('total_detected_objects'),
        func.avg(TelegramMessage.views).label('avg_views'),
        func.avg(TelegramMessage.forwards).label('avg_forwards'),
        func.avg(TelegramMessage.replies).label('avg_replies')
    ).outerjoin(
        TelegramMessage, TelegramChannel.id == TelegramMessage.channel_id
    ).outerjoin(
        MediaFile, TelegramMessage.id == MediaFile.message_id
    ).outerjoin(
        DetectedObject, TelegramMessage.id == DetectedObject.message_id
    ).group_by(
        TelegramChannel.id, TelegramChannel.channel_name
    ).all()
    
    return [{
        'channel_id': r.channel_id,
        'channel_name': r.channel_name,
        'total_messages': r.total_messages or 0,
        'total_media_files': r.total_media_files or 0,
        'total_detected_objects': r.total_detected_objects or 0,
        'avg_views': float(r.avg_views or 0),
        'avg_forwards': float(r.avg_forwards or 0),
        'avg_replies': float(r.avg_replies or 0)
    } for r in results]

def get_media_distribution(db: Session) -> List[Dict[str, Any]]:
    """Get media type distribution"""
    total_media = db.query(func.count(MediaFile.id)).scalar() or 1
    
    results = db.query(
        MediaFile.file_type,
        func.count(MediaFile.id).label('count')
    ).group_by(
        MediaFile.file_type
    ).all()
    
    return [{
        'media_type': r.file_type or 'unknown',
        'count': r.count,
        'percentage': round((r.count / total_media) * 100, 2)
    } for r in results]

def get_object_detection_summary(db: Session) -> List[Dict[str, Any]]:
    """Get object detection summary statistics"""
    results = db.query(
        DetectedObject.object_class,
        func.count(DetectedObject.id).label('count'),
        func.avg(DetectedObject.confidence).label('avg_confidence'),
        func.min(DetectedObject.confidence).label('min_confidence'),
        func.max(DetectedObject.confidence).label('max_confidence')
    ).group_by(
        DetectedObject.object_class
    ).order_by(
        desc('count')
    ).all()
    
    return [{
        'object_class': r.object_class,
        'count': r.count,
        'avg_confidence': round(float(r.avg_confidence), 3),
        'min_confidence': round(float(r.min_confidence), 3),
        'max_confidence': round(float(r.max_confidence), 3)
    } for r in results]

def get_business_insights(db: Session) -> Dict[str, Any]:
    """Get business intelligence insights"""
    total_businesses = db.query(func.count(BusinessInfo.id)).scalar() or 0
    
    businesses_with_contact = db.query(
        func.count(BusinessInfo.id)
    ).filter(
        BusinessInfo.contact_info.isnot(None)
    ).scalar() or 0
    
    businesses_with_address = db.query(
        func.count(BusinessInfo.id)
    ).filter(
        BusinessInfo.address.isnot(None)
    ).scalar() or 0
    
    businesses_with_pricing = db.query(
        func.count(BusinessInfo.id)
    ).filter(
        BusinessInfo.price.isnot(None)
    ).scalar() or 0
    
    # Get most common products
    common_products = db.query(
        BusinessInfo.product_name,
        func.count(BusinessInfo.id).label('count')
    ).filter(
        BusinessInfo.product_name.isnot(None)
    ).group_by(
        BusinessInfo.product_name
    ).order_by(
        desc('count')
    ).limit(10).all()
    
    # Get channels with businesses
    channels_with_businesses = db.query(
        TelegramChannel.channel_name
    ).join(
        TelegramMessage, TelegramChannel.id == TelegramMessage.channel_id
    ).join(
        BusinessInfo, TelegramMessage.id == BusinessInfo.message_id
    ).distinct().all()
    
    return {
        'total_businesses': total_businesses,
        'businesses_with_contact': businesses_with_contact,
        'businesses_with_address': businesses_with_address,
        'businesses_with_pricing': businesses_with_pricing,
        'most_common_products': [p.product_name for p in common_products],
        'channels_with_businesses': [c.channel_name for c in channels_with_businesses]
    }

def get_engagement_metrics(db: Session, channel_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get engagement metrics"""
    query = db.query(
        TelegramChannel.id.label('channel_id'),
        TelegramChannel.channel_name,
        func.sum(TelegramMessage.views).label('total_views'),
        func.sum(TelegramMessage.forwards).label('total_forwards'),
        func.sum(TelegramMessage.replies).label('total_replies'),
        func.avg(TelegramMessage.views).label('avg_views_per_message'),
        func.avg(TelegramMessage.forwards).label('avg_forwards_per_message'),
        func.avg(TelegramMessage.replies).label('avg_replies_per_message'),
        func.count(TelegramMessage.id).label('total_messages')
    ).join(
        TelegramMessage, TelegramChannel.id == TelegramMessage.channel_id
    ).group_by(
        TelegramChannel.id, TelegramChannel.channel_name
    )
    
    if channel_id is not None:
        query = query.filter(TelegramChannel.id == channel_id)
    
    results = query.all()
    
    return [{
        'channel_id': r.channel_id,
        'channel_name': r.channel_name,
        'total_views': r.total_views or 0,
        'total_forwards': r.total_forwards or 0,
        'total_replies': r.total_replies or 0,
        'avg_views_per_message': round(float(r.avg_views_per_message or 0), 2),
        'avg_forwards_per_message': round(float(r.avg_forwards_per_message or 0), 2),
        'avg_replies_per_message': round(float(r.avg_replies_per_message or 0), 2),
        'engagement_rate': round(
            ((r.total_forwards or 0) + (r.total_replies or 0)) / max(r.total_views or 1, 1) * 100, 2
        )
    } for r in results]

# ============================================================================
# ADVANCED ANALYTICS
# ============================================================================

def get_trending_objects(db: Session, days: int = 7) -> List[Dict[str, Any]]:
    """Get trending detected objects in the last N days"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    results = db.query(
        DetectedObject.object_class,
        func.count(DetectedObject.id).label('count'),
        func.avg(DetectedObject.confidence).label('avg_confidence')
    ).filter(
        DetectedObject.created_at >= cutoff_date
    ).group_by(
        DetectedObject.object_class
    ).order_by(
        desc('count')
    ).limit(20).all()
    
    return [{
        'object_class': r.object_class,
        'count': r.count,
        'avg_confidence': round(float(r.avg_confidence), 3)
    } for r in results]

def get_channel_activity_timeline(db: Session, channel_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """Get channel activity timeline"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    results = db.query(
        func.date(TelegramMessage.date).label('date'),
        func.count(TelegramMessage.id).label('message_count'),
        func.sum(TelegramMessage.views).label('total_views'),
        func.count(MediaFile.id).label('media_count')
    ).outerjoin(
        MediaFile, TelegramMessage.id == MediaFile.message_id
    ).filter(
        and_(
            TelegramMessage.channel_id == channel_id,
            TelegramMessage.date >= cutoff_date
        )
    ).group_by(
        func.date(TelegramMessage.date)
    ).order_by(
        'date'
    ).all()
    
    return [{
        'date': str(r.date),
        'message_count': r.message_count,
        'total_views': r.total_views or 0,
        'media_count': r.media_count or 0
    } for r in results]