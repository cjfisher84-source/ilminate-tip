"""
Custom SpamAssassin Integration for APEX
Provides comprehensive spam detection using rule-based analysis
"""

import os
import sys
import time
import logging
from typing import Dict, List, Optional

# Add testing directory to path for custom_spamassassin import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'testing'))

try:
    from custom_spamassassin import SpamAssassinDetector as CustomSpamAssassinDetector
    SPAMASSASSIN_AVAILABLE = True
except ImportError:
    SPAMASSASSIN_AVAILABLE = False

logger = logging.getLogger(__name__)

class SpamAssassinDetector:
    """Custom SpamAssassin email detector for APEX"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.threshold = config.get('threshold', 5.0)
        
        if self.enabled and SPAMASSASSIN_AVAILABLE:
            # Initialize custom SpamAssassin
            self.spamassassin = CustomSpamAssassinDetector()
            self.spamassassin.spamassassin.set_threshold(self.threshold)
            logger.info("🛡️ SpamAssassin Detector initialized with custom implementation")
        else:
            logger.info("🛡️ SpamAssassin Detector disabled or not available")

    async def analyze_email(self, email_data: Dict) -> Dict:
        """Analyze email using custom SpamAssassin"""
        if not self.enabled or not SPAMASSASSIN_AVAILABLE:
            return {
                'verdict': 'ALLOW',
                'confidence': 0.0,
                'processing_time_ms': 0.0,
                'details': 'SpamAssassin disabled or not available'
            }
        
        try:
            # Use custom SpamAssassin implementation
            result = await self.spamassassin.detect_spam(email_data)
            
            return {
                'verdict': result['verdict'],
                'confidence': result['confidence'],
                'processing_time_ms': result['processing_time_ms'],
                'details': {
                    'spam_score': result['score'],
                    'threshold': result['threshold'],
                    'rules_matched': result['rules_matched'],
                    'is_spam': result['is_spam']
                }
            }
            
        except Exception as e:
            logger.error(f"SpamAssassin analysis error: {e}")
            return {
                'verdict': 'ALLOW',
                'confidence': 0.0,
                'processing_time_ms': 0.0,
                'details': f'Error: {str(e)}'
            }