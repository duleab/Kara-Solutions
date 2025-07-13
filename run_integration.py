#!/usr/bin/env python3
"""
Telegram Data Integration Pipeline

This script orchestrates the complete integration of scraped Telegram data:
1. Database setup and initialization
2. Data migration from scraped files
3. dbt transformation pipeline execution
4. Data quality validation
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TelegramDataIntegrator:
    """Orchestrates the complete data integration pipeline."""
    
    def __init__(self, scraped_data_path: str = "./Technical Content/telegram_data"):
        self.scraped_data_path = Path(scraped_data_path)
        self.project_root = Path.cwd()
        self.dbt_project_path = self.project_root / "dbt_project"
        
    def setup_environment(self) -> bool:
        """Setup the environment and validate prerequisites."""
        logger.info("🔧 Setting up environment...")
        
        # Create necessary directories
        directories = ['logs', 'data/raw/telegram_messages', 'data/raw/media', 'data/processed']
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {directory}")
        
        # Check if .env file exists
        env_file = self.project_root / '.env'
        if not env_file.exists():
            logger.error("❌ .env file not found. Please create it first.")
            return False
        
        # Check if scraped data exists
        if not self.scraped_data_path.exists():
            logger.error(f"❌ Scraped data path not found: {self.scraped_data_path}")
            return False
        
        logger.info("✅ Environment setup completed")
        return True
    
    def install_dependencies(self) -> bool:
        """Install Python and dbt dependencies."""
        logger.info("📦 Installing dependencies...")
        
        try:
            # Install Python dependencies
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                         check=True, capture_output=True)
            logger.info("✅ Python dependencies installed")
            
            # Install dbt packages
            if self.dbt_project_path.exists():
                subprocess.run(['dbt', 'deps'], cwd=self.dbt_project_path, check=True, capture_output=True)
                logger.info("✅ dbt packages installed")
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
    
    def setup_database(self) -> bool:
        """Initialize the database and create tables."""
        logger.info("🗄️ Setting up database...")
        
        try:
            from src.database.config import db_config, get_db, init_database
            
            # Test database connection
            engine = get_database_engine()
            with engine.connect() as conn:
                logger.info("✅ Database connection successful")
            
            # Create tables
            init_database()
            logger.info("✅ Database tables created")
            
            return True
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            return False
    
    def migrate_scraped_data(self) -> bool:
        """Migrate scraped Telegram data to the database."""
        logger.info("📊 Migrating scraped data...")
        
        try:
            from migrate_scraped_data import ScrapedDataMigrator
            
            migrator = ScrapedDataMigrator(str(self.scraped_data_path))
            migrator.run_migration()
            
            logger.info("✅ Data migration completed")
            return True
        except Exception as e:
            logger.error(f"❌ Data migration failed: {e}")
            return False
    
    def run_dbt_pipeline(self) -> bool:
        """Execute the dbt transformation pipeline."""
        logger.info("🔄 Running dbt transformations...")
        
        if not self.dbt_project_path.exists():
            logger.error("❌ dbt project not found")
            return False
        
        try:
            # Run dbt debug to check configuration
            result = subprocess.run(['dbt', 'debug'], cwd=self.dbt_project_path, 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"⚠️ dbt debug warnings: {result.stdout}")
            
            # Run dbt transformations
            subprocess.run(['dbt', 'run'], cwd=self.dbt_project_path, check=True)
            logger.info("✅ dbt transformations completed")
            
            # Run dbt tests
            test_result = subprocess.run(['dbt', 'test'], cwd=self.dbt_project_path, 
                                       capture_output=True, text=True)
            if test_result.returncode == 0:
                logger.info("✅ All dbt tests passed")
            else:
                logger.warning(f"⚠️ Some dbt tests failed: {test_result.stdout}")
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ dbt pipeline failed: {e}")
            return False
    
    def generate_summary_report(self) -> None:
        """Generate a summary report of the integration."""
        logger.info("📋 Generating summary report...")
        
        try:
            from src.database.config import get_database_engine
            from sqlalchemy import text
            
            engine = get_database_engine()
            
            with engine.connect() as conn:
                # Get basic statistics
                stats = {}
                
                # Channel count
                result = conn.execute(text("SELECT COUNT(*) FROM telegram_channels"))
                stats['channels'] = result.scalar()
                
                # Message count
                result = conn.execute(text("SELECT COUNT(*) FROM telegram_messages"))
                stats['messages'] = result.scalar()
                
                # Media files count
                result = conn.execute(text("SELECT COUNT(*) FROM media_files"))
                stats['media_files'] = result.scalar()
                
                # Business info count
                result = conn.execute(text("SELECT COUNT(*) FROM business_info"))
                stats['business_records'] = result.scalar()
                
                # Generate report
                report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    INTEGRATION SUMMARY REPORT                ║
╠══════════════════════════════════════════════════════════════╣
║ Integration completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    ║
║                                                              ║
║ 📊 DATA STATISTICS:                                          ║
║   • Channels processed: {stats['channels']:>6}                              ║
║   • Messages imported: {stats['messages']:>7}                              ║
║   • Media files: {stats['media_files']:>12}                              ║
║   • Business records: {stats['business_records']:>8}                              ║
║                                                              ║
║ 🎯 NEXT STEPS:                                               ║
║   1. Query the marts models for business insights            ║
║   2. Use fact_message_analytics for detailed analysis       ║
║   3. Check business_summary for aggregated metrics          ║
║   4. Review daily_activity_trends for time-series data      ║
║                                                              ║
║ 📁 KEY MODELS CREATED:                                       ║
║   • stg_telegram_channels                                    ║
║   • stg_telegram_messages                                    ║
║   • stg_business_info                                        ║
║   • fact_message_analytics                                   ║
║   • business_summary                                         ║
║   • daily_activity_trends                                    ║
╚══════════════════════════════════════════════════════════════╝
                """
                
                print(report)
                logger.info("✅ Summary report generated")
                
                # Save report to file
                with open('logs/integration_summary.txt', 'w') as f:
                    f.write(report)
                
        except Exception as e:
            logger.error(f"❌ Failed to generate summary: {e}")
    
    def run_complete_integration(self) -> bool:
        """Run the complete integration pipeline."""
        logger.info("🚀 Starting complete Telegram data integration pipeline...")
        
        steps = [
            ("Environment Setup", self.setup_environment),
            ("Install Dependencies", self.install_dependencies),
            ("Database Setup", self.setup_database),
            ("Data Migration", self.migrate_scraped_data),
            ("dbt Pipeline", self.run_dbt_pipeline)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{'='*60}")
            logger.info(f"STEP: {step_name}")
            logger.info(f"{'='*60}")
            
            if not step_func():
                logger.error(f"❌ Pipeline failed at step: {step_name}")
                return False
        
        # Generate summary report
        self.generate_summary_report()
        
        logger.info("\n🎉 Integration pipeline completed successfully!")
        return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Telegram data integration pipeline')
    parser.add_argument(
        '--data-path',
        default='./Technical Content/telegram_data',
        help='Path to scraped telegram data folder'
    )
    parser.add_argument(
        '--skip-deps',
        action='store_true',
        help='Skip dependency installation'
    )
    
    args = parser.parse_args()
    
    integrator = TelegramDataIntegrator(args.data_path)
    
    if args.skip_deps:
        integrator.install_dependencies = lambda: True
    
    success = integrator.run_complete_integration()
    sys.exit(0 if success else 1)