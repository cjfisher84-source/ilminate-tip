"""
Ilminate Agent - Email Security Plugin
Version: 2.0.0
Python 3.9+

Advanced email security and threat detection plugin with AI/ML capabilities
"""

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

# Email processing
from email import message_from_string
from email.utils import parseaddr, parsedate_to_datetime
import mailbox

# ML/AI libraries
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers library not available. ML features will be limited.")

# Email server integrations
try:
    from exchangelib import Account, Credentials, Configuration, DELEGATE
    EXCHANGE_AVAILABLE = True
except ImportError:
    EXCHANGE_AVAILABLE = False

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ilminate.email_security')


# ============================================================================
# Data Models
# ============================================================================

class ThreatLevel(Enum):
    """Threat severity levels"""
    CLEAN = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ThreatCategory(Enum):
    """Threat categories"""
    PHISHING = "phishing"
    SPEAR_PHISHING = "spear_phishing"
    BEC = "business_email_compromise"
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    CREDENTIAL_HARVESTING = "credential_harvesting"
    SOCIAL_ENGINEERING = "social_engineering"
    AI_GENERATED = "ai_generated_phishing"
    DEEPFAKE = "deepfake_content"
    ACCOUNT_TAKEOVER = "account_takeover"
    DATA_EXFILTRATION = "data_exfiltration"
    SUPPLY_CHAIN = "supply_chain_attack"


@dataclass
class EmailMetadata:
    """Email metadata structure"""
    message_id: str
    sender: str
    sender_domain: str
    recipients: List[str]
    subject: str
    timestamp: datetime
    headers: Dict[str, str]
    has_attachments: bool
    attachment_count: int
    attachment_names: List[str]
    url_count: int
    urls: List[str]
    spf_result: Optional[str] = None
    dkim_result: Optional[str] = None
    dmarc_result: Optional[str] = None


