"""
Simplified APEX Detection Engine
Uses basic rules instead of external tools for testing
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re

class Action(Enum):
    ALLOW = "ALLOW"
    QUARANTINE = "QUARANTINE"
    BLOCK = "BLOCK"

class ThreatLevel(Enum):
    CLEAN = "CLEAN"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class APEXVerdict:
    """Final APEX detection verdict"""
    email_id: str
    timestamp: datetime
    
    # Overall verdict
    action: Action
    threat_level: ThreatLevel
    risk_score: float  # 0-100
    confidence: float  # 0-1
    
    # Detection details
    threats: List[Dict]
    indicators: List[str]
    explanation: str
    
    # Performance metrics
    duration_ms: float
    active_layers: List[str]

class SimpleAPEXDetector:
    """Simplified APEX detector using basic rules"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.version = "2.0.0-simple"
        
        # Load basic rules
        self.phishing_keywords = config.get('basic_rules', {}).get('phishing_keywords', [])
        self.suspicious_domains = config.get('basic_rules', {}).get('suspicious_domains', [])
        self.malware_extensions = config.get('basic_rules', {}).get('malware_extensions', [])
        self.bec_keywords = config.get('basic_rules', {}).get('bec_keywords', [])
        
        # Thresholds
        self.thresholds = config.get('ensemble', {}).get('thresholds', {
            'allow': 0.2,
            'quarantine': 0.4,
            'block': 0.6
        })
        
        logging.info(f"SimpleAPEXDetector initialized with {len(self.phishing_keywords)} phishing keywords")
    
    async def analyze_email(self, email: Dict) -> APEXVerdict:
        """Analyze email using basic rules"""
        start_time = time.time()
        
        email_id = email.get('subject', 'unknown')
        threats = []
        indicators = []
        risk_score = 0.0
        
        # Check phishing keywords
        phishing_score = self._check_phishing_keywords(email)
        if phishing_score > 0:
            risk_score += phishing_score * 0.4
            threats.append({
                'type': 'phishing',
                'severity': 'high' if phishing_score > 0.7 else 'medium',
                'description': f'Contains {phishing_score:.2f} phishing indicators'
            })
            indicators.append(f"Phishing keywords detected: {phishing_score:.2f}")
        
        # Check suspicious domains
        domain_score = self._check_suspicious_domains(email)
        if domain_score > 0:
            risk_score += domain_score * 0.3
            threats.append({
                'type': 'suspicious_domain',
                'severity': 'high',
                'description': f'From suspicious domain: {email.get("from", "unknown")}'
            })
            indicators.append(f"Suspicious domain: {email.get('from', 'unknown')}")
        
        # Check malware attachments
        malware_score = self._check_malware_attachments(email)
        if malware_score > 0:
            risk_score += malware_score * 0.5
            threats.append({
                'type': 'malware',
                'severity': 'critical',
                'description': 'Malicious attachment detected'
            })
            indicators.append("Malicious attachment detected")
        
        # Check BEC indicators
        bec_score = self._check_bec_indicators(email)
        if bec_score > 0:
            risk_score += bec_score * 0.4
            threats.append({
                'type': 'bec',
                'severity': 'high',
                'description': f'BEC attack indicators: {bec_score:.2f}'
            })
            indicators.append(f"BEC indicators: {bec_score:.2f}")
        
        # Check URL patterns
        url_score = self._check_suspicious_urls(email)
        if url_score > 0:
            risk_score += url_score * 0.3
            threats.append({
                'type': 'suspicious_url',
                'severity': 'medium',
                'description': 'Suspicious URL patterns detected'
            })
            indicators.append("Suspicious URL patterns")
        
        # Cap risk score at 100
        risk_score = min(risk_score * 100, 100)
        
        # Determine action based on thresholds
        if risk_score >= self.thresholds['block'] * 100:
            action = Action.BLOCK
            threat_level = ThreatLevel.CRITICAL
        elif risk_score >= self.thresholds['quarantine'] * 100:
            action = Action.QUARANTINE
            threat_level = ThreatLevel.HIGH
        elif risk_score >= self.thresholds['allow'] * 100:
            action = Action.QUARANTINE
            threat_level = ThreatLevel.MEDIUM
        else:
            action = Action.ALLOW
            threat_level = ThreatLevel.CLEAN
        
        # Generate explanation
        if threats:
            explanation = f"Detected {len(threats)} threat(s) with risk score {risk_score:.1f}%"
        else:
            explanation = "No significant threats detected. Email appears legitimate."
        
        duration_ms = (time.time() - start_time) * 1000
        
        return APEXVerdict(
            email_id=email_id,
            timestamp=datetime.now(),
            action=action,
            threat_level=threat_level,
            risk_score=risk_score,
            confidence=0.8 if threats else 0.5,
            threats=threats,
            indicators=indicators,
            explanation=explanation,
            duration_ms=duration_ms,
            active_layers=['basic_rules']
        )
    
    def _check_phishing_keywords(self, email: Dict) -> float:
        """Check for phishing keywords"""
        text = f"{email.get('subject', '')} {email.get('body', '')}".lower()
        
        matches = 0
        for keyword in self.phishing_keywords:
            if keyword.lower() in text:
                matches += 1
        
        return min(matches / len(self.phishing_keywords), 1.0) if self.phishing_keywords else 0.0
    
    def _check_suspicious_domains(self, email: Dict) -> float:
        """Check for suspicious domains"""
        from_addr = email.get('from', '').lower()
        
        for domain in self.suspicious_domains:
            if domain.lower() in from_addr:
                return 1.0
        
        return 0.0
    
    def _check_malware_attachments(self, email: Dict) -> float:
        """Check for malware attachments"""
        attachments = email.get('attachments', [])
        
        for attachment in attachments:
            filename = attachment.get('name', '').lower()
            for ext in self.malware_extensions:
                if filename.endswith(ext):
                    return 1.0
        
        return 0.0
    
    def _check_bec_indicators(self, email: Dict) -> float:
        """Check for BEC indicators"""
        text = f"{email.get('subject', '')} {email.get('body', '')}".lower()
        
        matches = 0
        for keyword in self.bec_keywords:
            if keyword.lower() in text:
                matches += 1
        
        return min(matches / len(self.bec_keywords), 1.0) if self.bec_keywords else 0.0
    
    def _check_suspicious_urls(self, email: Dict) -> float:
        """Check for suspicious URL patterns"""
        text = email.get('body', '')
        
        # Look for suspicious URL patterns
        suspicious_patterns = [
            r'http://[^/]+\.tk/',
            r'http://[^/]+\.ml/',
            r'http://[^/]+\.ga/',
            r'http://[^/]+\.cf/',
            r'bit\.ly/',
            r'tinyurl\.com/',
            r't\.co/'
        ]
        
        matches = 0
        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
        
        return min(matches / len(suspicious_patterns), 1.0)

