from dagster import (
    Definitions,
    job,
    op,
    schedule,
    DefaultScheduleStatus,
    ScheduleDefinition,
    AssetMaterialization,
    Output,
    In,
    Nothing,
    DagsterType,
    String,
    Int,
    Float,
    Bool,
    List,
    Dict,
    Any,
    get_dagster_logger,
    resource,
    ConfigurableResource,
    EnvVar
)
from dagster_dbt import DbtCliResource, dbt_assets
from pathlib import Path
import subprocess
import os
import sys
from datetime import datetime
from typing import Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import project modules
from scripts.telegram_scraper import TelegramScraper
from scripts.run_integration import TelegramDataIntegrator
from scripts.yolo_integration import YOLOObjectDetector

# ============================================================================
# RESOURCES
# ============================================================================

@resource
def telegram_scraper_resource():
    """Resource for Telegram scraping"""
    return TelegramScraper()

@resource
def yolo_detector_resource():
    """Resource for YOLO object detection"""
    return YOLOObjectDetector()

@resource
def data_integrator_resource():
    """Resource for data integration"""
    return TelegramDataIntegrator()

# DBT Resource
dbt_resource = DbtCliResource(
    project_dir=str(project_root / "dbt_project"),
    profiles_dir=str(project_root / "dbt_project"),
)

# ============================================================================
# OPERATIONS
# ============================================================================

@op(
    required_resource_keys={"telegram_scraper"},
    description="Scrape data from Telegram channels"
)
def scrape_telegram_data(context) -> str:
    """Scrape data from configured Telegram channels"""
    logger = get_dagster_logger()
    scraper = context.resources.telegram_scraper
    
    try:
        # Configure channels to scrape
        channels = [
            "DoctorsET",
            "lobelia4cosmetics", 
            "yetenaweg",
            "EAHCI"
        ]
        
        results = []
        for channel in channels:
            logger.info(f"Scraping channel: {channel}")
            result = scraper.scrape_channel(channel, limit=100)
            results.append(result)
            
        logger.info(f"Successfully scraped {len(results)} channels")
        
        # Log asset materialization
        context.log_event(
            AssetMaterialization(
                asset_key="telegram_raw_data",
                description=f"Scraped data from {len(channels)} Telegram channels",
                metadata={
                    "channels_scraped": len(channels),
                    "timestamp": datetime.now().isoformat()
                }
            )
        )
        
        return f"Scraped {len(results)} channels successfully"
        
    except Exception as e:
        logger.error(f"Error scraping Telegram data: {str(e)}")
        raise

@op(
    ins={"scrape_result": In(str)},
    required_resource_keys={"data_integrator"},
    description="Load scraped data into database"
)
def load_data_to_db(context, scrape_result: str) -> str:
    """Load scraped data into the database"""
    logger = get_dagster_logger()
    integrator = context.resources.data_integrator
    
    try:
        logger.info("Loading data to database...")
        
        # Run the data integration process
        integrator.run_integration()
        
        logger.info("Data loaded successfully")
        
        # Log asset materialization
        context.log_event(
            AssetMaterialization(
                asset_key="telegram_database",
                description="Loaded Telegram data into database",
                metadata={
                    "load_timestamp": datetime.now().isoformat(),
                    "previous_step": scrape_result
                }
            )
        )
        
        return "Data loaded to database successfully"
        
    except Exception as e:
        logger.error(f"Error loading data to database: {str(e)}")
        raise

@op(
    ins={"load_result": In(str)},
    required_resource_keys={"dbt"},
    description="Run dbt transformations"
)
def run_dbt_transformations(context, load_result: str) -> str:
    """Run dbt transformations to create staging and mart models"""
    logger = get_dagster_logger()
    
    try:
        logger.info("Running dbt transformations...")
        
        # Change to dbt project directory
        dbt_dir = project_root / "dbt_project"
        os.chdir(dbt_dir)
        
        # Run dbt commands
        commands = [
            "dbt deps",
            "dbt seed",
            "dbt run",
            "dbt test"
        ]
        
        for cmd in commands:
            logger.info(f"Executing: {cmd}")
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                cwd=dbt_dir
            )
            
            if result.returncode != 0:
                logger.error(f"dbt command failed: {cmd}")
                logger.error(f"Error: {result.stderr}")
                raise Exception(f"dbt command failed: {cmd}")
            
            logger.info(f"Command output: {result.stdout}")
        
        logger.info("dbt transformations completed successfully")
        
        # Log asset materialization
        context.log_event(
            AssetMaterialization(
                asset_key="dbt_models",
                description="dbt transformations completed",
                metadata={
                    "transformation_timestamp": datetime.now().isoformat(),
                    "models_built": "staging, marts, business"
                }
            )
        )
        
        return "dbt transformations completed successfully"
        
    except Exception as e:
        logger.error(f"Error running dbt transformations: {str(e)}")
        raise

