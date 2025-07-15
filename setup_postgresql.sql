-- PostgreSQL Database Setup for Telegram Analytics
-- Run this script to create the database and tables

-- Create database (run this as superuser)
-- CREATE DATABASE telegram_warehouse;

-- Connect to telegram_warehouse database and run the following:

-- Create schema
CREATE SCHEMA IF NOT EXISTS public;

-- Create telegram_channels table
CREATE TABLE IF NOT EXISTS telegram_channels (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    title TEXT,
    about TEXT,
    participants_count INTEGER DEFAULT 0,
    is_broadcast BOOLEAN DEFAULT FALSE,
    is_megagroup BOOLEAN DEFAULT FALSE,
    created_date TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create telegram_messages table
CREATE TABLE IF NOT EXISTS telegram_messages (
    id SERIAL PRIMARY KEY,
    channel_username VARCHAR(255) NOT NULL,
    sender_id BIGINT,
    text TEXT,
    date TIMESTAMP NOT NULL,
    sender_username VARCHAR(255),
    sender_first_name VARCHAR(255),
    sender_last_name VARCHAR(255),
    views INTEGER DEFAULT 0,
    forwards INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    is_reply BOOLEAN DEFAULT FALSE,
    reply_to_msg_id BIGINT,
    has_media BOOLEAN DEFAULT FALSE,
    media_type VARCHAR(100),
    media_file_path TEXT,
    raw_data JSONB,
    FOREIGN KEY (channel_username) REFERENCES telegram_channels(username)
);

-- Create business_info table
CREATE TABLE IF NOT EXISTS business_info (
    id SERIAL PRIMARY KEY,
    channel_username VARCHAR(255) NOT NULL,
    message_id BIGINT NOT NULL,
    business_name TEXT,
    phone_number VARCHAR(50),
    service_type VARCHAR(255),
    location TEXT,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_username) REFERENCES telegram_channels(username),
    FOREIGN KEY (message_id) REFERENCES telegram_messages(id)
);

-- Create media_files table
CREATE TABLE IF NOT EXISTS media_files (
    id SERIAL PRIMARY KEY,
    channel_username VARCHAR(255) NOT NULL,
    message_id BIGINT NOT NULL,
    file_path TEXT NOT NULL,
    media_type VARCHAR(100),
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_username) REFERENCES telegram_channels(username),
    FOREIGN KEY (message_id) REFERENCES telegram_messages(id)
);

-- Create detected_objects table
CREATE TABLE IF NOT EXISTS detected_objects (
    id SERIAL PRIMARY KEY,
    message_id BIGINT NOT NULL,
    media_file_id INTEGER NOT NULL,
    object_class VARCHAR(100),
    confidence DECIMAL(5,4),
    bbox_x INTEGER,
    bbox_y INTEGER,
    bbox_width INTEGER,
    bbox_height INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES telegram_messages(id),
    FOREIGN KEY (media_file_id) REFERENCES media_files(id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_telegram_messages_channel ON telegram_messages(channel_username);
CREATE INDEX IF NOT EXISTS idx_telegram_messages_date ON telegram_messages(date);
CREATE INDEX IF NOT EXISTS idx_telegram_messages_sender ON telegram_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_business_info_channel ON business_info(channel_username);
CREATE INDEX IF NOT EXISTS idx_media_files_message ON media_files(message_id);
CREATE INDEX IF NOT EXISTS idx_detected_objects_message ON detected_objects(message_id);

-- Grant permissions (adjust as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

COMMIT;