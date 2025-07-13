#!/usr/bin/env python3
"""
Pydantic schemas for data validation and serialization.

This module defines the data models used for API request/response validation,
following the structure from the Kara-Solutions repository with enhancements.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class MediaType(str, Enum):
    """Enumeration for media types"""
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    STICKER = "sticker"
    ANIMATION = "animation"

class FileType(str, Enum):
    """Enumeration for file types"""
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"

# ============================================================================
# BASE SCHEMAS
# ============================================================================

class TelegramChannelBase(BaseModel):
    """Base schema for Telegram channels"""
    channel_name: str = Field(..., min_length=1, max_length=255)
    channel_url: str = Field(..., min_length=1, max_length=500)
    channel_id: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    participants_count: Optional[int] = Field(None, ge=0)

class TelegramMessageBase(BaseModel):
    """Base schema for Telegram messages"""
    message_id: int = Field(..., ge=1)
    channel_id: int = Field(..., ge=1)
    sender_id: Optional[str] = Field(None, max_length=100)
    message_text: Optional[str] = None
    date: datetime
    views: Optional[int] = Field(0, ge=0)
    forwards: Optional[int] = Field(0, ge=0)
    replies: Optional[int] = Field(0, ge=0)
    is_reply: bool = False
    reply_to_msg_id: Optional[int] = Field(None, ge=1)
    has_media: bool = False
    media_type: Optional[MediaType] = None

class MediaFileBase(BaseModel):
    """Base schema for media files"""
    message_id: int = Field(..., ge=1)
    file_name: str = Field(..., min_length=1, max_length=500)
    file_path: str = Field(..., min_length=1, max_length=1000)
    file_size: Optional[int] = Field(None, ge=0)
    file_type: Optional[FileType] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    width: Optional[int] = Field(None, ge=0)
    height: Optional[int] = Field(None, ge=0)
    duration: Optional[float] = Field(None, ge=0.0)

class DetectedObjectBase(BaseModel):
    """Base schema for detected objects"""
    message_id: int = Field(..., ge=1)
    media_file_id: int = Field(..., ge=1)
    object_class: str = Field(..., min_length=1, max_length=100)
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox_x: float = Field(..., ge=0.0)
    bbox_y: float = Field(..., ge=0.0)
    bbox_width: float = Field(..., gt=0.0)
    bbox_height: float = Field(..., gt=0.0)

class BusinessInfoBase(BaseModel):
    """Base schema for business information"""
    message_id: int = Field(..., ge=1)
    business_name: Optional[str] = Field(None, max_length=500)
    product_name: Optional[str] = Field(None, max_length=500)
    price: Optional[str] = Field(None, max_length=200)
    contact_info: Optional[str] = None
    address: Optional[str] = None
    opening_hours: Optional[str] = None
    delivery_info: Optional[str] = None

# ============================================================================
# CREATE SCHEMAS
# ============================================================================

class TelegramChannelCreate(TelegramChannelBase):
    """Schema for creating a new Telegram channel"""
    pass

class TelegramMessageCreate(TelegramMessageBase):
    """Schema for creating a new Telegram message"""
    pass

class MediaFileCreate(MediaFileBase):
    """Schema for creating a new media file"""
    pass

class DetectedObjectCreate(DetectedObjectBase):
    """Schema for creating a new detected object"""
    pass

class BusinessInfoCreate(BusinessInfoBase):
    """Schema for creating new business information"""
    pass

# ============================================================================
# RESPONSE SCHEMAS (with relationships)
# ============================================================================

class DetectedObject(DetectedObjectBase):
    """Schema for detected object responses"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MediaFile(MediaFileBase):
    """Schema for media file responses"""
    id: int
    created_at: datetime
    detected_objects: List[DetectedObject] = []

    class Config:
        from_attributes = True

class BusinessInfo(BusinessInfoBase):
    """Schema for business information responses"""
    id: int
    extracted_at: datetime

    class Config:
        from_attributes = True

class TelegramMessage(TelegramMessageBase):
    """Schema for Telegram message responses"""
    id: int
    created_at: datetime
    media_files: List[MediaFile] = []
    detected_objects: List[DetectedObject] = []
    business_info: List[BusinessInfo] = []

    class Config:
        from_attributes = True

class TelegramChannel(TelegramChannelBase):
    """Schema for Telegram channel responses"""
    id: int
    created_at: datetime
    updated_at: datetime
    messages: List[TelegramMessage] = []

    class Config:
        from_attributes = True

# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class ChannelStatistics(BaseModel):
    """Schema for channel statistics"""
    channel_id: int
    channel_name: str
    total_messages: int
    total_media_files: int
    total_detected_objects: int
    avg_views: float
    avg_forwards: float
    avg_replies: float
    most_common_media_type: Optional[str]
    most_detected_object: Optional[str]

class MediaDistribution(BaseModel):
    """Schema for media distribution statistics"""
    media_type: str
    count: int
    percentage: float

class ObjectDetectionSummary(BaseModel):
    """Schema for object detection summary"""
    object_class: str
    count: int
    avg_confidence: float
    min_confidence: float
    max_confidence: float

class BusinessInsights(BaseModel):
    """Schema for business insights"""
    total_businesses: int
    businesses_with_contact: int
    businesses_with_address: int
    businesses_with_pricing: int
    most_common_products: List[str]
    channels_with_businesses: List[str]

class EngagementMetrics(BaseModel):
    """Schema for engagement metrics"""
    channel_id: Optional[int]
    channel_name: Optional[str]
    total_views: int
    total_forwards: int
    total_replies: int
    avg_views_per_message: float
    avg_forwards_per_message: float
    avg_replies_per_message: float
    engagement_rate: float

# ============================================================================
# VALIDATORS
# ============================================================================

@validator('confidence')
def validate_confidence(cls, v):
    """Validate confidence score is between 0 and 1"""
    if not 0.0 <= v <= 1.0:
        raise ValueError('Confidence must be between 0.0 and 1.0')
    return v

@validator('bbox_x', 'bbox_y')
def validate_bbox_coordinates(cls, v):
    """Validate bounding box coordinates are non-negative"""
    if v < 0:
        raise ValueError('Bounding box coordinates must be non-negative')
    return v

@validator('bbox_width', 'bbox_height')
def validate_bbox_dimensions(cls, v):
    """Validate bounding box dimensions are positive"""
    if v <= 0:
        raise ValueError('Bounding box dimensions must be positive')
    return v

# Add validators to the appropriate classes
DetectedObjectBase.validate_confidence = validate_confidence
DetectedObjectBase.validate_bbox_coordinates = validate_bbox_coordinates
DetectedObjectBase.validate_bbox_dimensions = validate_bbox_dimensions