def main():
    """Main function for testing"""
    import yaml
    
    # Load config
    with open('config/apex-simple-config.yml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize detector
    detector = SimpleAPEXDetector(config)
    
    # Test with sample emails
    test_emails = [
        {
            "subject": "URGENT: Verify Your Account Now!",
            "from": "noreply@fake-bank.com",
            "to": "spam@ilminate.com",
            "body": "Click here to verify your account: http://malicious-site.com/phish",
            "attachments": [],
            "headers": {"X-Mailer": "FakeBank Phishing Tool"}
        },
        {
            "subject": "Wire Transfer Request - URGENT",
            "from": "ceo@company.com",
            "to": "finance@company.com",
            "body": "I need you to wire $50,000 to account 123456789 immediately.",
            "attachments": [],
            "headers": {"X-Mailer": "Outlook"}
        },
        {
            "subject": "Invoice Attached",
            "from": "billing@suspicious-site.com",
            "to": "spam@ilminate.com",
            "body": "Please find your invoice attached.",
            "attachments": [{"name": "invoice.exe", "type": "application/x-executable"}],
            "headers": {"X-Mailer": "Invoice System"}
        },
        {
            "subject": "Meeting Reminder",
            "from": "colleague@company.com",
            "to": "spam@ilminate.com",
            "body": "Don't forget about our meeting tomorrow at 2 PM.",
            "attachments": [],
            "headers": {"X-Mailer": "Outlook"}
        }
    ]
    
    print("="*80)
    print("SIMPLE APEX DETECTOR TEST")
    print("="*80)
    
    for i, email in enumerate(test_emails, 1):
        print(f"\nTest {i}: {email['subject']}")
        result = asyncio.run(detector.analyze_email(email))
        
        print(f"  Verdict: {result.action}")
        print(f"  Risk Score: {result.risk_score:.1f}%")
        print(f"  Threat Level: {result.threat_level}")
        print(f"  Threats: {len(result.threats)}")
        if result.threats:
            for threat in result.threats:
                print(f"    - {threat['type']}: {threat['description']}")

if __name__ == "__main__":
    main()



