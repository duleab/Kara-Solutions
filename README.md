# Ethiopian Medical Business Telegram Analytics Pipeline

## 🚀 Enhanced Implementation

This is an enhanced version of the Ethiopian Medical Business Telegram Analytics Pipeline, inspired by the Kara-Solutions implementation but with significant improvements and additional features.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Data Pipeline](#data-pipeline)
- [Object Detection](#object-detection)
- [Analytics](#analytics)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This project provides a comprehensive solution for analyzing Ethiopian medical businesses through Telegram channel data. It combines data scraping, natural language processing, computer vision, and analytics to extract valuable business insights.

### Key Capabilities

- **Telegram Data Scraping**: Automated collection of messages and media from Telegram channels
- **Business Information Extraction**: AI-powered extraction of business details from text
- **Object Detection**: YOLO-based detection of medical products and equipment in images
- **Analytics API**: RESTful API for accessing insights and statistics
- **Data Pipeline**: Automated ETL processes for data cleaning and transformation
- **Real-time Monitoring**: Live tracking of channel activities and trends

## ✨ Features

### 🔍 Data Collection
- Multi-channel Telegram scraping with rate limiting
- Media file download and organization
- Metadata extraction and enrichment
- Incremental data updates

### 🧠 AI-Powered Analysis
- Business information extraction using NLP
- Medical product detection with YOLOv8
- Sentiment analysis of messages
- Trend identification and forecasting

### 📊 Analytics & Insights
- Channel performance metrics
- Business discovery and profiling
- Market trend analysis
- Engagement pattern recognition

### 🌐 API & Integration
- FastAPI-based REST API
- Real-time data access
- Comprehensive documentation
- Easy integration with external systems

## Project Overview

The pipeline consists of several key components:
1. **Data Scraping**: Automated Telegram data collection from medical business channels
2. **Data Modeling**: dbt-based data transformation and warehouse modeling
3. **Object Detection**: YOLOv8 integration for image analysis (Task 3)
4. **Analytics API**: FastAPI-based analytical endpoints (Task 4)
5. **Orchestration**: Dagster-based pipeline orchestration (Task 5)

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL (recommended) or SQLite for development
- Telegram API credentials

### Installation

1. **Clone and setup the project:**
```bash
cd d:\10-Academy\Week7
pip install -r requirements.txt
```

### Option 1: Complete Integration Pipeline (Recommended)

1. **Setup Environment**
   ```bash
   python setup.py
   ```

2. **Configure Environment Variables**
   ```bash
   # .env file is already created, edit with your credentials
   # Edit .env with your Telegram API credentials and database settings
   ```

3. **Run Complete Integration** (for scraped data)
   ```bash
   python run_integration.py
   ```

4. **Analyze Results**
   ```bash
   python analyze_results.py
   ```

### Option 2: Manual Step-by-Step Process

1. **Setup Environment**
   ```bash
   python setup.py
   ```

2. **Migrate Scraped Data**
   ```bash
   python migrate_scraped_data.py --data-path "./Technical Content/telegram_data"
   ```

3. **Run dbt Transformations**
   ```bash
   cd dbt_project
   dbt deps
   dbt run
   dbt test
   ```

4. **Run Live Scraping** (optional)
   ```bash
   python run_scraper.py --limit 100 --days-back 30
   ```

### Option 3: Traditional Setup (Legacy)

1. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

2. **Setup Telegram API credentials:**
   - Go to https://my.telegram.org/apps
   - Create a new application
   - Add `API_ID`, `API_HASH`, and `PHONE_NUMBER` to your `.env` file

3. **Initialize the database:**
```bash
python run_scraper.py --init-db
```

## Scraped Data Integration

### Overview
This project now includes complete integration for your pre-scraped Telegram data from Ethiopian medical business channels:
- **CheMed123**: Pharmaceutical delivery service
- **lobelia4cosmetics**: Pharmacy and cosmetics store
- **tikvahpharma**: Medical products and services
- **zoepharmacy**: Pharmaceutical products and health services

### Integration Features
- **Automated Data Migration**: Converts scraped text files to structured database records
- **Business Intelligence Extraction**: Automatically extracts prices, contact info, addresses, and delivery details
- **Media File Processing**: Catalogs and processes downloaded images and videos
- **dbt Pipeline Integration**: Flows seamlessly through existing transformation models
- **Analytics Dashboard**: Generates insights and visualizations

### Data Processing Pipeline
1. **Raw Data Import**: Processes `messages.txt` files and media from each channel
2. **Business Info Extraction**: Uses regex patterns to extract:
   - Product names and prices (3000-6500 Birr range)
   - Contact information (phone numbers, Telegram handles)
   - Business addresses and opening hours
   - Delivery information and fees
3. **Database Storage**: Saves to structured tables (channels, messages, business_info, media_files)
4. **dbt Transformations**: Applies data quality checks and creates analytics models
5. **Insight Generation**: Produces business intelligence reports and visualizations

### Generated Analytics
- **Channel Performance**: Message counts, engagement metrics, business coverage
- **Price Analysis**: Product pricing trends, channel comparisons, top products
- **Business Intelligence**: Contact coverage, delivery options, location analysis
- **Activity Trends**: Daily posting patterns, media vs text content

## Task 1: Data Scraping and Collection

### Overview
Automated scraping of Ethiopian medical business data from Telegram channels:
- `CheMed123`
- `lobelia4cosmetics`
- `tikvahpharma`
- `zoepharmacy`

### Features
- **Message Collection**: Text, media, engagement metrics
- **Business Information Extraction**: Names, prices, contacts, addresses
- **Media Download**: Images and videos for YOLO analysis
- **Rate Limiting**: Respectful API usage
- **Data Quality**: Validation and cleaning

### Usage

**Basic scraping (last 30 days, 100 messages per channel):**
```bash
python run_scraper.py
```

**Custom parameters:**
```bash
# Scrape last 7 days, 50 messages per channel
python run_scraper.py --days 7 --limit 50

# Initialize database and scrape
python run_scraper.py --init-db --days 30 --limit 200
```

### Data Schema

The scraper populates these tables:
- `telegram_channels`: Channel metadata
- `telegram_messages`: Message content and metrics
- `media_files`: Downloaded media information
- `business_info`: Extracted business details
- `detected_objects`: YOLO detection results (populated in Task 3)

### Business Information Extraction

The scraper automatically extracts:
- **Prices**: Ethiopian Birr amounts using regex patterns
- **Contact Info**: Phone numbers (Ethiopian format)
- **Delivery Info**: Delivery availability and terms
- **Addresses**: Location information with city detection
- **Business Categories**: Pharmacy, Cosmetics, Supplements

## Task 2: Data Modeling and Transformation

### Overview
Implements a modern data warehouse using dbt with staging and mart layers following dimensional modeling principles.

### Architecture

```
Raw Data (Telegram API)
    ↓
Staging Layer (Data Cleaning)
    ↓
Marts Layer (Business Logic)
    ↓
Analytics & Reporting
```

### dbt Project Structure

```
dbt_project/
├── models/
│   ├── staging/          # Data cleaning and standardization
│   │   ├── sources.yml   # Source definitions
│   │   ├── stg_telegram_channels.sql
│   │   ├── stg_telegram_messages.sql
│   │   └── stg_business_info.sql
│   └── marts/            # Business logic and analytics
│       ├── core/
│       │   └── fact_message_analytics.sql
│       └── business/
│           ├── business_summary.sql
│           └── daily_activity_trends.sql
├── tests/               # Data quality tests
├── macros/             # Reusable SQL functions
└── dbt_project.yml     # Project configuration
```

### Key Models

#### Staging Layer
- **`stg_telegram_channels`**: Cleaned channel information with categorization
- **`stg_telegram_messages`**: Standardized messages with engagement metrics
- **`stg_business_info`**: Processed business data with quality indicators

#### Marts Layer
- **`fact_message_analytics`**: Core fact table with all message and business data
- **`business_summary`**: Aggregated business intelligence by channel/category
- **`daily_activity_trends`**: Time-series analysis with moving averages

### Setup dbt

1. **Install dbt packages:**
```bash
cd dbt_project
dbt deps
```

2. **Configure database connection:**
   - Edit `profiles.yml` with your database credentials
   - Or set environment variables in `.env`

3. **Test connection:**
```bash
dbt debug
```

### Running dbt

**Full pipeline:**
```bash
cd dbt_project

# Run all models
dbt run

# Run tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

**Incremental development:**
```bash
# Run specific model
dbt run --select stg_telegram_messages

# Run model and downstream dependencies
dbt run --select stg_telegram_messages+

# Run only changed models
dbt run --select state:modified+
```

### Data Quality

The project includes comprehensive data quality tests:
- **Schema tests**: Uniqueness, not null, relationships
- **Custom tests**: Date ranges, price reasonableness, engagement consistency
- **dbt-expectations**: Advanced data quality checks

### Key Metrics and KPIs

#### Business Metrics
- Message volume and engagement by channel
- Business information completeness
- Price distribution and trends
- Geographic distribution of businesses
- Delivery service availability

#### Engagement Analytics
- Views, forwards, and replies tracking
- Engagement score calculation
- Time-based activity patterns
- Content type performance

#### Trend Analysis
- Daily/weekly/monthly activity trends
- Moving averages and change detection
- Seasonal patterns
- Channel performance comparison

## Data Pipeline Workflow

1. **Extract**: Telegram scraper collects raw data
2. **Load**: Data stored in PostgreSQL/SQLite
3. **Transform**: dbt processes data through staging to marts
4. **Quality**: Automated testing ensures data integrity
5. **Analyze**: Business intelligence through mart models

## Monitoring and Logging

- **Scraper logs**: `logs/telegram_scraper.log`
- **dbt logs**: `dbt_project/logs/`
- **Database monitoring**: Connection health and performance

## Next Steps

After completing Tasks 1 and 2:
- **Task 3**: Implement YOLOv8 object detection on scraped images
- **Task 4**: Build FastAPI analytical endpoints
- **Task 5**: Orchestrate with Dagster
- **Task 6**: Containerize with Docker

## Troubleshooting

### Common Issues

1. **Telegram API Rate Limiting**:
   - Reduce `--limit` parameter
   - Increase delays in scraper
   - Use multiple API accounts

2. **Database Connection Issues**:
   - Check `.env` configuration
   - Verify database is running
   - Test connection with `dbt debug`

3. **dbt Model Failures**:
   - Check `dbt_project/logs/` for detailed errors
   - Verify source data exists
   - Run `dbt test` to identify issues

### Performance Optimization

- Use PostgreSQL for better performance
- Implement incremental models for large datasets
- Add database indexes on frequently queried columns
- Monitor query performance and optimize


