# Ethiopian Medical Business Telegram Analytics Platform

A comprehensive data product that collects, processes, and analyzes medical-related content from Ethiopian Telegram channels. This platform implements modern data engineering practices to deliver actionable insights for healthcare business intelligence.

## Architecture Overview

This project implements a complete end-to-end data pipeline with the following components:

- **Data Collection**: Robust Telegram scraping using Telethon API
- **Data Storage**: PostgreSQL database with SQLAlchemy ORM
- **Data Transformation**: dbt for ELT processes and star schema modeling
- **Machine Learning**: YOLO v8 for medical product object detection
- **API Layer**: FastAPI for analytical endpoints with comprehensive validation
- **Orchestration**: Dagster for pipeline automation and scheduling
- **Containerization**: Docker for reproducible deployments

## Table of Contents

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

## Overview

This project provides a comprehensive solution for analyzing Ethiopian medical businesses through Telegram channel data. It combines data scraping, natural language processing, computer vision, and analytics to extract valuable business insights.

### Key Capabilities

- **Telegram Data Scraping**: Automated collection of messages and media from Telegram channels
- **Business Information Extraction**: AI-powered extraction of business details from text
- **Object Detection**: YOLO-based detection of medical products and equipment in images
- **Analytics API**: RESTful API for accessing insights and statistics
- **Data Pipeline**: Automated ETL processes for data cleaning and transformation
- **Real-time Monitoring**: Live tracking of channel activities and trends

## Key Features

### Data Collection
- Multi-channel Telegram scraping with rate limiting
- Media file download and organization
- Metadata extraction and enrichment
- Incremental data updates

### AI-Powered Analysis
- Business information extraction using NLP
- **Enhanced YOLO Object Detection**: YOLOv8/YOLOv11 integration for medical equipment detection
- Medical relevance scoring for detected objects
- Confidence-based quality assessment
- Sentiment analysis of messages
- Trend identification and forecasting

### Analytics and Insights
- Channel performance metrics
- Business discovery and profiling
- **Object Detection Analytics**: Comprehensive insights from YOLO detections
- Medical relevance analysis
- Detection quality metrics and trends
- Market trend analysis
- Engagement pattern recognition

### API and Integration
- FastAPI-based REST API with enhanced object detection endpoints
- Real-time data access
- **YOLO Analytics API**: Specialized endpoints for object detection insights
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

## YOLO Object Detection Integration

### Overview
Comprehensive computer vision integration using YOLOv8/YOLOv11 for medical equipment and product detection in Telegram media files.

### Key Features
- **Enhanced Object Detection**: YOLOv8/YOLOv11 models for medical context
- **Medical Relevance Scoring**: Specialized scoring for healthcare objects
- **Confidence-based Quality Assessment**: Multi-tier confidence evaluation
- **Database Integration**: Seamless storage of detection results
- **Analytics Pipeline**: dbt models for detection insights
- **API Endpoints**: RESTful access to detection analytics

### Supported Object Categories
- **Medical Tools**: Scissors, syringes, stethoscopes
- **Containers**: Medicine bottles, specimen cups
- **People**: Patients, medical staff
- **Documents & Devices**: Medical records, phones
- **Other**: General objects with medical context scoring

### Detection Pipeline
1. **Image Processing**: Automated detection on images in `data/raw/images`
2. **Result Storage**: Annotated images saved to `data/raw/DETECTED results`
3. **Database Integration**: Detection metadata stored in PostgreSQL
4. **Analytics Generation**: dbt models create business intelligence
5. **API Access**: RESTful endpoints for detection insights

### Usage

#### Quick Start - Complete Integration
```bash
# Run complete YOLO integration pipeline
python run_complete_yolo_integration.py
```

#### Manual Object Detection
```bash
# Run enhanced object detection script
python scripts/enhanced_object_detection.py
```

#### API Access
```bash
# Start the API server
python run_api.py

# Access detection endpoints
curl http://localhost:8000/detections/
curl http://localhost:8000/analytics/object-detection-insights
curl http://localhost:8000/analytics/medical-relevance-score
```

### Detection Analytics
- **Daily Detection Summary**: Object counts and confidence by channel
- **Object Popularity Rankings**: Most detected objects across channels
- **Channel Detection Patterns**: Unique detection profiles per channel
- **Medical Relevance Analysis**: Healthcare-specific object scoring
- **Quality Metrics**: Confidence distribution and detection trends

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

## Data Model

### Star Schema Design

The data warehouse implements a star schema optimized for analytical queries:

#### Fact Tables
- `fact_message_analytics`: Core message metrics with foreign keys to dimensions
- Contains engagement metrics, timestamps, and business indicators

#### Dimension Tables
- `dim_channels`: Channel information, metadata, and categorization
- `dim_dates`: Time dimension with business logic and Ethiopian calendar
- `dim_objects`: Detected objects from YOLO with confidence scores

#### Staging Tables
- `stg_telegram_channels`: Cleaned and validated channel data
- `stg_telegram_messages`: Processed message data with quality checks
- `stg_detected_objects`: Object detection results with metadata

## Usage Guide

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

## Monitoring and Observability

### Dagster UI
Access the Dagster UI at `http://localhost:3000` to:
- Monitor pipeline runs and execution status
- View asset lineage and dependencies
- Schedule and trigger jobs manually
- Debug failures with detailed logs

### API Monitoring
- Health check endpoint: `/health`
- Metrics endpoint: `/metrics`
- Interactive API documentation: `/docs`
- Real-time performance monitoring

## Testing Framework

```bash
# Execute test suite
pytest tests/

# Run with coverage reporting
pytest --cov=api tests/

# Execute dbt data quality tests
cd dbt_project
dbt test

# Run integration tests
pytest tests/integration/
```

## Deployment Options

### Production Deployment

1. **Environment Configuration**
   ```bash
   export ENVIRONMENT=production
   export DATABASE_URL=postgresql://user:pass@host:port/db
   export TELEGRAM_API_ID=your_api_id
   export TELEGRAM_API_HASH=your_api_hash
   ```

2. **Docker Production Deployment**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Kubernetes Deployment**
   ```bash
   kubectl apply -f k8s/
   kubectl get pods -n telegram-analytics
   ```

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

## Data Sources

- **Primary**: Ethiopian medical business Telegram channels
- **Secondary**: Public health information channels  
- **Supplementary**: Medical equipment supplier channels
- **Validation**: Cross-referenced with official medical databases

## Contributing Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request with detailed description
6. Ensure all tests pass and code follows style guidelines

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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

## Educational Purpose

This project is for educational purposes as part of the 10 Academy Data Engineering program.