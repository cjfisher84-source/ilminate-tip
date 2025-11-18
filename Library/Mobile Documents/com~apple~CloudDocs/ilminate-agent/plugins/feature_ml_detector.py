"""
Feature-Based ML Detector for APEX Detection Engine

Implements OpenAI's curated feature approach with GBDT
Fast, explainable email threat detection using engineered features
"""

import logging
import hashlib
import re
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np

# ML libraries (optional - graceful degradation)
try:
    import joblib
    from sklearn.ensemble import HistGradientBoostingClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available. Using rule-based fallback.")

logger = logging.getLogger('ilminate.apex.feature_ml')


class FeatureMLDetector:
    """
    Feature-based ML detector using GBDT
    
    Based on OpenAI's approach with curated features:
    - Authentication features (SPF, DKIM, DMARC)
    - Infrastructure features (domain age, ASN reputation)
    - Content features (intent, urgency, personalization)
    - Behavioral features (sender novelty, blast radius)
    - Template features (clustering, similarity)
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.model_path = config.get('model_path', '/etc/ilminate-apex/models/gbdt_model.joblib')
        self.confidence_threshold = config.get('confidence_threshold', 0.75)
        
        # Load model if available
        self.model = self._load_model()
        
        # Feature extractors
        self.domain_cache = {}
        
        logger.info("Feature-based ML detector initialized")
    
    def _load_model(self):
        """Load trained GBDT model"""
        if not SKLEARN_AVAILABLE:
            logger.warning("Sklearn not available, using rule-based detection")
            return None
        
        try:
            import os
            if os.path.exists(self.model_path):
                model = joblib.load(self.model_path)
                logger.info(f"Loaded GBDT model from {self.model_path}")
                return model
            else:
                logger.warning(f"Model file not found: {self.model_path}")
                logger.info("Using rule-based fallback detection")
                return None
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
    
    def predict(self, email_data) -> Dict:
        """
        Predict email threat using feature-based ML
        
        Returns:
            {
                'is_threat': bool,
                'risk_score': float (0-1),
                'confidence': float (0-1),
                'threat_types': list,
                'top_features': list,
                'features': dict
            }
        """
        try:
            # Extract features
            features = self.extract_features(email_data)
            
            # Predict with model or fallback to rules
            if self.model:
                prediction = self._predict_with_model(features)
            else:
                prediction = self._predict_with_rules(features)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Feature ML prediction error: {e}")
            return {
                'is_threat': False,
                'risk_score': 0.0,
                'confidence': 0.0,
                'threat_types': [],
                'top_features': [],
                'error': str(e)
            }
    
    def extract_features(self, email_data) -> Dict:
        """
        Extract curated features from email
        
        Feature categories:
        - Authentication (SPF, DKIM, DMARC)
        - Infrastructure (domain age, reputation)
        - Content (intent, urgency, requests)
        - Behavioral (sender patterns)
        - Template (similarity analysis)
        """
        if isinstance(email_data, str):
            # Parse raw email
            sender = self._extract_sender(email_data)
            sender_domain = sender.split('@')[-1] if '@' in sender else ''
            subject = self._extract_subject(email_data)
            body = self._extract_body(email_data)
            urls = re.findall(r'http[s]?://[^\s<>"]+', email_data)
            
            # Simple attachment detection
            has_attachments = 'Content-Disposition: attachment' in email_data
            attachment_count = email_data.count('Content-Disposition: attachment')
            
        else:
            # Use structured email object
            sender = getattr(email_data, 'sender', '')
            sender_domain = getattr(email_data, 'sender_domain', '')
            subject = getattr(email_data, 'subject', '')
            body = getattr(email_data, 'text_content', '')
            urls = getattr(email_data, 'urls', [])
            has_attachments = getattr(email_data, 'has_attachments', False)
            attachment_count = getattr(email_data, 'attachment_count', 0)
        
        # Extract features
        features = {
            # Authentication features
            'auth_spf': self._check_spf(email_data),
            'auth_dkim': self._check_dkim(email_data),
            'auth_dmarc': self._check_dmarc(email_data),
            
            # Infrastructure features
            'domain_age_days': self._get_domain_age(sender_domain),
            'from_display_mismatch': self._check_display_name_mismatch(email_data),
            'envelope_from_mismatch': self._check_envelope_mismatch(email_data),
            'asn_reputation_score': 50.0,  # Placeholder - integrate with reputation service
            
            # Content features
            'url_count': len(urls),
            'attachment_count': attachment_count,
            'content_intent': self._classify_intent(subject, body),
            'pressure_terms': self._count_urgency_terms(body),
            'money_request': self._detect_money_request(body),
            'credential_request': self._detect_credential_request(body),
            'agent_hijack_phrase': self._detect_agent_hijack(body),
            'personalization_score': self._calculate_personalization(body),
            
            # Behavioral features
            'org_graph_sender_novelty': 0.5,  # Placeholder - needs historical data
            'org_graph_blast_radius': 1,      # Placeholder - needs recipient tracking
            
            # Template features
            'template_similarity_max': 0.0,   # Placeholder - needs template database
        }
        
        return features
    
    def _predict_with_model(self, features: Dict) -> Dict:
        """Predict using trained GBDT model"""
        # Convert features to array (in correct order)
        feature_vector = self._features_to_vector(features)
        
        # Predict
        proba = self.model.predict_proba([feature_vector])[0]
        
        # Assuming binary classification: 0=benign, 1=threat
        threat_prob = proba[1] if len(proba) > 1 else proba[0]
        
        # Get feature importances for explanation
        top_features = self._get_top_features(features)
        
        # Classify threat types based on features
        threat_types = self._classify_threat_types(features)
        
        return {
            'is_threat': threat_prob > self.confidence_threshold,
            'risk_score': float(threat_prob),
            'confidence': max(proba),
            'threat_types': threat_types,
            'top_features': top_features,
            'features': features
        }
    
    def _predict_with_rules(self, features: Dict) -> Dict:
        """Fallback rule-based prediction"""
        risk_score = 0.0
        threat_types = []
        indicators = []
        
        # Auth failures
        if features['auth_dmarc'] == 'fail':
            risk_score += 0.35
            indicators.append('dmarc_fail')
        
        if features['auth_spf'] in ['fail', 'softfail']:
            risk_score += 0.20
            indicators.append('spf_fail')
        
        # New domain
        if features['domain_age_days'] < 14:
            risk_score += 0.15
            indicators.append('new_domain')
        
        # Display name mismatch
        if features['from_display_mismatch']:
            risk_score += 0.10
            indicators.append('display_mismatch')
        
        # Credential request
        if features['credential_request']:
            risk_score += 0.25
            threat_types.append('credential_harvesting')
            indicators.append('cred_request')
        
        # Money request
        if features['money_request']:
            risk_score += 0.25
            threat_types.append('bec')
            indicators.append('money_request')
        
        # Agent hijack
        if features['agent_hijack_phrase']:
            risk_score += 0.30
            threat_types.append('prompt_injection')
            indicators.append('agent_hijack')
        
        # Urgency + low personalization
        if features['pressure_terms'] >= 3 and features['personalization_score'] < 0.3:
            risk_score += 0.15
            threat_types.append('phishing')
            indicators.append('urgent_impersonal')
        
        # Cap at 1.0
        risk_score = min(risk_score, 1.0)
        
        return {
            'is_threat': risk_score > self.confidence_threshold,
            'risk_score': risk_score,
            'confidence': 0.7 if risk_score > 0.5 else 0.5,
            'threat_types': threat_types if threat_types else ['unknown'],
            'top_features': indicators,
            'features': features
        }
    
    # Feature extraction helpers
    
    def _check_spf(self, email_data) -> str:
        """Check SPF result"""
        if hasattr(email_data, 'spf_result'):
            return email_data.spf_result or 'none'
        # Parse from headers if raw email
        return 'none'
    
    def _check_dkim(self, email_data) -> str:
        """Check DKIM result"""
        if hasattr(email_data, 'dkim_result'):
            return email_data.dkim_result or 'none'
        return 'none'
    
    def _check_dmarc(self, email_data) -> str:
        """Check DMARC result"""
        if hasattr(email_data, 'dmarc_result'):
            return email_data.dmarc_result or 'none'
        return 'none'
    
    def _get_domain_age(self, domain: str) -> int:
        """Get domain age in days (placeholder - integrate with WHOIS)"""
        # Placeholder - in production, query WHOIS or domain reputation service
        return 365  # Assume 1 year for now
    
    def _check_display_name_mismatch(self, email_data) -> bool:
        """Check if display name doesn't match sender domain"""
        # Placeholder - needs full email parsing
        return False
    
    def _check_envelope_mismatch(self, email_data) -> bool:
        """Check if envelope-from doesn't match from header"""
        # Placeholder
        return False
    
    def _classify_intent(self, subject: str, body: str) -> str:
        """Classify email intent"""
        text = (subject + ' ' + body).lower()
        
        if any(w in text for w in ['invoice', 'payment', 'bill']):
            return 'invoice'
        if any(w in text for w in ['ceo', 'president', 'executive', 'wire transfer']):
            return 'bec'
        if any(w in text for w in ['hr', 'payroll', 'employee']):
            return 'hr'
        if any(w in text for w in ['bitcoin', 'crypto', 'wallet']):
            return 'crypto'
        if any(w in text for w in ['legal', 'lawsuit', 'court']):
            return 'legal'
        
        return 'generic'
    
    def _count_urgency_terms(self, text: str) -> int:
        """Count urgency/pressure terms"""
        urgency_terms = [
            'urgent', 'asap', 'immediately', 'emergency', 'critical',
            'expires', 'deadline', 'final notice', 'last chance',
            'act now', 'time sensitive', 'immediate action'
        ]
        
        text_lower = text.lower()
        return sum(1 for term in urgency_terms if term in text_lower)
    
    def _detect_money_request(self, text: str) -> bool:
        """Detect money/financial requests"""
        money_patterns = [
            r'(?i)(wire transfer|bank account|send.*money)',
            r'(?i)(payment|invoice|bill).*urgent',
            r'(?i)\$\d+[,\d]*'
        ]
        
        return any(re.search(pattern, text) for pattern in money_patterns)
    
    def _detect_credential_request(self, text: str) -> bool:
        """Detect credential harvesting attempts"""
        cred_patterns = [
            r'(?i)verify.*(account|identity|password)',
            r'(?i)confirm.*(credentials|login|password)',
            r'(?i)update.*(password|account)',
            r'(?i)(click here|sign in).*account'
        ]
        
        return any(re.search(pattern, text) for pattern in cred_patterns)
    
    def _detect_agent_hijack(self, text: str) -> bool:
        """Detect AI agent hijacking phrases"""
        hijack_patterns = [
            r'(?i)ignore (previous|all) instructions',
            r'(?i)disregard (prior|previous)',
            r'(?i)forget (previous|all)',
            r'(?i)override',
            r'(?i)system prompt'
        ]
        
        return any(re.search(pattern, text) for pattern in hijack_patterns)
    
    def _calculate_personalization(self, text: str) -> float:
        """Calculate personalization score (0-1)"""
        # Simple heuristic - real implementation would be more sophisticated
        personal_markers = [
            r'\b(dear|hello|hi)\s+[A-Z][a-z]+',  # Named greeting
            r'\b(your|you)\b',  # Personal pronouns
            r'\b(thank you|thanks)\b'
        ]
        
        score = sum(0.2 for pattern in personal_markers if re.search(pattern, text, re.IGNORECASE))
        return min(score, 1.0)
    
    def _features_to_vector(self, features: Dict) -> np.ndarray:
        """Convert feature dict to numpy array in correct order"""
        # Categorical encoding (simplified - real implementation uses OneHotEncoder)
        auth_map = {'pass': 0, 'fail': 1, 'softfail': 0.5, 'none': 0.3}
        intent_map = {'bec': 0, 'invoice': 1, 'hr': 2, 'crypto': 3, 'legal': 4, 'generic': 5}
        
        vector = [
            auth_map.get(features['auth_spf'], 0.3),
            auth_map.get(features['auth_dkim'], 0.3),
            auth_map.get(features['auth_dmarc'], 0.3),
            features['domain_age_days'],
            int(features['from_display_mismatch']),
            int(features['envelope_from_mismatch']),
            features['asn_reputation_score'],
            features['url_count'],
            features['attachment_count'],
            intent_map.get(features['content_intent'], 5),
            features['pressure_terms'],
            int(features['money_request']),
            int(features['credential_request']),
            int(features['agent_hijack_phrase']),
            features['personalization_score'],
            features['org_graph_sender_novelty'],
            features['org_graph_blast_radius'],
            features['template_similarity_max']
        ]
        
        return np.array(vector)
    
    def _get_top_features(self, features: Dict) -> List[str]:
        """Get top contributing features"""
        # Simplified - in production, use SHAP or feature importances
        top = []
        
        if features['agent_hijack_phrase']:
            top.append('agent_hijack_phrase')
        if features['auth_dmarc'] == 'fail':
            top.append('auth_dmarc')
        if features['domain_age_days'] < 30:
            top.append('domain_age_days')
        if features['credential_request']:
            top.append('credential_request')
        if features['money_request']:
            top.append('money_request')
        
        return top[:5]
    
    def _classify_threat_types(self, features: Dict) -> List[str]:
        """Classify threat types based on features"""
        types = []
        
        if features['money_request']:
            types.append('bec')
        if features['credential_request']:
            types.append('credential_harvesting')
        if features['agent_hijack_phrase']:
            types.append('prompt_injection')
        if features['content_intent'] == 'invoice':
            types.append('invoice_fraud')
        if features['pressure_terms'] >= 3:
            types.append('phishing')
        
        return types if types else ['unknown']
    
    # Email parsing helpers
    
    def _extract_sender(self, email: str) -> str:
        """Extract sender from raw email"""
        match = re.search(r'^From: .*<(.+?)>', email, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1)
        match = re.search(r'^From: (.+)$', email, re.MULTILINE | re.IGNORECASE)
        return match.group(1).strip() if match else ''
    
    def _extract_subject(self, email: str) -> str:
        """Extract subject from raw email"""
        match = re.search(r'^Subject: (.*)$', email, re.MULTILINE | re.IGNORECASE)
        return match.group(1) if match else ''
    
    def _extract_body(self, email: str) -> str:
        """Extract body from raw email"""
        parts = email.split('\n\n', 1)
        return parts[1] if len(parts) > 1 else ''







