from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class TelegramChannel(Base):
    """Model for storing Telegram channel information"""
    __tablename__ = 'telegram_channels'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_name = Column(String(255), unique=True, nullable=False)
    channel_url = Column(String(500), nullable=False)
    channel_id = Column(String(100), unique=True)
    title = Column(String(500))
    description = Column(Text)
    participants_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    messages = relationship("TelegramMessage", back_populates="channel")

class TelegramMessage(Base):
    """Model for storing Telegram messages"""
    __tablename__ = 'telegram_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, nullable=False)
    channel_id = Column(Integer, ForeignKey('telegram_channels.id'), nullable=False)
    sender_id = Column(String(100))
    message_text = Column(Text)
    date = Column(DateTime, nullable=False)
    views = Column(Integer, default=0)
    forwards = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    is_reply = Column(Boolean, default=False)
    reply_to_msg_id = Column(Integer)
    has_media = Column(Boolean, default=False)
    media_type = Column(String(50))  # photo, video, document, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    channel = relationship("TelegramChannel", back_populates="messages")
    media_files = relationship("MediaFile", back_populates="message")
    detected_objects = relationship("DetectedObject", back_populates="message")

class MediaFile(Base):
    """Model for storing media files from Telegram messages"""
    __tablename__ = 'media_files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey('telegram_messages.id'), nullable=False)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))  # image, video, document
    mime_type = Column(String(100))
    width = Column(Integer)
    height = Column(Integer)
    duration = Column(Float)  # for videos
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    message = relationship("TelegramMessage", back_populates="media_files")
    detected_objects = relationship("DetectedObject", back_populates="media_file")

class DetectedObject(Base):
    """Model for storing YOLO detected objects"""
    __tablename__ = 'detected_objects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey('telegram_messages.id'), nullable=False)
    media_file_id = Column(Integer, ForeignKey('media_files.id'), nullable=False)
    object_class = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    bbox_x = Column(Float, nullable=False)
    bbox_y = Column(Float, nullable=False)
    bbox_width = Column(Float, nullable=False)
    bbox_height = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("TelegramMessage", back_populates="detected_objects")
    media_file = relationship("MediaFile", back_populates="detected_objects")

class BusinessInfo(Base):
    """Model for storing extracted business information"""
    __tablename__ = 'business_info'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey('telegram_messages.id'), nullable=False)
    business_name = Column(String(500))
    product_name = Column(String(500))
    price = Column(String(200))
    contact_info = Column(Text)
    address = Column(Text)
    opening_hours = Column(Text)
    delivery_info = Column(Text)
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    message = relationship("TelegramMessage")