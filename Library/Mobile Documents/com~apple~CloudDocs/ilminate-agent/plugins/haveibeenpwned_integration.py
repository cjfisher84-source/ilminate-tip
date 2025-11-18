#!/usr/bin/env python3
"""
HaveIBeenPwned Integration for APEX
Checks emails against HaveIBeenPwned breach database
"""

import os
import yaml
import requests
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class HaveIBeenPwnedIntegration:
    """Integration with HaveIBeenPwned API"""
    
    def __init__(self, api_key: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize HaveIBeenPwned integration
        
        Args:
            api_key: HaveIBeenPwned API key (optional, will load from config if not provided)
            config_path: Path to mosint config file (default: ~/.mosint.yaml)
        """
        self.api_key = api_key
        self.base_url = "https://haveibeenpwned.com/api/v3"
        
        # Load API key from config if not provided
        if not self.api_key:
            self.api_key = self._load_api_key(config_path)
        
        if not self.api_key:
            logger.warning("⚠️ HaveIBeenPwned API key not found - integration disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("✅ HaveIBeenPwned integration initialized")
    
    def _load_api_key(self, config_path: Optional[str] = None) -> Optional[str]:
        """Load API key from mosint config file"""
        if not config_path:
            config_path = os.path.expanduser("~/.mosint.yaml")
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'haveibeenpwned_api_key' in config:
                        api_key = config.get('haveibeenpwned_api_key', '').strip()
                        if api_key:
                            return api_key
        except Exception as e:
            logger.debug(f"Error loading HaveIBeenPwned API key: {e}")
        
        return None
    
    def check_email(self, email: str) -> Dict:
        """
        Check if email has been breached
        
        Args:
            email: Email address to check
        
        Returns:
            Dictionary with breach information
        """
        if not self.enabled:
            return {'enabled': False, 'error': 'API key not configured'}
        
        url = f"{self.base_url}/breachedaccount/{email}"
        headers = {
            'hibp-api-key': self.api_key,
            'User-Agent': 'APEX-Email-Security'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                breaches = response.json()
                return {
                    'enabled': True,
                    'found': True,
                    'breach_count': len(breaches),
                    'breaches': breaches,
                    'success': True
                }
            elif response.status_code == 404:
                return {
                    'enabled': True,
                    'found': False,
                    'breach_count': 0,
                    'breaches': [],
                    'success': True
                }
            elif response.status_code == 401:
                logger.warning("HaveIBeenPwned: Invalid API key")
                return {
                    'enabled': True,
                    'found': False,
                    'error': 'Invalid API key',
                    'success': False
                }
            elif response.status_code == 429:
                logger.warning("HaveIBeenPwned: Rate limit exceeded")
                return {
                    'enabled': True,
                    'found': False,
                    'error': 'Rate limit exceeded',
                    'success': False,
                    'rate_limited': True
                }
            else:
                logger.warning(f"HaveIBeenPwned API error: {response.status_code}")
                return {
                    'enabled': True,
                    'found': False,
                    'error': f"API error: {response.status_code}",
                    'success': False
                }
        except requests.exceptions.Timeout:
            logger.warning("HaveIBeenPwned: Request timeout")
            return {
                'enabled': True,
                'found': False,
                'error': 'Request timeout',
                'success': False
            }
        except Exception as e:
            logger.error(f"HaveIBeenPwned check error: {e}")
            return {
                'enabled': True,
                'found': False,
                'error': str(e),
                'success': False
            }
    
    def check_pastes(self, email: str) -> Dict:
        """
        Check if email appears in pastes
        
        Args:
            email: Email address to check
        
        Returns:
            Dictionary with paste information
        """
        if not self.enabled:
            return {'enabled': False, 'error': 'API key not configured'}
        
        url = f"{self.base_url}/pasteaccount/{email}"
        headers = {
            'hibp-api-key': self.api_key,
            'User-Agent': 'APEX-Email-Security'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                pastes = response.json()
                return {
                    'enabled': True,
                    'found': len(pastes) > 0,
                    'paste_count': len(pastes),
                    'pastes': pastes,
                    'success': True
                }
            elif response.status_code == 404:
                return {
                    'enabled': True,
                    'found': False,
                    'paste_count': 0,
                    'pastes': [],
                    'success': True
                }
            else:
                return {
                    'enabled': True,
                    'found': False,
                    'error': f"API error: {response.status_code}",
                    'success': False
                }
        except Exception as e:
            logger.error(f"HaveIBeenPwned paste check error: {e}")
            return {
                'enabled': True,
                'found': False,
                'error': str(e),
                'success': False
            }