@dataclass
class ThreatDetection:
    """Threat detection result"""
    threat_level: ThreatLevel
    threat_categories: List[ThreatCategory]
    confidence: float
    threat_score: float
    detection_methods: List[str]
    model_predictions: Dict[str, Dict]
    indicators: List[str]
    recommended_action: str
    explanation: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary"""
        data = asdict(self)
        data['threat_level'] = self.threat_level.name
        data['threat_categories'] = [cat.value for cat in self.threat_categories]
        data['timestamp'] = self.timestamp.isoformat()
        return data


# ============================================================================
# Email Parser
# ============================================================================

class EmailParser:
    """Parse and extract features from emails"""
    
    def __init__(self):
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
    def parse(self, raw_email: str) -> Tuple[EmailMetadata, str, str]:
        """
        Parse raw email into metadata and content
        
        Returns:
            (metadata, text_content, html_content)
        """
        msg = message_from_string(raw_email)
        
        # Extract basic fields
        sender = parseaddr(msg.get('From', ''))[1]
        sender_domain = sender.split('@')[-1] if '@' in sender else ''
        recipients = [parseaddr(addr)[1] for addr in msg.get_all('To', [])]
        subject = msg.get('Subject', '')
        
        # Parse timestamp
        date_str = msg.get('Date')
        try:
            timestamp = parsedate_to_datetime(date_str) if date_str else datetime.utcnow()
        except:
            timestamp = datetime.utcnow()
        
        # Extract all headers
        headers = {key: value for key, value in msg.items()}
        
        # Extract content
        text_content = ""
        html_content = ""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append(filename)
                elif content_type == "text/plain":
                    text_content += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif content_type == "text/html":
                    html_content += part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            if content_type == "text/plain":
                text_content = payload
            elif content_type == "text/html":
                html_content = payload
        
        # Extract URLs
        urls = list(set(self.url_pattern.findall(text_content + html_content)))
        
        # Authentication results
        spf_result = self._extract_auth_result(headers, 'spf')
        dkim_result = self._extract_auth_result(headers, 'dkim')
        dmarc_result = self._extract_auth_result(headers, 'dmarc')
        
        metadata = EmailMetadata(
            message_id=msg.get('Message-ID', ''),
            sender=sender,
            sender_domain=sender_domain,
            recipients=recipients,
            subject=subject,
            timestamp=timestamp,
            headers=headers,
            has_attachments=len(attachments) > 0,
            attachment_count=len(attachments),
            attachment_names=attachments,
            url_count=len(urls),
            urls=urls,
            spf_result=spf_result,
            dkim_result=dkim_result,
            dmarc_result=dmarc_result
        )
        
        return metadata, text_content, html_content
    
    def _extract_auth_result(self, headers: Dict, auth_type: str) -> Optional[str]:
        """Extract authentication results from headers"""
        auth_results = headers.get('Authentication-Results', '')
        
        if auth_type in auth_results.lower():
            match = re.search(f'{auth_type}=(\w+)', auth_results, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None


# ============================================================================
# AI Model Manager
# ============================================================================

class AIModelManager:
    """Manage and orchestrate multiple AI models"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.models = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        if TRANSFORMERS_AVAILABLE:
            self._load_models()
        else:
            logger.warning("Transformers not available. Using rule-based detection only.")
    
    def _load_models(self):
        """Load all configured AI models"""
        try:
            # BERT Phishing Detector
            if self.config.get('bert_enabled', True):
                logger.info("Loading BERT phishing detector...")
                self.models['bert'] = self._load_bert_model()
            
            # RoBERTa Threat Classifier
            if self.config.get('roberta_enabled', True):
                logger.info("Loading RoBERTa threat classifier...")
                self.models['roberta'] = self._load_roberta_model()
            
            logger.info(f"Loaded {len(self.models)} AI models")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def _load_bert_model(self):
        """Load BERT-based phishing detector"""
        model_path = self.config.get('bert_model_path', 'distilbert-base-uncased')
        
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        model.to(self.device)
        model.eval()
        
        return {
            'tokenizer': tokenizer,
            'model': model,
            'name': 'BERT Phishing Detector'
        }
    
    def _load_roberta_model(self):
        """Load RoBERTa threat classifier"""
        model_path = self.config.get('roberta_model_path', 'roberta-base')
        
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        model.to(self.device)
        model.eval()
        
        return {
            'tokenizer': tokenizer,
            'model': model,
            'name': 'RoBERTa Threat Classifier'
        }
    
    def predict_phishing(self, text: str) -> Dict:
        """
        Predict if text is phishing using BERT model
        
        Returns:
            {
                'is_phishing': bool,
                'confidence': float,
                'model': str
            }
        """
        if 'bert' not in self.models:
            return self._rule_based_phishing_detection(text)
        
        try:
            model_data = self.models['bert']
            tokenizer = model_data['tokenizer']
            model = model_data['model']
            
            # Tokenize
            inputs = tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            # Inference
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)
            
            # Get prediction
            predicted_class = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][predicted_class].item()
            
            return {
                'is_phishing': predicted_class == 1,
                'confidence': confidence,
                'model': 'bert',
                'probabilities': probabilities[0].cpu().numpy().tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in BERT prediction: {e}")
            return self._rule_based_phishing_detection(text)
    
    def _rule_based_phishing_detection(self, text: str) -> Dict:
        """Fallback rule-based phishing detection"""
        phishing_indicators = [
            'verify your account',
            'suspended account',
            'unusual activity',
            'confirm your identity',
            'click here immediately',
            'urgent action required',
            'your account will be closed',
            'verify your password',
            'update your information'
        ]
        
        text_lower = text.lower()
        matches = sum(1 for indicator in phishing_indicators if indicator in text_lower)
        
        confidence = min(matches / 3.0, 1.0)
        
        return {
            'is_phishing': matches >= 2,
            'confidence': confidence,
            'model': 'rule_based',
            'matched_indicators': matches
        }


# ============================================================================
# Threat Detectors
# ============================================================================

class PhishingDetector:
    """Advanced phishing detection"""
    
    def __init__(self, ai_model_manager: AIModelManager):
        self.ai_models = ai_model_manager
        
    def detect(self, metadata: EmailMetadata, text: str, html: str) -> Dict:
        """Detect phishing attempts"""
        indicators = []
        confidence_scores = []
        
        # AI-based detection
        combined_text = f"{metadata.subject} {text}"
        ai_result = self.ai_models.predict_phishing(combined_text)
        
        if ai_result['is_phishing']:
            indicators.append(f"AI detected phishing (confidence: {ai_result['confidence']:.2f})")
            confidence_scores.append(ai_result['confidence'])
        
        # Authentication failures
        if metadata.spf_result and metadata.spf_result.lower() in ['fail', 'softfail']:
            indicators.append("SPF authentication failed")
            confidence_scores.append(0.7)
        
        if metadata.dkim_result and metadata.dkim_result.lower() == 'fail':
            indicators.append("DKIM authentication failed")
            confidence_scores.append(0.8)
        
        # Suspicious URLs
        if metadata.url_count > 0:
            suspicious_url_count = self._check_suspicious_urls(metadata.urls)
            if suspicious_url_count > 0:
                indicators.append(f"{suspicious_url_count} suspicious URLs detected")
                confidence_scores.append(0.85)
        
        # Suspicious attachments
        if metadata.has_attachments:
            suspicious_attachments = self._check_suspicious_attachments(metadata.attachment_names)
            if suspicious_attachments:
                indicators.append(f"Suspicious attachments: {', '.join(suspicious_attachments)}")
                confidence_scores.append(0.9)
        
        # Calculate overall confidence
        if confidence_scores:
            avg_confidence = np.mean(confidence_scores)
        else:
            avg_confidence = 0.0
        
        return {
            'is_threat': len(indicators) > 0,
            'confidence': avg_confidence,
            'indicators': indicators,
            'ai_result': ai_result
        }
    
    def _check_suspicious_urls(self, urls: List[str]) -> int:
        """Check for suspicious URL patterns"""
        suspicious_count = 0
        
        suspicious_patterns = [
            r'\.tk$', r'\.ml$', r'\.ga$',  # Free TLDs
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP addresses
            r'@',  # @ in URL
            r'bit\.ly', r'tinyurl\.com',  # URL shorteners
        ]
        
        for url in urls:
            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    suspicious_count += 1
                    break
        
        return suspicious_count
    
    def _check_suspicious_attachments(self, attachments: List[str]) -> List[str]:
        """Check for suspicious attachment types"""
        suspicious_extensions = [
            '.exe', '.scr', '.bat', '.cmd', '.com', '.pif',
            '.vbs', '.js', '.jar', '.msi', '.app'
        ]
        
        suspicious = []
        for attachment in attachments:
            for ext in suspicious_extensions:
                if attachment.lower().endswith(ext):
                    suspicious.append(attachment)
                    break
        
        return suspicious


class BECDetector:
    """Business Email Compromise detection"""
    
    def __init__(self, mosint_detector=None):
        self.executive_keywords = [
            'ceo', 'cfo', 'president', 'director', 'vp', 'vice president',
            'chief', 'executive', 'chairman'
        ]
        self.mosint_detector = mosint_detector  # Optional mosint integration
        
    def detect(self, metadata: EmailMetadata, text: str) -> Dict:
        """Detect BEC attempts"""
        indicators = []
        confidence = 0.0
        
        text_lower = text.lower()
        subject_lower = metadata.subject.lower()
        
        # Check for executive impersonation
        has_exec_reference = any(
            keyword in subject_lower or keyword in text_lower
            for keyword in self.executive_keywords
        )
        
        # Urgency markers
        urgency_markers = ['urgent', 'asap', 'immediately', 'right away', 'time sensitive']
        has_urgency = any(marker in text_lower for marker in urgency_markers)
        
        # Financial requests
        financial_keywords = [
            'wire transfer', 'payment', 'invoice', 'bank account',
            'wire', 'transfer funds', 'purchase'
        ]
        has_financial = any(keyword in text_lower for keyword in financial_keywords)
        
        # Secrecy markers
        secrecy_markers = [
            'confidential', 'do not share', 'keep this between us',
            'discreet', 'private matter'
        ]
        has_secrecy = any(marker in text_lower for marker in secrecy_markers)
        
        # Calculate BEC probability
        if has_exec_reference and has_financial:
            if has_urgency or has_secrecy:
                indicators.append("Executive impersonation with financial request")
                confidence = 0.95
            else:
                indicators.append("Possible executive financial request")
                confidence = 0.70
        
        # Mosint OSINT check for related domains (if available)
        sender_email = getattr(metadata, 'from_email', getattr(metadata, 'sender', ''))
        if self.mosint_detector and self.mosint_detector.enabled and sender_email:
            try:
                mosint_result = self.mosint_detector.check_bec_indicators(sender_email)
                if mosint_result.get('detected'):
                    # Increase confidence if mosint finds related domains
                    confidence = min(confidence + mosint_result.get('score', 0.0) * 0.3, 1.0)
                    if mosint_result.get('suspicious_domains'):
                        indicators.append(f"Lookalike domains detected: {', '.join(mosint_result['suspicious_domains'][:3])}")
                    if mosint_result.get('related_domains'):
                        indicators.append(f"Related domains found: {mosint_result['domain_count']}")
            except Exception as e:
                # Silently fail - mosint is optional
                pass
        
        return {
            'is_threat': confidence > 0.6,
            'confidence': confidence,
            'indicators': indicators,
            'has_exec_reference': has_exec_reference,
            'has_financial_request': has_financial,
            'has_urgency': has_urgency
        }


class AIGeneratedDetector:
    """Detect AI-generated phishing content"""
    
    def __init__(self):
        # GPT-style patterns
        self.gpt_patterns = [
            r'I hope this (?:message|email) finds you well',
            r'I trust this (?:message|email) finds you well',
            r'Thank you for your prompt attention',
            r'Please (?:don\'t|do not) hesitate to reach out',
            r'Looking forward to your (?:response|reply)',
        ]
        
        # Formal AI patterns
        self.formal_patterns = [
            r'(?i)kindly\s+(?:proceed|verify|update|confirm)',
            r'(?i)please\s+be\s+advised',
            r'(?i)for\s+your\s+information',
        ]
        
    def detect(self, text: str) -> Dict:
        """Detect AI-generated content"""
        indicators = []
        gpt_matches = 0
        formal_matches = 0
        
        # Check GPT patterns
        for pattern in self.gpt_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                gpt_matches += 1
        
        # Check formal patterns
        for pattern in self.formal_patterns:
            if re.search(pattern, text):
                formal_matches += 1
        
        # Calculate perplexity (simplified - real version would use GPT-2)
        avg_word_length = np.mean([len(word) for word in text.split()])
        sentence_count = len(re.split(r'[.!?]+', text))
        avg_sentence_length = len(text.split()) / max(sentence_count, 1)
        
        # AI text tends to have consistent sentence length and word choice
        is_consistent = 15 < avg_sentence_length < 25 and 4 < avg_word_length < 7
        
        if gpt_matches >= 2:
            indicators.append(f"GPT-style phrases detected ({gpt_matches} matches)")
        
        if formal_matches >= 2:
            indicators.append(f"AI formal patterns detected ({formal_matches} matches)")
        
        if is_consistent and (gpt_matches > 0 or formal_matches > 0):
            indicators.append("Consistent AI writing style detected")
        
        confidence = min((gpt_matches * 0.2 + formal_matches * 0.15 + 
                         (0.3 if is_consistent else 0)), 1.0)
        
        return {
            'is_ai_generated': confidence > 0.5,
            'confidence': confidence,
            'indicators': indicators,
            'gpt_matches': gpt_matches,
            'likely_source': 'GPT' if gpt_matches > formal_matches else 'Unknown AI'
        }


# ============================================================================
# Main Email Security Plugin
# ============================================================================

class EmailSecurityPlugin:
    """
    Main email security plugin for Ilminate Agent
    """
    
    def __init__(self, config: Dict):
        """
        Initialize email security plugin
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.parser = EmailParser()
        self.ai_models = AIModelManager(config.get('ai_config', {}))
        
        # Initialize detectors
        self.phishing_detector = PhishingDetector(self.ai_models)
        self.bec_detector = BECDetector()
        self.ai_generated_detector = AIGeneratedDetector()
        
        logger.info("Email Security Plugin initialized")
    
    async def analyze_email(self, raw_email: str) -> ThreatDetection:
        """
        Analyze an email for threats
        
        Args:
            raw_email: Raw email content (RFC 822 format)
            
        Returns:
            ThreatDetection object with analysis results
        """
        try:
            # Parse email
            metadata, text_content, html_content = self.parser.parse(raw_email)
            
            logger.info(f"Analyzing email: {metadata.subject} from {metadata.sender}")
            
            # Run all detectors in parallel
            results = await asyncio.gather(
                self._run_phishing_detection(metadata, text_content, html_content),
                self._run_bec_detection(metadata, text_content),
                self._run_ai_generated_detection(text_content),
                return_exceptions=True
            )
            
            phishing_result, bec_result, ai_gen_result = results
            
            # Aggregate results
            threat_detection = self._aggregate_results(
                metadata,
                phishing_result,
                bec_result,
                ai_gen_result
            )
            
            logger.info(f"Analysis complete: {threat_detection.threat_level.name} "
                       f"(confidence: {threat_detection.confidence:.2f})")
            
            return threat_detection
            
        except Exception as e:
            logger.error(f"Error analyzing email: {e}", exc_info=True)
            raise
    
    async def _run_phishing_detection(self, metadata, text, html):
        """Run phishing detection"""
        return await asyncio.to_thread(
            self.phishing_detector.detect,
            metadata, text, html
        )
    
    async def _run_bec_detection(self, metadata, text):
        """Run BEC detection"""
        return await asyncio.to_thread(
            self.bec_detector.detect,
            metadata, text
        )
    
    async def _run_ai_generated_detection(self, text):
        """Run AI-generated content detection"""
        return await asyncio.to_thread(
            self.ai_generated_detector.detect,
            text
        )
    
    def _aggregate_results(
        self,
        metadata: EmailMetadata,
        phishing_result: Dict,
        bec_result: Dict,
        ai_gen_result: Dict
    ) -> ThreatDetection:
        """
        Aggregate results from all detectors
        """
        all_indicators = []
        threat_categories = []
        detection_methods = []
        threat_scores = []
        
        # Phishing results
        if phishing_result['is_threat']:
            threat_categories.append(ThreatCategory.PHISHING)
            all_indicators.extend(phishing_result['indicators'])
            detection_methods.append('phishing_detector')
            threat_scores.append(phishing_result['confidence'])
        
        # BEC results
        if bec_result['is_threat']:
            threat_categories.append(ThreatCategory.BEC)
            all_indicators.extend(bec_result['indicators'])
            detection_methods.append('bec_detector')
            threat_scores.append(bec_result['confidence'])
        
        # AI-generated results
        if ai_gen_result['is_ai_generated']:
            threat_categories.append(ThreatCategory.AI_GENERATED)
            all_indicators.extend(ai_gen_result['indicators'])
            detection_methods.append('ai_generated_detector')
            threat_scores.append(ai_gen_result['confidence'])
        
        # Calculate overall threat score
        if threat_scores:
            overall_threat_score = max(threat_scores)  # Use maximum threat score
            overall_confidence = np.mean(threat_scores)
        else:
            overall_threat_score = 0.0
            overall_confidence = 0.0
        
        # Determine threat level
        if overall_threat_score >= 0.9:
            threat_level = ThreatLevel.CRITICAL
        elif overall_threat_score >= 0.7:
            threat_level = ThreatLevel.HIGH
        elif overall_threat_score >= 0.5:
            threat_level = ThreatLevel.MEDIUM
        elif overall_threat_score >= 0.3:
            threat_level = ThreatLevel.LOW
        else:
            threat_level = ThreatLevel.CLEAN
        
        # Recommended action
        recommended_action = self._get_recommended_action(threat_level)
        
        # Generate explanation
        explanation = self._generate_explanation(
            threat_level,
            threat_categories,
            all_indicators
        )
        
        # Model predictions
        model_predictions = {
            'phishing': phishing_result,
            'bec': bec_result,
            'ai_generated': ai_gen_result
        }
        
        return ThreatDetection(
            threat_level=threat_level,
            threat_categories=threat_categories,
            confidence=overall_confidence,
            threat_score=overall_threat_score,
            detection_methods=detection_methods,
            model_predictions=model_predictions,
            indicators=all_indicators,
            recommended_action=recommended_action,
            explanation=explanation
        )
    
    def _get_recommended_action(self, threat_level: ThreatLevel) -> str:
        """Get recommended action based on threat level"""
        actions = {
            ThreatLevel.CRITICAL: "quarantine_and_alert",
            ThreatLevel.HIGH: "quarantine",
            ThreatLevel.MEDIUM: "warn_user",
            ThreatLevel.LOW: "tag_suspicious",
            ThreatLevel.CLEAN: "allow"
        }
        return actions.get(threat_level, "allow")
    
    def _generate_explanation(
        self,
        threat_level: ThreatLevel,
        categories: List[ThreatCategory],
        indicators: List[str]
    ) -> str:
        """Generate human-readable explanation"""
        if threat_level == ThreatLevel.CLEAN:
            return "No significant threats detected in this email."
        
        category_str = ", ".join([cat.value.replace('_', ' ').title() for cat in categories])
        indicator_str = "; ".join(indicators[:3])  # Top 3 indicators
        
        return (
            f"This email has been classified as {threat_level.name} threat. "
            f"Detected categories: {category_str}. "
            f"Key indicators: {indicator_str}."
        )
    
    def generate_report(self, detection: ThreatDetection) -> Dict:
        """
        Generate detailed report for SIEM
        
        Args:
            detection: ThreatDetection object
            
        Returns:
            Dict with formatted report
        """
        return {
            "alert_type": "email_threat_detection",
            "timestamp": detection.timestamp.isoformat(),
            "severity": detection.threat_level.name.lower(),
            "category": "email_security",
            "threat_score": detection.threat_score,
            "confidence": detection.confidence,
            "threat_categories": [cat.value for cat in detection.threat_categories],
            "detection_methods": detection.detection_methods,
            "indicators": detection.indicators,
            "recommended_action": detection.recommended_action,
            "explanation": detection.explanation,
            "model_predictions": detection.model_predictions,
            "metadata": {
                "plugin": "email_security_v2",
                "version": "2.0.0"
            }
        }


# ============================================================================
# Example Usage
# ============================================================================

async def main():
    """Example usage of Email Security Plugin"""
    
    # Configuration
    config = {
        'ai_config': {
            'bert_enabled': False,  # Set to True when models are available
            'roberta_enabled': False,
            'bert_model_path': '/etc/ilminate-agent/models/bert-email-security',
            'roberta_model_path': '/etc/ilminate-agent/models/roberta-threat'
        }
    }
    
    # Initialize plugin
    plugin = EmailSecurityPlugin(config)
    
    # Example phishing email
    sample_email = """From: security@paypa1.com
To: user@example.com
Subject: Urgent: Verify Your Account
Date: Mon, 18 Oct 2025 10:00:00 +0000
Message-ID: <12345@fake.com>

Dear Valued Customer,

I hope this message finds you well. We have detected unusual activity on your account 
and require immediate verification to prevent suspension.

Please click here to verify your account immediately: http://paypa1-verify.tk/login

This is a time-sensitive matter and your account will be closed if not verified 
within 24 hours.

Thank you for your prompt attention to this matter.

Best regards,
PayPal Security Team
"""
    
    # Analyze email
    result = await plugin.analyze_email(sample_email)
    
    # Print results
    print("\n" + "="*80)
    print("EMAIL THREAT ANALYSIS RESULT")
    print("="*80)
    print(f"Threat Level: {result.threat_level.name}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Threat Score: {result.threat_score:.2f}")
    print(f"\nCategories: {', '.join([cat.value for cat in result.threat_categories])}")
    print(f"\nIndicators:")
    for indicator in result.indicators:
        print(f"  - {indicator}")
    print(f"\nRecommended Action: {result.recommended_action}")
    print(f"\nExplanation: {result.explanation}")
    print("="*80 + "\n")
    
    # Generate SIEM report
    report = plugin.generate_report(result)
    print("SIEM Report:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())







