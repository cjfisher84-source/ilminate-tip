#!/usr/bin/env python3
"""
Mosint OSINT Detector for APEX
Integrates mosint OSINT tool into APEX detection engine
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Tuple
import json
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from plugins.mosint_integration import MosintIntegration
    MOSINT_AVAILABLE = True
except ImportError:
    MOSINT_AVAILABLE = False
    logging.warning("Mosint integration not available")

try:
    from plugins.haveibeenpwned_integration import HaveIBeenPwnedIntegration
    HIBP_AVAILABLE = True
except ImportError:
    HIBP_AVAILABLE = False
    logging.warning("HaveIBeenPwned integration not available")

logger = logging.getLogger(__name__)


class MosintDetector:
    """
    Mosint OSINT Detector for APEX
    Provides BEC detection, ATO detection, email verification, and reputation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Mosint detector
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        
        if not MOSINT_AVAILABLE:
            logger.warning("Mosint not available - detector disabled")
            self.enabled = False
            return
        
        try:
            config_path = self.config.get('config_path')
            self.mosint = MosintIntegration(config_path=config_path)
            logger.info("✅ Mosint detector initialized")
            
            # Initialize HaveIBeenPwned integration
            if HIBP_AVAILABLE:
                try:
                    self.hibp = HaveIBeenPwnedIntegration(config_path=config_path)
                    if self.hibp.enabled:
                        logger.info("✅ HaveIBeenPwned integration initialized")
                    else:
                        self.hibp = None
                except Exception as e:
                    logger.debug(f"HaveIBeenPwned not available: {e}")
                    self.hibp = None
            else:
                self.hibp = None
        except Exception as e:
            logger.error(f"Failed to initialize Mosint: {e}")
            self.enabled = False
            self.hibp = None
    
    def check_bec_indicators(self, sender_email: str) -> Dict:
        """
        Check for BEC indicators using mosint
        
        Args:
            sender_email: Sender email address
        
        Returns:
            Dictionary with BEC detection results
        """
        if not self.enabled:
            return {'enabled': False}
        
        try:
            # Find related domains (uses 1 Hunter.io credit)
            result = self.mosint.find_related_domains(sender_email)
            
            if not result.get('success'):
                # Check if rate limited
                if result.get('rate_limited'):
                    logger.debug("Hunter.io rate limit reached - skipping BEC check")
                    return {
                        'enabled': True,
                        'detected': False,
                        'score': 0.0,
                        'related_domains': [],
                        'rate_limited': True,
                        'error': 'Rate limit exceeded'
                    }
                return {
                    'enabled': True,
                    'detected': False,
                    'score': 0.0,
                    'related_domains': [],
                    'error': result.get('error')
                }
            
            related_domains = result.get('related_domains', [])
            domain_count = result.get('domain_count', 0)
            
            # Calculate BEC risk score
            # More related domains = higher risk
            risk_score = min(domain_count * 0.15, 1.0) if domain_count > 0 else 0.0
            
            # Check if any domains are suspicious (lookalike domains)
            suspicious_domains = []
            sender_domain = sender_email.split('@')[1] if '@' in sender_email else ''
            
            for domain in related_domains:
                # Check for lookalike patterns
                if self._is_lookalike_domain(domain, sender_domain):
                    suspicious_domains.append(domain)
                    risk_score = min(risk_score + 0.3, 1.0)
            
            detected = risk_score >= 0.3 or len(suspicious_domains) > 0
            
            return {
                'enabled': True,
                'detected': detected,
                'score': risk_score,
                'related_domains': related_domains,
                'suspicious_domains': suspicious_domains,
                'domain_count': domain_count,
                'reason': f'Found {domain_count} related domains, {len(suspicious_domains)} suspicious' if detected else 'No BEC indicators found'
            }
            
        except Exception as e:
            logger.error(f"BEC check error: {e}")
            return {
                'enabled': True,
                'detected': False,
                'score': 0.0,
                'error': str(e)
            }
    
    def check_ato_indicators(self, sender_email: str) -> Dict:
        """
        Check for Account Takeover (ATO) indicators using mosint and HaveIBeenPwned
        
        Args:
            sender_email: Sender email address
        
        Returns:
            Dictionary with ATO detection results
        """
        if not self.enabled:
            return {'enabled': False}
        
        all_breaches = []
        breach_sources = []
        total_breach_count = 0
        
        try:
            # Check breaches via mosint (Intelligence X, BreachDirectory, EmailRep)
            mosint_result = self.mosint.check_breaches(sender_email)
            
            if mosint_result.get('success'):
                mosint_breaches = mosint_result.get('breaches', [])
                mosint_count = mosint_result.get('breach_count', 0)
                if mosint_count > 0:
                    all_breaches.extend(mosint_breaches)
                    breach_sources.append('Mosint')
                    total_breach_count += mosint_count
            
            # Check HaveIBeenPwned (if available)
            if self.hibp and self.hibp.enabled:
                try:
                    hibp_result = self.hibp.check_email(sender_email)
                    if hibp_result.get('success') and hibp_result.get('found'):
                        hibp_breaches = hibp_result.get('breaches', [])
                        hibp_count = hibp_result.get('breach_count', 0)
                        if hibp_count > 0:
                            # Add HaveIBeenPwned breaches (format: {'Name': name, 'BreachDate': date, ...})
                            all_breaches.extend(hibp_breaches)
                            breach_sources.append('HaveIBeenPwned')
                            total_breach_count += hibp_count
                except Exception as e:
                    logger.debug(f"HaveIBeenPwned check error: {e}")
            
            # Calculate ATO risk score based on total breaches
            # More breaches = higher risk
            risk_score = min(total_breach_count * 0.15, 1.0) if total_breach_count > 0 else 0.0
            
            # High risk if breach count > 3 or multiple sources
            if total_breach_count > 3:
                risk_score = min(risk_score + 0.3, 1.0)
            
            if len(breach_sources) > 1:
                risk_score = min(risk_score + 0.2, 1.0)  # Multiple sources = higher confidence
            
            detected = total_breach_count > 0
            
            return {
                'enabled': True,
                'detected': detected,
                'score': risk_score,
                'breaches': all_breaches,
                'breach_count': total_breach_count,
                'sources': breach_sources,
                'reason': f'Email found in {total_breach_count} breach(es) across {len(breach_sources)} source(s)' if detected else 'No breaches found'
            }
            
        except Exception as e:
            logger.error(f"ATO check error: {e}")
            return {
                'enabled': True,
                'detected': False,
                'score': 0.0,
                'error': str(e)
            }
    
    def verify_email(self, email: str) -> Dict:
        """
        Verify email address validity
        
        Args:
            email: Email address to verify
        
        Returns:
            Dictionary with verification results
        """
        if not self.enabled:
            return {'enabled': False}
        
        try:
            result = self.mosint.verify_email(email)
            
            if not result.get('success'):
                return {
                    'enabled': True,
                    'valid': False,
                    'error': result.get('error')
                }
            
            verification = result.get('verification', {})
            valid = verification.get('valid', False)
            
            return {
                'enabled': True,
                'valid': valid,
                'verification': verification
            }
            
        except Exception as e:
            logger.error(f"Email verification error: {e}")
            return {
                'enabled': True,
                'valid': False,
                'error': str(e)
            }
    
    def get_reputation(self, email: str) -> Dict:
        """
        Get email reputation score
        
        Args:
            email: Email address to check
        
        Returns:
            Dictionary with reputation information
        """
        if not self.enabled:
            return {'enabled': False}
        
        try:
            result = self.mosint.get_reputation(email)
            
            if not result.get('success'):
                return {
                    'enabled': True,
                    'score': 0.5,  # Neutral score
                    'error': result.get('error')
                }
            
            reputation = result.get('reputation', {})
            score = reputation.get('score', 0.5)
            
            return {
                'enabled': True,
                'score': score,
                'reputation': reputation
            }
            
        except Exception as e:
            logger.error(f"Reputation check error: {e}")
            return {
                'enabled': True,
                'score': 0.5,
                'error': str(e)
            }
    
    def _is_lookalike_domain(self, domain1: str, domain2: str) -> bool:
        """
        Check if two domains are lookalikes (for BEC detection)
        
        Args:
            domain1: First domain
            domain2: Second domain
        
        Returns:
            True if domains are lookalikes
        """
        if not domain1 or not domain2:
            return False
        
        # Normalize domains
        domain1 = domain1.lower().strip()
        domain2 = domain2.lower().strip()
        
        # Exact match is not suspicious
        if domain1 == domain2:
            return False
        
        # Check for character substitution (e.g., microsft.com vs microsoft.com)
        if len(domain1) == len(domain2):
            differences = sum(c1 != c2 for c1, c2 in zip(domain1, domain2))
            if differences <= 2:  # 1-2 character differences
                return True
        
        # Check for missing/extra characters (e.g., microsoftt.com vs microsoft.com)
        if abs(len(domain1) - len(domain2)) <= 2:
            if domain1 in domain2 or domain2 in domain1:
                return True
        
        # Check for common TLD swaps (e.g., .com vs .co)
        domain1_base = domain1.rsplit('.', 1)[0] if '.' in domain1 else domain1
        domain2_base = domain2.rsplit('.', 1)[0] if '.' in domain2 else domain2
        
        if domain1_base == domain2_base:
            return True
        
        return False