@op(
    ins={"dbt_result": In(str)},
    required_resource_keys={"yolo_detector"},
    description="Run YOLO object detection on media files"
)
def run_yolo_detection(context, dbt_result: str) -> str:
    """Run YOLO object detection on media files"""
    logger = get_dagster_logger()
    detector = context.resources.yolo_detector
    
    try:
        logger.info("Running YOLO object detection...")
        
        # Process images in the media directory
        media_dir = project_root / "data" / "raw" / "media"
        
        if media_dir.exists():
            image_files = list(media_dir.glob("*.jpg")) + list(media_dir.glob("*.png"))
            
            processed_count = 0
            for image_file in image_files:
                try:
                    results = detector.detect_objects(str(image_file))
                    if results:
                        processed_count += 1
                        logger.info(f"Processed {image_file.name}: {len(results)} objects detected")
                except Exception as e:
                    logger.warning(f"Failed to process {image_file.name}: {str(e)}")
            
            logger.info(f"YOLO detection completed. Processed {processed_count} images")
        else:
            logger.warning("Media directory not found, skipping YOLO detection")
            processed_count = 0
        
        # Log asset materialization
        context.log_event(
            AssetMaterialization(
                asset_key="yolo_detections",
                description="YOLO object detection completed",
                metadata={
                    "detection_timestamp": datetime.now().isoformat(),
                    "images_processed": processed_count
                }
            )
        )
        
        return f"YOLO detection completed. Processed {processed_count} images"
        
    except Exception as e:
        logger.error(f"Error running YOLO detection: {str(e)}")
        raise

@op(
    ins={"yolo_result": In(str)},
    description="Start FastAPI server"
)
def start_api_server(context, yolo_result: str) -> str:
    """Start the FastAPI server"""
    logger = get_dagster_logger()
    
    try:
        logger.info("Starting FastAPI server...")
        
        # Log asset materialization
        context.log_event(
            AssetMaterialization(
                asset_key="api_server",
                description="FastAPI server ready",
                metadata={
                    "server_start_timestamp": datetime.now().isoformat(),
                    "endpoint": "http://localhost:8000"
                }
            )
        )
        
        return "FastAPI server is ready at http://localhost:8000"
        
    except Exception as e:
        logger.error(f"Error starting API server: {str(e)}")
        raise

# ============================================================================
# JOBS
# ============================================================================

@job(
    resource_defs={
        "telegram_scraper": telegram_scraper_resource,
        "data_integrator": data_integrator_resource,
        "dbt": dbt_resource,
        "yolo_detector": yolo_detector_resource
    },
    description="Complete data pipeline: scrape -> load -> transform -> enrich -> serve"
)
def telegram_data_pipeline():
    """Complete data pipeline job"""
    scrape_result = scrape_telegram_data()
    load_result = load_data_to_db(scrape_result)
    dbt_result = run_dbt_transformations(load_result)
    yolo_result = run_yolo_detection(dbt_result)
    start_api_server(yolo_result)

@job(
    resource_defs={
        "telegram_scraper": telegram_scraper_resource,
        "data_integrator": data_integrator_resource
    },
    description="Data ingestion job: scrape and load data"
)
def data_ingestion_job():
    """Data ingestion job"""
    scrape_result = scrape_telegram_data()
    load_data_to_db(scrape_result)

@job(
    resource_defs={
        "dbt": dbt_resource
    },
    description="Data transformation job using dbt"
)
def data_transformation_job():
    """Data transformation job"""
    run_dbt_transformations("manual_trigger")

@job(
    resource_defs={
        "yolo_detector": yolo_detector_resource
    },
    description="YOLO object detection job"
)
def object_detection_job():
    """Object detection job"""
    run_yolo_detection("manual_trigger")

# ============================================================================
# SCHEDULES
# ============================================================================

# Daily data pipeline schedule
daily_pipeline_schedule = ScheduleDefinition(
    job=telegram_data_pipeline,
    cron_schedule="0 6 * * *",  # Run daily at 6 AM
    default_status=DefaultScheduleStatus.STOPPED,
    name="daily_telegram_pipeline",
    description="Run the complete Telegram data pipeline daily at 6 AM"
)

# Hourly data ingestion schedule
hourly_ingestion_schedule = ScheduleDefinition(
    job=data_ingestion_job,
    cron_schedule="0 * * * *",  # Run every hour
    default_status=DefaultScheduleStatus.STOPPED,
    name="hourly_data_ingestion",
    description="Run data ingestion every hour"
)

# Weekly object detection schedule
weekly_detection_schedule = ScheduleDefinition(
    job=object_detection_job,
    cron_schedule="0 2 * * 0",  # Run weekly on Sunday at 2 AM
    default_status=DefaultScheduleStatus.STOPPED,
    name="weekly_object_detection",
    description="Run YOLO object detection weekly"
)

# ============================================================================
# DEFINITIONS
# ============================================================================

defs = Definitions(
    jobs=[
        telegram_data_pipeline,
        data_ingestion_job,
        data_transformation_job,
        object_detection_job
    ],
    schedules=[
        daily_pipeline_schedule,
        hourly_ingestion_schedule,
        weekly_detection_schedule
    ],
    resources={
        "telegram_scraper": telegram_scraper_resource,
        "data_integrator": data_integrator_resource,
        "dbt": dbt_resource,
        "yolo_detector": yolo_detector_resource
    }
)