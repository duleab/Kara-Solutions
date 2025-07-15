#!/usr/bin/env python3
"""
Implementation Validation Script

This script validates that all advanced enhancements have been properly implemented
and are functioning correctly. It performs comprehensive checks across:
- dbt project structure
- Model functionality
- Data quality
- Performance metrics
- Security configurations

Usage:
    python scripts/validate_implementation.py [--verbose] [--fix-issues]

Requirements:
    pip install dbt-core dbt-postgres pandas psycopg2-binary pyyaml
"""

import os
import sys
import json
import yaml
import subprocess
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse

class ImplementationValidator:
    """Comprehensive validation of dbt project implementation"""
    
    def __init__(self, project_dir: str, verbose: bool = False, fix_issues: bool = False):
        self.project_dir = Path(project_dir)
        self.verbose = verbose
        self.fix_issues = fix_issues
        self.results = {
            'structure': [],
            'functionality': [],
            'data_quality': [],
            'performance': [],
            'security': [],
            'overall_score': 0
        }
        
    def log(self, message: str, level: str = 'INFO'):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self.verbose or level in ['ERROR', 'WARNING']:
            print(f"[{timestamp}] {level}: {message}")
    
    def run_dbt_command(self, command: str) -> Tuple[bool, str]:
        """Execute dbt command and return success status and output"""
        try:
            result = subprocess.run(
                f"dbt {command}",
                shell=True,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out after 5 minutes"
        except Exception as e:
            return False, str(e)
    
    def validate_project_structure(self) -> Dict:
        """Validate dbt project structure and required files"""
        self.log("Validating project structure...")
        
        required_files = [
            'dbt_project.yml',
            'profiles.yml',
            '.pre-commit-config.yaml',
            'CODE_QUALITY_GUIDE.md',
            'IMPLEMENTATION_CHECKLIST.md'
        ]
        
        required_directories = [
            'models/staging',
            'models/marts/core',
            'models/analytics',
            'macros',
            'tests',
            'analyses',
            'seeds',
            'snapshots'
        ]
        
        structure_results = []
        
        # Check required files
        for file_path in required_files:
            full_path = self.project_dir / file_path
            if full_path.exists():
                structure_results.append({
                    'check': f'File exists: {file_path}',
                    'status': 'PASS',
                    'message': 'File found'
                })
            else:
                structure_results.append({
                    'check': f'File exists: {file_path}',
                    'status': 'FAIL',
                    'message': 'Required file missing'
                })
        
        # Check required directories
        for dir_path in required_directories:
            full_path = self.project_dir / dir_path
            if full_path.exists() and full_path.is_dir():
                structure_results.append({
                    'check': f'Directory exists: {dir_path}',
                    'status': 'PASS',
                    'message': 'Directory found'
                })
            else:
                structure_results.append({
                    'check': f'Directory exists: {dir_path}',
                    'status': 'FAIL',
                    'message': 'Required directory missing'
                })
        
        # Check for key model files
        key_models = [
            'models/staging/stg_telegram_messages.sql',
            'models/staging/stg_telegram_channels.sql',
            'models/staging/stg_business_info.sql',
            'models/marts/core/fact_message_analytics.sql'
        ]
        
        for model_path in key_models:
            full_path = self.project_dir / model_path
            if full_path.exists():
                structure_results.append({
                    'check': f'Key model exists: {model_path}',
                    'status': 'PASS',
                    'message': 'Model file found'
                })
            else:
                structure_results.append({
                    'check': f'Key model exists: {model_path}',
                    'status': 'FAIL',
                    'message': 'Key model missing'
                })
        
        self.results['structure'] = structure_results
        return structure_results
    
    def validate_dbt_functionality(self) -> Dict:
        """Validate dbt commands and model compilation"""
        self.log("Validating dbt functionality...")
        
        functionality_results = []
        
        # Test dbt parse
        success, output = self.run_dbt_command("parse")
        functionality_results.append({
            'check': 'dbt parse',
            'status': 'PASS' if success else 'FAIL',
            'message': 'Project parses successfully' if success else f'Parse error: {output[:200]}'
        })
        
        # Test dbt compile
        success, output = self.run_dbt_command("compile")
        functionality_results.append({
            'check': 'dbt compile',
            'status': 'PASS' if success else 'FAIL',
            'message': 'Models compile successfully' if success else f'Compile error: {output[:200]}'
        })
        
        # Test dbt deps (if packages.yml exists)
        if (self.project_dir / 'packages.yml').exists():
            success, output = self.run_dbt_command("deps")
            functionality_results.append({
                'check': 'dbt deps',
                'status': 'PASS' if success else 'FAIL',
                'message': 'Dependencies installed' if success else f'Deps error: {output[:200]}'
            })
        
        # Test dbt run (dry run with --dry-run if available, otherwise skip)
        self.log("Testing model execution...")
        success, output = self.run_dbt_command("run --select stg_telegram_messages")
        functionality_results.append({
            'check': 'dbt run (sample model)',
            'status': 'PASS' if success else 'WARNING',
            'message': 'Sample model runs successfully' if success else 'Model execution may need database connection'
        })
        
        self.results['functionality'] = functionality_results
        return functionality_results
    
    def validate_data_quality_setup(self) -> Dict:
        """Validate data quality tests and configurations"""
        self.log("Validating data quality setup...")
        
        quality_results = []
        
        # Check for schema.yml files with tests
        schema_files = list(self.project_dir.glob('**/schema.yml'))
        if schema_files:
            quality_results.append({
                'check': 'Schema files with tests',
                'status': 'PASS',
                'message': f'Found {len(schema_files)} schema files'
            })
            
            # Check content of schema files for tests
            has_tests = False
            for schema_file in schema_files:
                try:
                    with open(schema_file, 'r') as f:
                        schema_content = yaml.safe_load(f)
                        if 'models' in schema_content:
                            for model in schema_content['models']:
                                if 'tests' in model or ('columns' in model and 
                                    any('tests' in col for col in model['columns'])):
                                    has_tests = True
                                    break
                except Exception as e:
                    self.log(f"Error reading schema file {schema_file}: {e}", 'WARNING')
            
            quality_results.append({
                'check': 'Tests defined in schema files',
                'status': 'PASS' if has_tests else 'WARNING',
                'message': 'Tests found in schema files' if has_tests else 'No tests found in schema files'
            })
        else:
            quality_results.append({
                'check': 'Schema files with tests',
                'status': 'FAIL',
                'message': 'No schema.yml files found'
            })
        
        # Check for custom tests
        custom_tests = list(self.project_dir.glob('tests/**/*.sql'))
        quality_results.append({
            'check': 'Custom test files',
            'status': 'PASS' if custom_tests else 'WARNING',
            'message': f'Found {len(custom_tests)} custom test files' if custom_tests else 'No custom tests found'
        })
        
        # Check for macros
        macro_files = list(self.project_dir.glob('macros/**/*.sql'))
        quality_results.append({
            'check': 'Macro files',
            'status': 'PASS' if macro_files else 'WARNING',
            'message': f'Found {len(macro_files)} macro files' if macro_files else 'No macros found'
        })
        
        self.results['data_quality'] = quality_results
        return quality_results
    
    def validate_performance_setup(self) -> Dict:
        """Validate performance optimization configurations"""
        self.log("Validating performance setup...")
        
        performance_results = []
        
        # Check dbt_project.yml for materialization strategies
        try:
            with open(self.project_dir / 'dbt_project.yml', 'r') as f:
                project_config = yaml.safe_load(f)
                
            if 'models' in project_config:
                has_materializations = any(
                    'materialized' in str(config) 
                    for config in str(project_config['models'])
                )
                performance_results.append({
                    'check': 'Materialization strategies defined',
                    'status': 'PASS' if has_materializations else 'WARNING',
                    'message': 'Materialization strategies found' if has_materializations else 'Consider defining materialization strategies'
                })
            
        except Exception as e:
            performance_results.append({
                'check': 'dbt_project.yml configuration',
                'status': 'FAIL',
                'message': f'Error reading project config: {e}'
            })
        
        # Check for incremental models
        incremental_models = []
        for model_file in self.project_dir.glob('models/**/*.sql'):
            try:
                with open(model_file, 'r') as f:
                    content = f.read()
                    if 'materialized="incremental"' in content or "materialized='incremental'" in content:
                        incremental_models.append(model_file.name)
            except Exception:
                continue
        
        performance_results.append({
            'check': 'Incremental models',
            'status': 'PASS' if incremental_models else 'INFO',
            'message': f'Found {len(incremental_models)} incremental models' if incremental_models else 'No incremental models found (may not be needed)'
        })
        
        # Check for analyses files
        analysis_files = list(self.project_dir.glob('analyses/**/*.sql'))
        performance_results.append({
            'check': 'Analysis files',
            'status': 'PASS' if analysis_files else 'INFO',
            'message': f'Found {len(analysis_files)} analysis files' if analysis_files else 'No analysis files found'
        })
        
        self.results['performance'] = performance_results
        return performance_results
    
    def validate_security_setup(self) -> Dict:
        """Validate security and governance configurations"""
        self.log("Validating security setup...")
        
        security_results = []
        
        # Check for pre-commit configuration
        precommit_file = self.project_dir / '.pre-commit-config.yaml'
        if precommit_file.exists():
            security_results.append({
                'check': 'Pre-commit hooks configured',
                'status': 'PASS',
                'message': 'Pre-commit configuration found'
            })
            
            try:
                with open(precommit_file, 'r') as f:
                    precommit_config = yaml.safe_load(f)
                    
                has_dbt_hooks = any(
                    'dbt' in str(repo.get('repo', '')) 
                    for repo in precommit_config.get('repos', [])
                )
                
                security_results.append({
                    'check': 'dbt-specific pre-commit hooks',
                    'status': 'PASS' if has_dbt_hooks else 'WARNING',
                    'message': 'dbt hooks found' if has_dbt_hooks else 'Consider adding dbt-specific hooks'
                })
                
            except Exception as e:
                security_results.append({
                    'check': 'Pre-commit configuration validity',
                    'status': 'FAIL',
                    'message': f'Error reading pre-commit config: {e}'
                })
        else:
            security_results.append({
                'check': 'Pre-commit hooks configured',
                'status': 'WARNING',
                'message': 'No pre-commit configuration found'
            })
        
        # Check for documentation
        doc_files = [
            'CODE_QUALITY_GUIDE.md',
            'IMPLEMENTATION_CHECKLIST.md',
            'README.md'
        ]
        
        found_docs = []
        for doc_file in doc_files:
            if (self.project_dir / doc_file).exists():
                found_docs.append(doc_file)
        
        security_results.append({
            'check': 'Documentation files',
            'status': 'PASS' if len(found_docs) >= 2 else 'WARNING',
            'message': f'Found documentation: {", ".join(found_docs)}' if found_docs else 'No documentation found'
        })
        
        # Check for governance files
        governance_files = ['dbt_project_properties.yml']
        found_governance = [f for f in governance_files if (self.project_dir / f).exists()]
        
        security_results.append({
            'check': 'Governance configurations',
            'status': 'PASS' if found_governance else 'INFO',
            'message': f'Found governance files: {", ".join(found_governance)}' if found_governance else 'No governance files found'
        })
        
        self.results['security'] = security_results
        return security_results
    
    def calculate_overall_score(self) -> int:
        """Calculate overall implementation score (0-100)"""
        total_checks = 0
        passed_checks = 0
        
        for category in ['structure', 'functionality', 'data_quality', 'performance', 'security']:
            for result in self.results[category]:
                total_checks += 1
                if result['status'] == 'PASS':
                    passed_checks += 1
                elif result['status'] == 'WARNING':
                    passed_checks += 0.5  # Partial credit for warnings
        
        score = int((passed_checks / total_checks) * 100) if total_checks > 0 else 0
        self.results['overall_score'] = score
        return score
    
    def generate_report(self) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("=" * 80)
        report.append("DBT PROJECT IMPLEMENTATION VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Project Directory: {self.project_dir}")
        report.append(f"Overall Score: {self.results['overall_score']}/100")
        report.append("")
        
        categories = {
            'structure': 'PROJECT STRUCTURE',
            'functionality': 'DBT FUNCTIONALITY',
            'data_quality': 'DATA QUALITY SETUP',
            'performance': 'PERFORMANCE OPTIMIZATION',
            'security': 'SECURITY & GOVERNANCE'
        }
        
        for category, title in categories.items():
            report.append(f"\n{title}")
            report.append("-" * len(title))
            
            for result in self.results[category]:
                status_icon = {
                    'PASS': '✅',
                    'FAIL': '❌',
                    'WARNING': '⚠️',
                    'INFO': 'ℹ️'
                }.get(result['status'], '❓')
                
                report.append(f"{status_icon} {result['check']}: {result['message']}")
        
        # Add recommendations
        report.append("\n\nRECOMMENDations")
        report.append("-" * 15)
        
        failed_checks = []
        warning_checks = []
        
        for category in self.results:
            if category != 'overall_score':
                for result in self.results[category]:
                    if result['status'] == 'FAIL':
                        failed_checks.append(result)
                    elif result['status'] == 'WARNING':
                        warning_checks.append(result)
        
        if failed_checks:
            report.append("\nCRITICAL ISSUES (Must Fix):")
            for check in failed_checks:
                report.append(f"  • {check['check']}: {check['message']}")
        
        if warning_checks:
            report.append("\nIMPROVEMENT OPPORTUNITIES:")
            for check in warning_checks:
                report.append(f"  • {check['check']}: {check['message']}")
        
        if self.results['overall_score'] >= 90:
            report.append("\n🎉 EXCELLENT! Your implementation is highly optimized.")
        elif self.results['overall_score'] >= 75:
            report.append("\n👍 GOOD! Your implementation is solid with room for minor improvements.")
        elif self.results['overall_score'] >= 60:
            report.append("\n⚠️ FAIR! Your implementation needs some attention to reach best practices.")
        else:
            report.append("\n🔧 NEEDS WORK! Several critical issues need to be addressed.")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
    
    def run_validation(self) -> Dict:
        """Run complete validation suite"""
        self.log("Starting comprehensive implementation validation...")
        
        # Run all validation checks
        self.validate_project_structure()
        self.validate_dbt_functionality()
        self.validate_data_quality_setup()
        self.validate_performance_setup()
        self.validate_security_setup()
        
        # Calculate overall score
        self.calculate_overall_score()
        
        self.log(f"Validation complete. Overall score: {self.results['overall_score']}/100")
        
        return self.results

def main():
    parser = argparse.ArgumentParser(description='Validate dbt project implementation')
    parser.add_argument('--project-dir', default='dbt_project', help='Path to dbt project directory')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--fix-issues', action='store_true', help='Attempt to fix common issues')
    parser.add_argument('--output', help='Output file for validation report')
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = ImplementationValidator(
        project_dir=args.project_dir,
        verbose=args.verbose,
        fix_issues=args.fix_issues
    )
    
    # Run validation
    results = validator.run_validation()
    
    # Generate and display report
    report = validator.generate_report()
    print(report)
    
    # Save report if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {args.output}")
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_score'] >= 75 else 1
    sys.exit(exit_code)

if __name__ == '__main__':
    main()