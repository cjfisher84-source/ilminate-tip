"""
Enhanced APEX Detection Engine
Uses all available detection layers
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import yaml
import os
import sys

# Add plugins to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plugins'))

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
    action: Action
    threat_level: ThreatLevel
    risk_score: float  # 0-100
    confidence: float  # 0-1
    threats: List[Dict]
    indicators: List[str]
    explanation: str
    duration_ms: float
    active_layers: List[str]

class EnhancedAPEXDetector:
    """Enhanced APEX detector using all available layers"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.version = "2.0.0-enhanced"
        self.active_layers = []
        
        # Initialize all available detectors
        self._init_detectors()
        
        logging.info(f"Enhanced APEX Detection Engine v{self.version} initialized")
        logging.info(f"Active layers: {self.active_layers}")
    
    def _init_detectors(self):
        """Initialize all available detection layers"""
        
        # Basic rules detector (always available)
        self.basic_detector = None
        try:
            from simple_apex_detector import SimpleAPEXDetector
            self.basic_detector = SimpleAPEXDetector(self.config)
            self.active_layers.append("Basic-Rules")
            logging.info("✓ Basic Rules detector loaded")
        except Exception as e:
            logging.error(f"Failed to load Basic Rules: {e}")
        
        # SpamAssassin detector
        self.spamassassin = None
        try:
            from spamassassin_detector import SpamAssassinDetector
            layer_config = self.config.get('detection_layers', {}).get('traditional_scanning', {}).get('spamassassin', {})
            if layer_config.get('enabled', True):
                self.spamassassin = SpamAssassinDetector(layer_config)
                self.active_layers.append("SpamAssassin")
                logging.info("✓ SpamAssassin detector loaded")
        except Exception as e:
            logging.warning(f"SpamAssassin not available: {e}")
        
        # ClamAV detector
        self.clamav = None
        try:
            from clamav_detector import ClamAVDetector
            layer_config = self.config.get('detection_layers', {}).get('traditional_scanning', {}).get('clamav', {})
            if layer_config.get('enabled', True):
                self.clamav = ClamAVDetector(layer_config)
                self.active_layers.append("ClamAV")
                logging.info("✓ ClamAV detector loaded")
        except Exception as e:
            logging.warning(f"ClamAV not available: {e}")
        
        # YARA detector
        self.yara = None
        try:
            from yara_detector import YARADetector
            layer_config = self.config.get('detection_layers', {}).get('yara_rules', {})
            if layer_config.get('enabled', True):
                self.yara = YARADetector(layer_config)
                self.active_layers.append("YARA")
                logging.info("✓ YARA detector loaded")
        except Exception as e:
            logging.warning(f"YARA not available: {e}")
        
        # Feature ML detector
        self.feature_ml = None
        try:
            from feature_ml_detector import FeatureMLDetector
            layer_config = self.config.get('detection_layers', {}).get('feature_ml', {})
            if layer_config.get('enabled', True):
                self.feature_ml = FeatureMLDetector(layer_config)
                self.active_layers.append("Feature-ML")
                logging.info("✓ Feature ML detector loaded")
        except Exception as e:
            logging.warning(f"Feature ML not available: {e}")
        
        # Deep Learning detector
        self.deep_learning = None
        try:
            from email_security_plugin import EmailSecurityPlugin
            layer_config = self.config.get('detection_layers', {}).get('deep_learning', {})
            if layer_config.get('enabled', True):
                self.deep_learning = EmailSecurityPlugin(layer_config)
                self.active_layers.append("Deep-Learning")
                logging.info("✓ Deep Learning detector loaded")
        except Exception as e:
            logging.warning(f"Deep Learning not available: {e}")
    
    async def analyze_email(self, email: Dict) -> APEXVerdict:
        """Analyze email using all available detection layers"""
        start_time = time.time()
        
        email_id = email.get('subject', 'unknown')
        all_threats = []
        all_indicators = []
        layer_scores = {}
        
        # Run all available detectors
        detectors = [
            ("Basic-Rules", self.basic_detector),
            ("SpamAssassin", self.spamassassin),
            ("ClamAV", self.clamav),
            ("YARA", self.yara),
            ("Feature-ML", self.feature_ml),
            ("Deep-Learning", self.deep_learning)
        ]
        
        for layer_name, detector in detectors:
            if detector is None:
                continue
            
            try:
                if hasattr(detector, 'analyze_email'):
                    result = await detector.analyze_email(email)
                    
                    # Collect threats and indicators
                    if hasattr(result, 'threats') and result.threats:
                        all_threats.extend(result.threats)
                    
                    if hasattr(result, 'indicators') and result.indicators:
                        all_indicators.extend(result.indicators)
                    
                    # Collect risk scores
                    if hasattr(result, 'risk_score'):
                        layer_scores[layer_name] = result.risk_score
                    
                    logging.debug(f"{layer_name} analysis complete: {result.action if hasattr(result, 'action') else 'Unknown'}")
                
            except Exception as e:
                logging.warning(f"Error in {layer_name} detector: {e}")
        
        # Calculate ensemble score
        if layer_scores:
            # Weighted average of all layer scores
            weights = {
                "Basic-Rules": 0.2,
                "SpamAssassin": 0.3,
                "ClamAV": 0.4,
                "YARA": 0.6,
                "Feature-ML": 0.7,
                "Deep-Learning": 0.8
            }
            
            weighted_score = 0
            total_weight = 0
            
            for layer, score in layer_scores.items():
                weight = weights.get(layer, 0.5)
                weighted_score += score * weight
                total_weight += weight
            
            if total_weight > 0:
                risk_score = (weighted_score / total_weight) * 100
            else:
                risk_score = 0
        else:
            risk_score = 0
        
        # Determine action based on thresholds
        thresholds = self.config.get('ensemble', {}).get('thresholds', {
            'allow': 0.2,
            'quarantine': 0.4,
            'block': 0.6
        })
        
        if risk_score >= thresholds['block'] * 100:
            action = Action.BLOCK
            threat_level = ThreatLevel.CRITICAL
        elif risk_score >= thresholds['quarantine'] * 100:
            action = Action.QUARANTINE
            threat_level = ThreatLevel.HIGH
        elif risk_score >= thresholds['allow'] * 100:
            action = Action.QUARANTINE
            threat_level = ThreatLevel.MEDIUM
        else:
            action = Action.ALLOW
            threat_level = ThreatLevel.CLEAN
        
        # Generate explanation
        if all_threats:
            explanation = f"Detected {len(all_threats)} threat(s) across {len(self.active_layers)} layers with risk score {risk_score:.1f}%"
        else:
            explanation = "No significant threats detected across all layers. Email appears legitimate."
        
        duration_ms = (time.time() - start_time) * 1000
        
        return APEXVerdict(
            email_id=email_id,
            timestamp=datetime.now(),
            action=action,
            threat_level=threat_level,
            risk_score=risk_score,
            confidence=0.9 if all_threats else 0.5,
            threats=all_threats,
            indicators=all_indicators,
            explanation=explanation,
            duration_ms=duration_ms,
            active_layers=self.active_layers
        )

def main():
    """Test the enhanced APEX detector"""
    import yaml
    
    # Load config
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'apex-full-config.yml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize detector
    detector = EnhancedAPEXDetector(config)
    
    print(f"Enhanced APEX Detector initialized with {len(detector.active_layers)} active layers:")
    for layer in detector.active_layers:
        print(f"  ✓ {layer}")
    
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
            "subject": "Meeting Reminder",
            "from": "colleague@company.com",
            "to": "spam@ilminate.com",
            "body": "Don't forget about our meeting tomorrow at 2 PM.",
            "attachments": [],
            "headers": {"X-Mailer": "Outlook"}
        }
    ]
    
    print("\nTesting enhanced detector...")
    
    for i, email in enumerate(test_emails, 1):
        print(f"\nTest {i}: {email['subject']}")
        result = asyncio.run(detector.analyze_email(email))
        
        print(f"  Verdict: {result.action}")
        print(f"  Risk Score: {result.risk_score:.1f}%")
        print(f"  Threat Level: {result.threat_level}")
        print(f"  Active Layers: {len(result.active_layers)}")
        print(f"  Threats: {len(result.threats)}")

if __name__ == "__main__":
    main()



