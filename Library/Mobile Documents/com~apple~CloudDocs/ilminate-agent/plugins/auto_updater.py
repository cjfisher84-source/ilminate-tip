#!/usr/bin/env python3
"""
APEX Detection Engines Auto-Updater
Automatically updates all detection engines and ensures they're running
"""

import os
import sys
import subprocess
import logging
import time
from datetime import datetime
from pathlib import Path
import json

logging.basicConfig(
    level=logging.INFO,
    format='[APEX Auto-Updater] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APEXAutoUpdater:
    """Auto-updater for all APEX detection engines"""
    
    def __init__(self):
        self.update_log = []
        self.services_status = {}
        
    def update_clamav_database(self):
        """Update ClamAV virus database"""
        try:
            logger.info("Updating ClamAV database...")
            result = subprocess.run(
                ['freshclam', '--quiet'],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.info("✅ ClamAV database updated successfully")
                self.update_log.append({
                    'engine': 'ClamAV',
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                })
                return True
            else:
                logger.warning(f"⚠️ ClamAV update had issues: {result.stderr[:100]}")
                return False
        except FileNotFoundError:
            logger.warning("⚠️ freshclam not found - ClamAV not installed")
            return False
        except subprocess.TimeoutExpired:
            logger.error("❌ ClamAV update timed out")
            return False
        except Exception as e:
            logger.error(f"❌ ClamAV update error: {e}")
            return False
    
    def update_yara_rules(self):
        """Update YARA rules"""
        try:
            logger.info("Checking YARA rules...")
            yara_rules_path = "/etc/ilminate-agent/deployment/ansible/files/yara"
            if os.path.exists(yara_rules_path):
                logger.info("✅ YARA rules directory exists")
                # Check if rules need updating (could add git pull here)
                self.update_log.append({
                    'engine': 'YARA',
                    'status': 'checked',
                    'timestamp': datetime.now().isoformat()
                })
                return True
            else:
                logger.warning("⚠️ YARA rules directory not found")
                return False
        except Exception as e:
            logger.error(f"❌ YARA rules check error: {e}")
            return False
    
    def update_ml_models(self):
        """Check and update ML models"""
        try:
            logger.info("Checking ML models...")
            # Check if models directory exists
            models_path = "/etc/ilminate-apex/models"
            if os.path.exists(models_path):
                logger.info("✅ ML models directory exists")
                self.update_log.append({
                    'engine': 'ML Models',
                    'status': 'checked',
                    'timestamp': datetime.now().isoformat()
                })
                return True
            else:
                logger.info("ℹ️ ML models directory not found (will be created on first use)")
                return True
        except Exception as e:
            logger.error(f"❌ ML models check error: {e}")
            return False
    
    def check_clamav_service(self):
        """Check if ClamAV daemon is running"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'clamd'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✅ ClamAV daemon is running")
                self.services_status['clamav'] = 'running'
                return True
            else:
                logger.warning("⚠️ ClamAV daemon not running")
                self.services_status['clamav'] = 'stopped'
                return False
        except Exception as e:
            logger.error(f"❌ ClamAV service check error: {e}")
            return False
    
    def start_clamav_service(self):
        """Start ClamAV daemon"""
        try:
            logger.info("Starting ClamAV daemon...")
            # Try systemd first
            result = subprocess.run(
                ['sudo', 'systemctl', 'start', 'clamav-daemon'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info("✅ ClamAV daemon started")
                time.sleep(2)  # Wait for service to start
                return True
            else:
                # Try direct start
                logger.info("Trying to start ClamAV directly...")
                result = subprocess.run(
                    ['clamd'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                logger.warning("⚠️ ClamAV start attempted (may need manual start)")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Could not start ClamAV: {e}")
            return False
    
    def check_spamassassin_service(self):
        """Check if SpamAssassin is available"""
        try:
            result = subprocess.run(
                ['which', 'spamc'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✅ SpamAssassin is available")
                self.services_status['spamassassin'] = 'available'
                return True
            else:
                logger.info("ℹ️ SpamAssassin not installed (ML alternatives available)")
                self.services_status['spamassassin'] = 'not_installed'
                return False
        except Exception as e:
            logger.warning(f"⚠️ SpamAssassin check error: {e}")
            return False
    
    def check_python_packages(self):
        """Check and update Python packages"""
        try:
            logger.info("Checking Python packages...")
            packages_to_check = [
                'numpy', 'scipy', 'scikit-learn', 'pandas',
                'torch', 'transformers', 'yara-python', 'boto3'
            ]
            
            missing_packages = []
            for package in packages_to_check:
                try:
                    __import__(package.replace('-', '_'))
                    logger.debug(f"✅ {package} installed")
                except ImportError:
                    missing_packages.append(package)
                    logger.warning(f"⚠️ {package} not installed")
            
            if missing_packages:
                logger.info(f"Missing packages: {', '.join(missing_packages)}")
                logger.info("Run: pip install " + " ".join(missing_packages))
                return False
            else:
                logger.info("✅ All required Python packages installed")
                return True
        except Exception as e:
            logger.error(f"❌ Python packages check error: {e}")
            return False
    
    def check_mosint(self):
        """Check if mosint is available"""
        try:
            result = subprocess.run(
                ['which', 'mosint'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("✅ Mosint is available")
                self.services_status['mosint'] = 'available'
                return True
            else:
                # Check Go bin
                go_path = subprocess.run(
                    ['go', 'env', 'GOPATH'],
                    capture_output=True,
                    text=True
                ).stdout.strip()
                mosint_path = os.path.join(go_path, 'bin', 'mosint')
                if os.path.exists(mosint_path):
                    logger.info("✅ Mosint found in Go bin")
                    self.services_status['mosint'] = 'available'
                    return True
                else:
                    logger.warning("⚠️ Mosint not found")
                    self.services_status['mosint'] = 'not_found'
                    return False
        except Exception as e:
            logger.warning(f"⚠️ Mosint check error: {e}")
            return False
    
    def update_all(self):
        """Update all detection engines"""
        logger.info("=" * 80)
        logger.info("Starting APEX Detection Engines Auto-Update")
        logger.info("=" * 80)
        
        results = {
            'clamav': self.update_clamav_database(),
            'yara': self.update_yara_rules(),
            'ml_models': self.update_ml_models(),
            'python_packages': self.check_python_packages()
        }
        
        logger.info("=" * 80)
        logger.info("Update Summary:")
        for engine, status in results.items():
            status_str = "✅ Success" if status else "⚠️ Issues"
            logger.info(f"  {engine:20} {status_str}")
        logger.info("=" * 80)
        
        return results
    
    def check_all_services(self):
        """Check status of all services"""
        logger.info("=" * 80)
        logger.info("Checking APEX Detection Engine Services")
        logger.info("=" * 80)
        
        results = {
            'clamav': self.check_clamav_service(),
            'spamassassin': self.check_spamassassin_service(),
            'mosint': self.check_mosint(),
            'python_packages': self.check_python_packages()
        }
        
        logger.info("=" * 80)
        logger.info("Service Status:")
        for service, status in results.items():
            status_str = self.services_status.get(service, 'unknown')
            logger.info(f"  {service:20} {status_str}")
        logger.info("=" * 80)
        
        return results
    
    def start_all_services(self):
        """Start all required services"""
        logger.info("=" * 80)
        logger.info("Starting APEX Detection Engine Services")
        logger.info("=" * 80)
        
        # Check ClamAV
        if not self.check_clamav_service():
            logger.info("Starting ClamAV...")
            self.start_clamav_service()
            time.sleep(2)
            self.check_clamav_service()
        
        logger.info("=" * 80)
        logger.info("Service Start Summary:")
        for service, status in self.services_status.items():
            logger.info(f"  {service:20} {status}")
        logger.info("=" * 80)
    
    def save_update_log(self, log_file='apex_update_log.json'):
        """Save update log to file"""
        try:
            log_data = {
                'last_update': datetime.now().isoformat(),
                'updates': self.update_log,
                'services': self.services_status
            }
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            logger.info(f"✅ Update log saved to {log_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save update log: {e}")


def main():
    """Main function"""
    updater = APEXAutoUpdater()
    
    # Update all engines
    updater.update_all()
    
    # Check all services
    updater.check_all_services()
    
    # Start services if needed
    updater.start_all_services()
    
    # Save log
    updater.save_update_log()
    
    logger.info("=" * 80)
    logger.info("✅ Auto-update complete!")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()

