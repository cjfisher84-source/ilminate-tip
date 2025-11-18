#!/usr/bin/env python3
"""
APEX Detection Engines Health Monitor
Monitors all detection engines and sends alerts on service disruption
"""

import os
import sys
import subprocess
import logging
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(
    level=logging.INFO,
    format='[APEX Health Monitor] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthMonitor:
    """Health monitor for APEX detection engines"""
    
    def __init__(self, alert_email: str = "chris@ilminate.com"):
        self.alert_email = alert_email
        self.health_status_file = "apex_health_status.json"
        self.alert_history_file = "apex_alert_history.json"
        self.uptime_file = "apex_uptime.json"
        self.last_status = self._load_status()
        self.alert_history = self._load_alert_history()
        
    def _load_status(self) -> Dict:
        """Load last health status"""
        try:
            if os.path.exists(self.health_status_file):
                with open(self.health_status_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load status: {e}")
        return {}
    
    def _save_status(self, status: Dict):
        """Save health status"""
        try:
            with open(self.health_status_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save status: {e}")
    
    def _load_alert_history(self) -> List:
        """Load alert history"""
        try:
            if os.path.exists(self.alert_history_file):
                with open(self.alert_history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load alert history: {e}")
        return []
    
    def _save_alert_history(self):
        """Save alert history"""
        try:
            with open(self.alert_history_file, 'w') as f:
                json.dump(self.alert_history, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save alert history: {e}")
    
    def check_engine_health(self, engine_name: str, check_func) -> Dict:
        """Check health of a specific engine"""
        try:
            result = check_func()
            return {
                'name': engine_name,
                'status': 'healthy' if result else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'checked': True
            }
        except Exception as e:
            logger.error(f"Health check error for {engine_name}: {e}")
            return {
                'name': engine_name,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'checked': True
            }
    
    def check_clamav(self) -> bool:
        """Check ClamAV health"""
        try:
            # Check if clamdscan is available
            result = subprocess.run(
                ['which', 'clamdscan'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False
            
            # Check if daemon is running
            daemon = subprocess.run(
                ['pgrep', '-f', 'clamd'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return daemon.returncode == 0
        except Exception:
            return False
    
    def check_yara(self) -> bool:
        """Check YARA health"""
        try:
            import yara
            return True
        except ImportError:
            return False
    
    def check_ml_engines(self) -> bool:
        """Check ML/AI engines health"""
        try:
            import numpy
            import sklearn
            return True
        except ImportError:
            return False
    
    def check_mosint(self) -> bool:
        """Check Mosint health"""
        try:
            result = subprocess.run(
                ['which', 'mosint'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
            
            # Check Go bin
            go_path = subprocess.run(
                ['go', 'env', 'GOPATH'],
                capture_output=True,
                text=True,
                timeout=5
            ).stdout.strip()
            mosint_path = os.path.join(go_path, 'bin', 'mosint')
            return os.path.exists(mosint_path)
        except Exception:
            return False
    
    def check_mosint_detector(self) -> bool:
        """Check Mosint detector health"""
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from plugins.mosint_detector import MosintDetector
            detector = MosintDetector({'enabled': True})
            return detector.enabled
        except Exception:
            return False
    
    def check_apex_engine(self) -> bool:
        """Check APEX detection engine health"""
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from plugins.apex_detection_engine import APEXDetectionEngine
            config = {'mosint': {'enabled': True}, 'detection_layers': {}}
            engine = APEXDetectionEngine(config)
            return engine is not None
        except Exception:
            return False
    
    def check_all_engines(self) -> Dict:
        """Check health of all detection engines"""
        logger.info("=" * 80)
        logger.info("Checking APEX Detection Engines Health")
        logger.info("=" * 80)
        
        engines = {
            'ClamAV': self.check_clamav,
            'YARA': self.check_yara,
            'ML/AI Engines': self.check_ml_engines,
            'Mosint OSINT': self.check_mosint,
            'Mosint Detector': self.check_mosint_detector,
            'APEX Engine': self.check_apex_engine,
        }
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'engines': {},
            'overall_status': 'healthy',
            'unhealthy_count': 0,
            'total_count': len(engines)
        }
        
        for engine_name, check_func in engines.items():
            engine_status = self.check_engine_health(engine_name, check_func)
            health_status['engines'][engine_name] = engine_status
            
            if engine_status['status'] != 'healthy':
                health_status['unhealthy_count'] += 1
                health_status['overall_status'] = 'unhealthy'
                logger.warning(f"⚠️ {engine_name}: {engine_status['status']}")
            else:
                logger.info(f"✅ {engine_name}: healthy")
        
        # Save status
        self._save_status(health_status)
        
        logger.info("=" * 80)
        logger.info(f"Overall Status: {health_status['overall_status'].upper()}")
        logger.info(f"Unhealthy Engines: {health_status['unhealthy_count']}/{health_status['total_count']}")
        logger.info("=" * 80)
        
        return health_status
    
    def send_alert(self, subject: str, message: str, is_critical: bool = True):
        """Send email alert"""
        # Try email alerter module first
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from plugins.email_alerter import EmailAlerter
            alerter = EmailAlerter(recipient=self.alert_email)
            if alerter.send_alert(subject, message, is_critical):
                logger.info(f"✅ Alert sent to {self.alert_email}")
                self.alert_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'subject': subject,
                    'sent': True,
                    'method': 'email_alerter'
                })
                self._save_alert_history()
                return True
        except Exception as e:
            logger.debug(f"Email alerter failed: {e}")
        
        # Fallback: Try system mail command
        try:
            email_body = f"{message}\n\n---\nAPEX Health Monitor\nIlminate Security"
            process = subprocess.Popen(
                ['mail', '-s', subject, self.alert_email],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=email_body, timeout=10)
            
            if process.returncode == 0:
                logger.info(f"✅ Alert sent via mail command to {self.alert_email}")
                self.alert_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'subject': subject,
                    'sent': True,
                    'method': 'mail_command'
                })
                self._save_alert_history()
                return True
        except Exception as e:
            logger.debug(f"Mail command failed: {e}")
        
        # Log alert if email sending fails
        logger.warning(f"⚠️ Alert logged (email not sent): {subject}")
        self.alert_history.append({
            'timestamp': datetime.now().isoformat(),
            'subject': subject,
            'message': message[:200],  # Truncate for storage
            'sent': False,
            'method': 'logged_only'
        })
        self._save_alert_history()
        return False
    
    def check_and_alert(self):
        """Check health and send alerts if needed"""
        current_status = self.check_all_engines()
        
        # Compare with last status
        if self.last_status:
            # Check for new failures
            for engine_name, engine_status in current_status['engines'].items():
                last_engine_status = self.last_status.get('engines', {}).get(engine_name, {})
                
                # If engine became unhealthy
                if (engine_status['status'] != 'healthy' and 
                    last_engine_status.get('status') == 'healthy'):
                    
                    subject = f"🚨 APEX Alert: {engine_name} Service Disruption"
                    message = f"""
APEX Detection Engine Service Disruption Alert

Engine: {engine_name}
Status: {engine_status['status']}
Time: {engine_status['timestamp']}

This engine was previously healthy but is now reporting issues.

Please investigate immediately.

APEX Health Monitor
Ilminate Security
"""
                    self.send_alert(subject, message, is_critical=True)
                    logger.warning(f"🚨 Alert sent: {engine_name} service disruption")
        
        # Update last status
        self.last_status = current_status
        
        # If overall status is unhealthy, send summary alert
        if current_status['overall_status'] == 'unhealthy':
            unhealthy_engines = [
                name for name, status in current_status['engines'].items()
                if status['status'] != 'healthy'
            ]
            
            subject = f"🚨 APEX Alert: {len(unhealthy_engines)} Engine(s) Unhealthy"
            message = f"""
APEX Detection Engines Health Alert

Overall Status: UNHEALTHY
Unhealthy Engines: {len(unhealthy_engines)}/{current_status['total_count']}

Unhealthy Engines:
{chr(10).join(f'  - {name}: {current_status["engines"][name]["status"]}' for name in unhealthy_engines)}

Time: {current_status['timestamp']}

Please investigate immediately.

APEX Health Monitor
Ilminate Security
"""
            self.send_alert(subject, message, is_critical=True)
    
    def get_uptime_stats(self) -> Dict:
        """Get uptime statistics"""
        try:
            if os.path.exists(self.uptime_file):
                with open(self.uptime_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        
        # Initialize uptime tracking
        return {
            'start_time': datetime.now().isoformat(),
            'last_check': datetime.now().isoformat(),
            'total_checks': 0,
            'healthy_checks': 0,
            'unhealthy_checks': 0,
            'uptime_percentage': 100.0
        }
    
    def update_uptime(self, is_healthy: bool):
        """Update uptime statistics"""
        stats = self.get_uptime_stats()
        stats['last_check'] = datetime.now().isoformat()
        stats['total_checks'] = stats.get('total_checks', 0) + 1
        
        if is_healthy:
            stats['healthy_checks'] = stats.get('healthy_checks', 0) + 1
        else:
            stats['unhealthy_checks'] = stats.get('unhealthy_checks', 0) + 1
        
        if stats['total_checks'] > 0:
            stats['uptime_percentage'] = (stats['healthy_checks'] / stats['total_checks']) * 100.0
        
        try:
            with open(self.uptime_file, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save uptime stats: {e}")


def main():
    """Main function"""
    monitor = HealthMonitor(alert_email="chris@ilminate.com")
    
    # Check health
    status = monitor.check_all_engines()
    
    # Check and send alerts
    monitor.check_and_alert()
    
    # Update uptime
    monitor.update_uptime(status['overall_status'] == 'healthy')
    
    # Print uptime stats
    uptime = monitor.get_uptime_stats()
    logger.info("=" * 80)
    logger.info("Uptime Statistics:")
    logger.info(f"  Total Checks: {uptime.get('total_checks', 0)}")
    logger.info(f"  Healthy Checks: {uptime.get('healthy_checks', 0)}")
    logger.info(f"  Unhealthy Checks: {uptime.get('unhealthy_checks', 0)}")
    logger.info(f"  Uptime: {uptime.get('uptime_percentage', 100.0):.2f}%")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()

