#!/usr/bin/env python3
"""
APEX Service Watchdog
Ensures all detection engines are always running and restarts them if needed
"""

import os
import sys
import subprocess
import logging
import time
import signal
from datetime import datetime
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format='[APEX Watchdog] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceWatchdog:
    """Watchdog to ensure services stay running"""
    
    def __init__(self):
        self.running = True
        self.check_interval = 60  # Check every 60 seconds
        self.max_restart_attempts = 3
        self.restart_delays = {}  # Track restart attempts
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def check_service(self, service_name: str, check_func, start_func=None) -> bool:
        """Check if a service is running"""
        try:
            is_running = check_func()
            if not is_running:
                logger.warning(f"⚠️ {service_name} is not running")
                if start_func:
                    self.restart_service(service_name, start_func)
            return is_running
        except Exception as e:
            logger.error(f"Error checking {service_name}: {e}")
            return False
    
    def restart_service(self, service_name: str, start_func):
        """Restart a service"""
        # Check restart attempts
        attempts = self.restart_delays.get(service_name, {}).get('attempts', 0)
        if attempts >= self.max_restart_attempts:
            logger.error(f"❌ {service_name} failed to start after {self.max_restart_attempts} attempts")
            return False
        
        logger.info(f"🔄 Attempting to restart {service_name}...")
        
        try:
            success = start_func()
            if success:
                logger.info(f"✅ {service_name} restarted successfully")
                self.restart_delays[service_name] = {'attempts': 0, 'last_attempt': None}
                return True
            else:
                attempts += 1
                self.restart_delays[service_name] = {
                    'attempts': attempts,
                    'last_attempt': datetime.now().isoformat()
                }
                logger.warning(f"⚠️ {service_name} restart attempt {attempts} failed")
                return False
        except Exception as e:
            logger.error(f"❌ Error restarting {service_name}: {e}")
            attempts += 1
            self.restart_delays[service_name] = {
                'attempts': attempts,
                'last_attempt': datetime.now().isoformat()
            }
            return False
    
    def start_clamav(self) -> bool:
        """Start ClamAV daemon"""
        try:
            # Try systemd first
            result = subprocess.run(
                ['sudo', 'systemctl', 'start', 'clamav-daemon'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                time.sleep(2)  # Wait for service to start
                return True
            
            # Try direct start
            logger.warning("ClamAV may need manual start: sudo systemctl start clamav-daemon")
            return False
        except Exception as e:
            logger.error(f"Error starting ClamAV: {e}")
            return False
    
    def check_clamav(self) -> bool:
        """Check if ClamAV is running"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'clamd'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def monitor_services(self):
        """Monitor all services"""
        logger.info("=" * 80)
        logger.info("APEX Service Watchdog Starting")
        logger.info("=" * 80)
        
        services = [
            ('ClamAV', self.check_clamav, self.start_clamav),
        ]
        
        while self.running:
            try:
                logger.info(f"Checking services at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                all_healthy = True
                for service_name, check_func, start_func in services:
                    is_running = self.check_service(service_name, check_func, start_func)
                    if not is_running:
                        all_healthy = False
                
                if all_healthy:
                    logger.info("✅ All services healthy")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Watchdog stopped by user")
                break
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
                time.sleep(self.check_interval)
        
        logger.info("=" * 80)
        logger.info("APEX Service Watchdog Stopped")
        logger.info("=" * 80)


def main():
    """Main function"""
    watchdog = ServiceWatchdog()
    watchdog.monitor_services()


if __name__ == '__main__':
    main()

