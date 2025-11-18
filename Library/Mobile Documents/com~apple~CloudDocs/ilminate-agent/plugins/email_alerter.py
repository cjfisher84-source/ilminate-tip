#!/usr/bin/env python3
"""
Email Alerter for APEX Health Monitor
Sends alerts to chris@ilminate.com via SMTP or mail command
"""

import os
import subprocess
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='[APEX Email Alerter] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailAlerter:
    """Email alerter for APEX health monitoring"""
    
    def __init__(self, recipient: str = "chris@ilminate.com"):
        self.recipient = recipient
        self.smtp_config = self._load_smtp_config()
    
    def _load_smtp_config(self) -> Optional[Dict]:
        """Load SMTP configuration from environment or config"""
        config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_user': os.getenv('SMTP_USER', ''),
            'smtp_password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('SMTP_FROM', 'apex@ilminate.com')
        }
        
        # Only return config if credentials are set
        if config['smtp_user'] and config['smtp_password']:
            return config
        return None
    
    def send_alert(self, subject: str, message: str, is_critical: bool = True) -> bool:
        """Send email alert"""
        # Try mail command first (works on macOS/Linux)
        if self._send_via_mail_command(subject, message):
            return True
        
        # Try SMTP if configured
        if self.smtp_config:
            if self._send_via_smtp(subject, message):
                return True
        
        # Log alert if email sending fails
        logger.warning(f"⚠️ Alert logged (email not sent): {subject}")
        self._log_alert(subject, message)
        return False
    
    def _send_via_mail_command(self, subject: str, message: str) -> bool:
        """Send email via system mail command"""
        try:
            # Create email body
            email_body = f"""Subject: {subject}

{message}

---
APEX Health Monitor
Ilminate Security
"""
            
            # Use mail command
            process = subprocess.Popen(
                ['mail', '-s', subject, self.recipient],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=email_body, timeout=10)
            
            if process.returncode == 0:
                logger.info(f"✅ Alert sent via mail command to {self.recipient}")
                return True
            else:
                logger.debug(f"Mail command failed: {stderr}")
                return False
        except FileNotFoundError:
            logger.debug("mail command not available")
            return False
        except Exception as e:
            logger.debug(f"Mail command error: {e}")
            return False
    
    def _send_via_smtp(self, subject: str, message: str) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = self.recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
            server.starttls()
            server.login(self.smtp_config['smtp_user'], self.smtp_config['smtp_password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Alert sent via SMTP to {self.recipient}")
            return True
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            return False
    
    def _log_alert(self, subject: str, message: str):
        """Log alert to file"""
        alert_log = "apex_alerts.log"
        try:
            with open(alert_log, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Time: {datetime.now().isoformat()}\n")
                f.write(f"Subject: {subject}\n")
                f.write(f"To: {self.recipient}\n")
                f.write(f"\n{message}\n")
                f.write(f"{'='*80}\n")
        except Exception as e:
            logger.error(f"Could not log alert: {e}")


if __name__ == '__main__':
    from datetime import datetime
    
    alerter = EmailAlerter(recipient="chris@ilminate.com")
    
    # Test alert
    subject = "APEX Health Monitor Test"
    message = f"""
This is a test alert from APEX Health Monitor.

Time: {datetime.now().isoformat()}

If you receive this, the alerting system is working correctly.

APEX Health Monitor
Ilminate Security
"""
    
    alerter.send_alert(subject, message)

