"""
ClamAV Integration
Scans email attachments for malware using ClamAV
"""

import os
import subprocess
import tempfile
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ClamAVDetector:
    """ClamAV malware detector"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.clamscan_path = self._find_clamscan()
        
        if self.clamscan_path:
            logger.info(f"✓ ClamAV found at: {self.clamscan_path}")
        else:
            logger.warning("❌ ClamAV not found - malware detection disabled")
    
    def _find_clamscan(self) -> Optional[str]:
        """Find ClamAV clamscan executable"""
        possible_paths = [
            '/usr/bin/clamscan',
            '/usr/local/bin/clamscan',
            '/opt/homebrew/bin/clamscan',
            '/usr/sbin/clamscan'
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        # Try to find via which
        try:
            result = subprocess.run(['which', 'clamscan'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None
    
    def _scan_file(self, file_path: str) -> Dict:
        """Scan a file with ClamAV"""
        if not self.clamscan_path:
            return {
                'is_malware': False,
                'threat_name': None,
                'scan_result': 'clamav_not_available'
            }
        
        try:
            # Find URLhaus signature database
            urlhaus_db = None
            possible_db_paths = [
                '/opt/homebrew/var/lib/clamav/urlhaus.ndb',
                f'{os.path.expanduser("~")}/.clamav/urlhaus.ndb',
                '/var/lib/clamav/urlhaus.ndb',
                '/usr/local/var/lib/clamav/urlhaus.ndb'
            ]
            
            for db_path in possible_db_paths:
                if os.path.exists(db_path):
                    urlhaus_db = db_path
                    break
            
            # Build ClamAV scan command
            scan_cmd = [
                self.clamscan_path,
                '--no-summary',  # Don't show summary
                '--infected',    # Only show infected files
            ]
            
            # Add URLhaus database if found
            if urlhaus_db:
                scan_cmd.extend(['-d', urlhaus_db])
            
            scan_cmd.append(file_path)
            
            # Run ClamAV scan
            result = subprocess.run(
                scan_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # No malware found
                return {
                    'is_malware': False,
                    'threat_name': None,
                    'scan_result': 'clean'
                }
            elif result.returncode == 1:
                # Malware found
                output = result.stdout.strip()
                threat_name = "Unknown"
                
                # Extract threat name from output
                if ':' in output:
                    threat_name = output.split(':')[-1].strip()
                
                return {
                    'is_malware': True,
                    'threat_name': threat_name,
                    'scan_result': 'infected'
                }
            else:
                # Error
                logger.error(f"ClamAV scan error: {result.stderr}")
                return {
                    'is_malware': False,
                    'threat_name': None,
                    'scan_result': 'error'
                }
                
        except subprocess.TimeoutExpired:
            logger.error("ClamAV scan timeout")
            return {
                'is_malware': False,
                'threat_name': None,
                'scan_result': 'timeout'
            }
        except Exception as e:
            logger.error(f"ClamAV scan error: {e}")
            return {
                'is_malware': False,
                'threat_name': None,
                'scan_result': 'error'
            }
    
    def _create_test_file(self, content: str, filename: str) -> str:
        """Create a test file for scanning"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=f'_{filename}', delete=False)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name
    
    def analyze_email(self, email_data: Dict) -> Dict:
        """Analyze email attachments for malware"""
        if not self.enabled:
            return {
                'is_malware': False,
                'threat_name': None,
                'scan_result': 'disabled',
                'attachments_scanned': 0
            }
        
        attachments = email_data.get('attachments', [])
        if not attachments:
            return {
                'is_malware': False,
                'threat_name': None,
                'scan_result': 'no_attachments',
                'attachments_scanned': 0
            }
        
        malware_found = False
        threat_names = []
        scanned_count = 0
        
        for attachment in attachments:
            try:
                # Get attachment content
                content = attachment.get('content', '')
                filename = attachment.get('filename', 'unknown')
                
                if not content:
                    continue
                
                # Create temporary file for scanning
                temp_file = self._create_test_file(content, filename)
                
                # Scan the file
                scan_result = self._scan_file(temp_file)
                scanned_count += 1
                
                # Clean up temp file
                os.unlink(temp_file)
                
                if scan_result['is_malware']:
                    malware_found = True
                    threat_names.append(scan_result['threat_name'])
                    logger.warning(f"Malware detected in {filename}: {scan_result['threat_name']}")
                
            except Exception as e:
                logger.error(f"Error scanning attachment {filename}: {e}")
        
        return {
            'is_malware': malware_found,
            'threat_name': threat_names[0] if threat_names else None,
            'threat_names': threat_names,
            'scan_result': 'completed',
            'attachments_scanned': scanned_count
        }

# Test the detector
if __name__ == "__main__":
    detector = ClamAVDetector({'enabled': True})
    
    # Test with a suspicious attachment
    test_email = {
        'sender': 'malicious@evil.com',
        'recipients': ['test@example.com'],
        'subject': 'Important Document',
        'body_plain': 'Please find the attached document.',
        'attachments': [
            {
                'filename': 'suspicious.exe',
                'content': 'This is a test file that might be detected as malware'
            }
        ]
    }
    
    result = detector.analyze_email(test_email)
    print(f"ClamAV scan result: {result}")