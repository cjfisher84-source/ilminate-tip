#!/usr/bin/env python3
"""
Mosint Integration for APEX
Python wrapper for mosint OSINT tool
"""

import os
import json
import subprocess
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class MosintIntegration:
    """Integration wrapper for mosint OSINT tool"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Mosint integration
        
        Args:
            config_path: Path to mosint config file (default: ~/.mosint.yaml)
        """
        # Find mosint binary
        self.mosint_path = self._find_mosint()
        if not self.mosint_path:
            raise RuntimeError("mosint not found. Install with: go install github.com/alpkeskin/mosint/v3/cmd/mosint@latest")
        
        # Config file path
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = os.path.expanduser("~/.mosint.yaml")
        
        logger.info(f"✅ Mosint integration initialized: {self.mosint_path}")
    
    def _find_mosint(self) -> Optional[str]:
        """Find mosint binary in PATH or Go bin directory"""
        # Check PATH
        result = subprocess.run(['which', 'mosint'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        
        # Check Go bin directory
        go_path_result = subprocess.run(['go', 'env', 'GOPATH'], capture_output=True, text=True)
        if go_path_result.returncode == 0:
            go_path = go_path_result.stdout.strip()
            mosint_path = os.path.join(go_path, 'bin', 'mosint')
            if os.path.exists(mosint_path):
                return mosint_path
        
        return None
    
    def scan_email(self, email: str, output_file: Optional[str] = None) -> Dict:
        """
        Scan email address with mosint
        
        Args:
            email: Email address to scan
            output_file: Optional JSON output file path
        
        Returns:
            Dictionary with scan results
        """
        try:
            # Build command
            cmd = [self.mosint_path, email]
            
            # Add config file (required by mosint)
            # Use default location if exists, otherwise create empty one
            if not os.path.exists(self.config_path):
                # Create empty config file
                Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_path, 'w') as f:
                    f.write("# Mosint config file\n")
            
            cmd.extend(['--config', self.config_path])
            
            # Add output file if specified
            if output_file:
                cmd.extend(['--output', output_file])
            
            # Run mosint
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode != 0:
                # Check for rate limit errors
                if 'rate limit' in result.stderr.lower() or 'quota' in result.stderr.lower():
                    logger.warning(f"Hunter.io rate limit reached: {result.stderr}")
                    return {'error': 'Rate limit exceeded', 'success': False, 'rate_limited': True}
                logger.error(f"Mosint scan failed: {result.stderr}")
                return {'error': result.stderr, 'success': False}
            
            # Parse output
            if output_file and os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    data = json.load(f)
                return {'success': True, 'data': data}
            else:
                # Parse text output
                return {'success': True, 'output': result.stdout}
                
        except subprocess.TimeoutExpired:
            logger.error("Mosint scan timed out")
            return {'error': 'Timeout', 'success': False}
        except Exception as e:
            logger.error(f"Mosint scan error: {e}")
            return {'error': str(e), 'success': False}
    
    def check_breaches(self, email: str) -> Dict:
        """
        Check if email appears in data breaches
        
        Args:
            email: Email address to check
        
        Returns:
            Dictionary with breach information
        """
        result = self.scan_email(email)
        if not result.get('success'):
            return result
        
        data = result.get('data', {})
        breaches = []
        
        # Extract breach information from various sources
        if 'haveibeenpwned' in data:
            breaches.extend(data['haveibeenpwned'].get('breaches', []))
        
        if 'breachdirectory' in data:
            breaches.extend(data['breachdirectory'].get('breaches', []))
        
        if 'intelx' in data:
            breaches.extend(data['intelx'].get('breaches', []))
        
        return {
            'success': True,
            'email': email,
            'breaches': breaches,
            'breach_count': len(breaches)
        }
    
    def find_related_domains(self, email: str) -> Dict:
        """
        Find domains related to email address
        
        Args:
            email: Email address to check
        
        Returns:
            Dictionary with related domains
        """
        result = self.scan_email(email)
        if not result.get('success'):
            return result
        
        data = result.get('data', {})
        domains = []
        
        # Extract domain information
        if 'hunter' in data:
            hunter_data = data['hunter']
            if 'related_emails' in hunter_data:
                for related_email in hunter_data['related_emails']:
                    domain = related_email.get('domain')
                    if domain and domain not in domains:
                        domains.append(domain)
        
        if 'ipapi' in data:
            ipapi_data = data['ipapi']
            domain = ipapi_data.get('domain')
            if domain and domain not in domains:
                domains.append(domain)
        
        return {
            'success': True,
            'email': email,
            'related_domains': domains,
            'domain_count': len(domains)
        }
    
    def verify_email(self, email: str) -> Dict:
        """
        Verify email address validity
        
        Args:
            email: Email address to verify
        
        Returns:
            Dictionary with verification results
        """
        result = self.scan_email(email)
        if not result.get('success'):
            return result
        
        data = result.get('data', {})
        verification = {}
        
        # Extract verification information
        if 'verification' in data:
            verification = data['verification']
        
        return {
            'success': True,
            'email': email,
            'verification': verification
        }
    
    def get_reputation(self, email: str) -> Dict:
        """
        Get email reputation score
        
        Args:
            email: Email address to check
        
        Returns:
            Dictionary with reputation information
        """
        result = self.scan_email(email)
        if not result.get('success'):
            return result
        
        data = result.get('data', {})
        reputation = {}
        
        # Extract reputation information
        if 'emailrep' in data:
            reputation = data['emailrep']
        
        return {
            'success': True,
            'email': email,
            'reputation': reputation
        }

def main():
    """Test mosint integration"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mosint_integration.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    
    try:
        mosint = MosintIntegration()
        
        print(f"🔍 Scanning {email} with mosint...")
        result = mosint.scan_email(email)
        
        if result.get('success'):
            print("✅ Scan completed successfully")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Scan failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()

