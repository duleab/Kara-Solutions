#!/usr/bin/env python3
"""
DBT Project Enhancement Setup Script

This script helps you set up and configure the advanced enhancements for your dbt project.
It provides an interactive setup process and automates common configuration tasks.

Usage:
    python scripts/setup_enhancements.py [--auto] [--phase PHASE_NUMBER]

Phases:
    1: Foundation Setup (incremental models, basic tests)
    2: Analytics Enhancement (time series, BI dashboard)
    3: Enterprise Features (security, CI/CD)
    4: Advanced Analytics (ML integration, real-time)

Requirements:
    pip install dbt-core dbt-postgres pyyaml
"""

import os
import sys
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import argparse
from datetime import datetime

class EnhancementSetup:
    """Interactive setup for dbt project enhancements"""
    
    def __init__(self, project_dir: str, auto_mode: bool = False):
        self.project_dir = Path(project_dir)
        self.auto_mode = auto_mode
        self.setup_log = []
        
    def log(self, message: str, level: str = 'INFO'):
        """Log setup progress"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}"
        self.setup_log.append(log_entry)
        print(log_entry)
    
    def prompt_user(self, question: str, default: str = 'y') -> str:
        """Prompt user for input (auto-mode returns default)"""
        if self.auto_mode:
            return default
        return input(f"{question} [{default}]: ").strip() or default
    
    def run_command(self, command: str, description: str) -> bool:
        """Run a command and log the result"""
        self.log(f"Running: {description}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.log(f"✅ {description} completed successfully")
                return True
            else:
                self.log(f"❌ {description} failed: {result.stderr}", 'ERROR')
                return False
        except Exception as e:
            self.log(f"❌ {description} failed: {str(e)}", 'ERROR')
            return False
    
    def create_file_if_not_exists(self, file_path: str, content: str, description: str) -> bool:
        """Create a file with content if it doesn't exist"""
        full_path = self.project_dir / file_path
        
        if full_path.exists():
            self.log(f"ℹ️ {description} already exists: {file_path}")
            return True
        
        try:
            # Create parent directories if they don't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content)
            
            self.log(f"✅ Created {description}: {file_path}")
            return True
        except Exception as e:
            self.log(f"❌ Failed to create {description}: {str(e)}", 'ERROR')
            return False
    
    def setup_phase_1_foundation(self) -> bool:
        """Phase 1: Foundation Setup"""
        self.log("\n🚀 Starting Phase 1: Foundation Setup")
        
        success = True
        
        # 1. Create incremental model template
        incremental_template = '''-- Incremental model template
-- Copy this template to create incremental versions of your large tables

{{
    config(
        materialized='incremental',
        unique_key='id',
        on_schema_change='fail'
    )
}}

SELECT 
    id,
    -- Add your columns here
    created_at,
    updated_at
FROM {{ source('your_source', 'your_table') }}

{% if is_incremental() %}
    -- Only process new or updated records
    WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
{% endif %}
'''
        
        if self.prompt_user("Create incremental model template?").lower().startswith('y'):
            success &= self.create_file_if_not_exists(
                'templates/incremental_template.sql',
                incremental_template,
                'incremental model template'
            )
        
        # 2. Create basic custom test
        custom_test = '''-- Custom test: Check for reasonable engagement scores
SELECT *
FROM {{ ref('fact_message_analytics') }}
WHERE engagement_score < 0 
   OR engagement_score > 100
'''
        
        if self.prompt_user("Create basic custom test?").lower().startswith('y'):
            success &= self.create_file_if_not_exists(
                'tests/assert_reasonable_engagement_scores.sql',
                custom_test,
                'custom engagement test'
            )
        
        # 3. Create basic macro
        basic_macro = '''-- Basic utility macro for data quality flags
{% macro add_data_quality_flags() %}
    CASE 
        WHEN message_text IS NULL OR LENGTH(TRIM(message_text)) = 0 THEN true
        ELSE false
    END as has_empty_content,
    
    CASE 
        WHEN created_at > CURRENT_TIMESTAMP THEN true
        WHEN created_at < '2020-01-01' THEN true
        ELSE false
    END as has_invalid_date
{% endmacro %}
'''
        
        if self.prompt_user("Create basic utility macro?").lower().startswith('y'):
            success &= self.create_file_if_not_exists(
                'macros/data_quality_utils.sql',
                basic_macro,
                'basic utility macro'
            )
        
        # 4. Run dbt parse to validate
        if self.prompt_user("Run dbt parse to validate setup?").lower().startswith('y'):
            success &= self.run_command('dbt parse', 'dbt parse validation')
        
        return success
    
    def setup_phase_2_analytics(self) -> bool:
        """Phase 2: Analytics Enhancement"""
        self.log("\n📊 Starting Phase 2: Analytics Enhancement")
        
        success = True
        
        # 1. Create time series analysis model
        time_series_model = '''-- Time series analysis for message trends
{{ config(materialized='table') }}

WITH daily_metrics AS (
    SELECT 
        DATE(message_date) as analysis_date,
        channel_id,
        COUNT(*) as daily_message_count,
        AVG(engagement_score) as daily_avg_engagement,
        SUM(CASE WHEN media_type IS NOT NULL THEN 1 ELSE 0 END) as daily_media_count
    FROM {{ ref('fact_message_analytics') }}
    WHERE message_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY DATE(message_date), channel_id
),

trend_analysis AS (
    SELECT 
        *,
        AVG(daily_message_count) OVER (
            PARTITION BY channel_id 
            ORDER BY analysis_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as weekly_avg_messages,
        
        LAG(daily_message_count, 7) OVER (
            PARTITION BY channel_id 
            ORDER BY analysis_date
        ) as messages_week_ago
    FROM daily_metrics
)

SELECT 
    *,
    CASE 
        WHEN messages_week_ago > 0 THEN 
            (daily_message_count - messages_week_ago)::FLOAT / messages_week_ago
        ELSE NULL
    END as week_over_week_growth,
    
    CASE 
        WHEN daily_message_count > weekly_avg_messages * 1.5 THEN 'High Activity'
        WHEN daily_message_count < weekly_avg_messages * 0.5 THEN 'Low Activity'
        ELSE 'Normal Activity'
    END as activity_level
    
FROM trend_analysis
ORDER BY analysis_date DESC, channel_id
'''
        
        if self.prompt_user("Create time series analysis model?").lower().startswith('y'):
            success &= self.create_file_if_not_exists(
                'models/analytics/time_series_analysis.sql',
                time_series_model,
                'time series analysis model'
            )
        
        # 2. Create channel performance dashboard
        dashboard_model = '''-- Channel performance dashboard
{{ config(materialized='table') }}

WITH channel_metrics AS (
    SELECT 
        c.channel_name,
        c.channel_type,
        f.business_category,
        COUNT(*) as total_messages,
        AVG(f.engagement_score) as avg_engagement,
        MAX(f.message_date) as last_message_date,
        COUNT(DISTINCT DATE(f.message_date)) as active_days,
        SUM(CASE WHEN f.media_type IS NOT NULL THEN 1 ELSE 0 END) as media_messages
    FROM {{ ref('fact_message_analytics') }} f
    JOIN {{ ref('stg_telegram_channels') }} c ON f.channel_id = c.id
    WHERE f.message_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY c.channel_name, c.channel_type, f.business_category
),

performance_ranking AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (ORDER BY avg_engagement DESC) as engagement_rank,
        ROW_NUMBER() OVER (ORDER BY total_messages DESC) as volume_rank,
        NTILE(4) OVER (ORDER BY avg_engagement) as engagement_quartile
    FROM channel_metrics
)

SELECT 
    *,
    CASE 
        WHEN engagement_quartile = 4 AND volume_rank <= 10 THEN 'Top Performer'
        WHEN engagement_quartile >= 3 THEN 'Good Performer'
        WHEN engagement_quartile = 2 THEN 'Average Performer'
        ELSE 'Needs Attention'
    END as performance_category,
    
    ROUND(total_messages::FLOAT / NULLIF(active_days, 0), 2) as avg_messages_per_day
    
FROM performance_ranking
ORDER BY avg_engagement DESC
'''
        
        if self.prompt_user("Create channel performance dashboard?").lower().startswith('y'):
            success &= self.create_file_if_not_exists(
                'models/analytics/channel_performance_dashboard.sql',
                dashboard_model,
                'channel performance dashboard'
            )
        
        return success
    
    def setup_phase_3_enterprise(self) -> bool:
        """Phase 3: Enterprise Features"""
        self.log("\n🏢 Starting Phase 3: Enterprise Features")
        
        success = True
        
        # 1. Create GitHub Actions workflow
        github_workflow = '''name: dbt CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install dbt-core dbt-postgres
        dbt deps
    
    - name: Configure dbt profile
      run: |
        mkdir -p ~/.dbt
        echo "$DBT_PROFILES" > ~/.dbt/profiles.yml
      env:
        DBT_PROFILES: ${{ secrets.DBT_PROFILES_YML }}
    
    - name: Test dbt project
      run: |
        dbt debug
        dbt parse
        dbt compile
        dbt test
    
    - name: Generate documentation
      run: |
        dbt docs generate
    
    - name: Deploy to staging (on develop)
      if: github.ref == 'refs/heads/develop'
      run: |
        dbt run --target staging
        dbt test --target staging
    
    - name: Deploy to production (on main)
      if: github.ref == 'refs/heads/main'
      run: |
        dbt run --target prod
        dbt test --target prod
'''
        
        if self.prompt_user("Create GitHub Actions CI/CD workflow?").lower().startswith('y'):
            success &= self.create_file_if_not_exists(
                '.github/workflows/dbt_ci.yml',
                github_workflow,
                'GitHub Actions workflow'
            )
        
        # 2. Create audit trail model
        audit_model = '''-- Model execution audit trail
{{ config(materialized='incremental', unique_key='execution_id') }}

SELECT 
    {{ dbt_utils.generate_surrogate_key(['model_name', 'execution_timestamp']) }} as execution_id,
    '{{ this.name }}' as model_name,
    CURRENT_TIMESTAMP as execution_timestamp,
    '{{ target.name }}' as target_environment,
    '{{ var("dbt_version", "unknown") }}' as dbt_version,
    COUNT(*) as record_count
FROM {{ this }}

{% if is_incremental() %}
WHERE execution_timestamp > (SELECT MAX(execution_timestamp) FROM {{ this }})
{% endif %}
'''
        
        if self.prompt_user("Create audit trail model?").lower().startswith('y'):
            success &= self.create_file_if_not_exists(
                'models/audit/model_execution_log.sql',
                audit_model,
                'audit trail model'
            )
        
        return success
    
    def setup_phase_4_advanced(self) -> bool:
        """Phase 4: Advanced Analytics"""
        self.log("\n🤖 Starting Phase 4: Advanced Analytics")
        
        success = True
        
        # 1. Create anomaly detection analysis
        anomaly_detection = '''-- Anomaly detection for engagement patterns
WITH engagement_stats AS (
    SELECT 
        channel_id,
        AVG(engagement_score) as avg_engagement,
        STDDEV(engagement_score) as stddev_engagement,
        COUNT(*) as message_count
    FROM {{ ref('fact_message_analytics') }}
    WHERE message_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY channel_id
    HAVING COUNT(*) >= 10  -- Only channels with sufficient data
),

anomalies AS (
    SELECT 
        f.channel_id,
        f.message_date,
        f.engagement_score,
        s.avg_engagement,
        s.stddev_engagement,
        ABS(f.engagement_score - s.avg_engagement) / NULLIF(s.stddev_engagement, 0) as z_score,
        CASE 
            WHEN ABS(f.engagement_score - s.avg_engagement) / NULLIF(s.stddev_engagement, 0) > 3 THEN 'Extreme Anomaly'
            WHEN ABS(f.engagement_score - s.avg_engagement) / NULLIF(s.stddev_engagement, 0) > 2 THEN 'Moderate Anomaly'
            ELSE 'Normal'
        END as anomaly_level
    FROM {{ ref('fact_message_analytics') }} f
    JOIN engagement_stats s ON f.channel_id = s.channel_id
    WHERE f.message_date >= CURRENT_DATE - INTERVAL '7 days'
)

SELECT 
    c.channel_name,
    a.*
FROM anomalies a
JOIN {{ ref('stg_telegram_channels') }} c ON a.channel_id = c.id
WHERE a.anomaly_level != 'Normal'
ORDER BY a.z_score DESC
'''
        
        if self.prompt_user("Create anomaly detection analysis?").lower().startswith('y'):
            success &= self.create_file_if_not_exists(
                'analyses/anomaly_detection.sql',
                anomaly_detection,
                'anomaly detection analysis'
            )
        
        # 2. Create ML preparation script
        ml_script = '''#!/usr/bin/env python3
"""
Machine Learning Data Preparation

This script prepares data from dbt models for machine learning analysis.
"""

import pandas as pd
import psycopg2
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

def prepare_engagement_prediction_data():
    """Prepare data for engagement score prediction"""
    
    # Connect to database (configure connection details)
    conn = psycopg2.connect(
        host="localhost",
        database="your_database",
        user="your_user",
        password="your_password"
    )
    
    # Load data from dbt model
    query = """
    SELECT 
        engagement_score,
        EXTRACT(hour FROM message_date) as hour_of_day,
        EXTRACT(dow FROM message_date) as day_of_week,
        LENGTH(message_text) as message_length,
        CASE WHEN media_type IS NOT NULL THEN 1 ELSE 0 END as has_media,
        business_category
    FROM analytics.fact_message_analytics
    WHERE engagement_score IS NOT NULL
    AND message_date >= CURRENT_DATE - INTERVAL '90 days'
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Feature engineering
    df = pd.get_dummies(df, columns=['business_category'], prefix='category')
    
    # Prepare features and target
    X = df.drop('engagement_score', axis=1)
    y = df['engagement_score']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save preprocessed data
    joblib.dump(scaler, 'models/ml/engagement_scaler.pkl')
    
    return X_train_scaled, X_test_scaled, y_train, y_test

if __name__ == '__main__':
    print("Preparing ML data...")
    X_train, X_test, y_train, y_test = prepare_engagement_prediction_data()
    print(f"Training data shape: {X_train.shape}")
    print(f"Test data shape: {X_test.shape}")
    print("Data preparation complete!")
'''
        
        if self.prompt_user("Create ML preparation script?").lower().startswith('y'):
            success &= self.create_file_if_not_exists(
                'scripts/ml_data_preparation.py',
                ml_script,
                'ML preparation script'
            )
        
        return success
    
    def run_setup(self, phase: Optional[int] = None) -> bool:
        """Run the complete setup process"""
        self.log("🎯 Starting DBT Project Enhancement Setup")
        self.log(f"Project Directory: {self.project_dir}")
        self.log(f"Auto Mode: {self.auto_mode}")
        
        overall_success = True
        
        # Determine which phases to run
        if phase:
            phases = [phase]
        else:
            if self.auto_mode:
                phases = [1, 2, 3, 4]
            else:
                response = self.prompt_user(
                    "Which phases would you like to set up? (1-4, or 'all')", 
                    'all'
                )
                if response.lower() == 'all':
                    phases = [1, 2, 3, 4]
                else:
                    try:
                        phases = [int(x.strip()) for x in response.split(',')]
                    except ValueError:
                        self.log("Invalid phase selection. Running all phases.", 'WARNING')
                        phases = [1, 2, 3, 4]
        
        # Run selected phases
        phase_functions = {
            1: self.setup_phase_1_foundation,
            2: self.setup_phase_2_analytics,
            3: self.setup_phase_3_enterprise,
            4: self.setup_phase_4_advanced
        }
        
        for phase_num in phases:
            if phase_num in phase_functions:
                success = phase_functions[phase_num]()
                overall_success &= success
                
                if not success:
                    self.log(f"❌ Phase {phase_num} completed with errors", 'WARNING')
                else:
                    self.log(f"✅ Phase {phase_num} completed successfully")
            else:
                self.log(f"❌ Invalid phase number: {phase_num}", 'ERROR')
                overall_success = False
        
        # Final validation
        if overall_success:
            self.log("\n🎉 Setup completed successfully!")
            self.log("Next steps:")
            self.log("  1. Run 'dbt parse' to validate your project")
            self.log("  2. Run 'dbt compile' to check model compilation")
            self.log("  3. Run 'dbt test' to execute your tests")
            self.log("  4. Review the IMPLEMENTATION_CHECKLIST.md for detailed next steps")
        else:
            self.log("\n⚠️ Setup completed with some issues. Please review the log above.", 'WARNING')
        
        # Save setup log
        log_file = self.project_dir / 'setup_log.txt'
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.setup_log))
        self.log(f"Setup log saved to: {log_file}")
        
        return overall_success

def main():
    parser = argparse.ArgumentParser(description='Set up dbt project enhancements')
    parser.add_argument('--project-dir', default='dbt_project', help='Path to dbt project directory')
    parser.add_argument('--auto', action='store_true', help='Run in automatic mode (no prompts)')
    parser.add_argument('--phase', type=int, choices=[1, 2, 3, 4], help='Run specific phase only')
    
    args = parser.parse_args()
    
    # Initialize setup
    setup = EnhancementSetup(
        project_dir=args.project_dir,
        auto_mode=args.auto
    )
    
    # Run setup
    success = setup.run_setup(phase=args.phase)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()