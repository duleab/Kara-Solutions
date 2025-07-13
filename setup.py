#!/usr/bin/env python3
"""
Setup script for Ethiopian Medical Business Telegram Analytics Pipeline
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'data/raw/telegram_messages',
        'data/raw/media',
        'data/processed'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created project directories")
    return True

def setup_environment():
    """Setup environment file"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your actual credentials")
        else:
            print("❌ .env.example file not found")
            return False
    else:
        print("✅ .env file already exists")
    return True

def install_dependencies():
    """Install Python dependencies"""
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    return run_command(
        'pip install -r requirements.txt',
        'Installing Python dependencies'
    )

def setup_dbt():
    """Setup dbt project"""
    os.chdir('dbt_project')
    
    # Install dbt packages
    success = run_command(
        'dbt deps',
        'Installing dbt packages'
    )
    
    if success:
        # Test dbt connection (will likely fail without proper DB setup)
        print("\nTesting dbt connection (may fail if database not configured)...")
        subprocess.run('dbt debug', shell=True)
    
    os.chdir('..')
    return success

def main():
    """Main setup function"""
    print("🚀 Setting up Ethiopian Medical Business Telegram Analytics Pipeline")
    print("=" * 70)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    # Setup steps
    steps = [
        (create_directories, "Creating project directories"),
        (setup_environment, "Setting up environment"),
        (install_dependencies, "Installing dependencies"),
        (setup_dbt, "Setting up dbt project")
    ]
    
    failed_steps = []
    
    for step_func, step_name in steps:
        if not step_func():
            failed_steps.append(step_name)
    
    print("\n" + "=" * 70)
    
    if failed_steps:
        print("❌ Setup completed with errors:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nPlease resolve the issues above and run setup again.")
    else:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your Telegram API credentials")
        print("2. Setup your database (PostgreSQL recommended)")
        print("3. Update dbt_project/profiles.yml with database connection")
        print("4. Run: python run_scraper.py --init-db")
        print("5. Run: python run_scraper.py")
        print("6. Run: cd dbt_project && dbt run")
        print("\nFor detailed instructions, see README.md")

if __name__ == "__main__":
    main()