def main():
    """Test mosint detector"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mosint_detector.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    
    detector = MosintDetector()
    
    print(f"🔍 Testing Mosint Detector for {email}")
    print("=" * 70)
    
    # BEC check
    print("\n1. BEC Detection:")
    bec_result = detector.check_bec_indicators(email)
    print(f"   Detected: {bec_result.get('detected', False)}")
    print(f"   Score: {bec_result.get('score', 0.0):.2f}")
    print(f"   Related Domains: {bec_result.get('domain_count', 0)}")
    if bec_result.get('suspicious_domains'):
        print(f"   Suspicious: {bec_result.get('suspicious_domains')}")
    
    # ATO check
    print("\n2. ATO Detection:")
    ato_result = detector.check_ato_indicators(email)
    print(f"   Detected: {ato_result.get('detected', False)}")
    print(f"   Score: {ato_result.get('score', 0.0):.2f}")
    print(f"   Breaches: {ato_result.get('breach_count', 0)}")
    
    # Email verification
    print("\n3. Email Verification:")
    verify_result = detector.verify_email(email)
    print(f"   Valid: {verify_result.get('valid', False)}")
    
    # Reputation
    print("\n4. Reputation:")
    rep_result = detector.get_reputation(email)
    print(f"   Score: {rep_result.get('score', 0.5):.2f}")

if __name__ == '__main__':
    main()

