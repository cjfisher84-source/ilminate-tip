"""
Sublime Security Integration for APEX Detection Engine

Wrapper for Sublime Security email threat detection rules
Note: This is a simplified implementation. Full Sublime integration
      requires their platform/API.
"""

import logging
import yaml
import re
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger('ilminate.apex.sublime')


class SublimeSecurityDetector:
    """
    Sublime Security detection wrapper
    
    Implements basic Sublime-style detection rules (MQL-like)
    For production, integrate with actual Sublime platform
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.rules_path = config.get('rules_path', '/etc/ilminate-apex/sublime-rules')
        self.rules = self._load_rules()
        
        logger.info(f"Loaded {len(self.rules)} Sublime-style rules")
    
    def _load_rules(self) -> List[Dict]:
        """Load detection rules"""
        rules = []
        
        # Built-in rules (Sublime-style)
        rules.extend([
            {
                'id': 'BEC_WIRE_TRANSFER',
                'name': 'BEC Wire Transfer Request',
                'severity': 'critical',
                'description': 'Detects wire transfer requests from executives',
                'conditions': {
                    'subject_patterns': [
                        r'(?i)(wire|bank|urgent|transfer)',
                    ],
                    'body_patterns': [
                        r'(?i)(wire transfer|bank account|send.*money)',
                        r'(?i)(ceo|president|director|executive)',
                        r'(?i)(urgent|asap|immediately|confidential)'
                    ],
                    'min_matches': 3
                },
                'tags': ['bec', 'financial']
            },
            {
                'id': 'CREDENTIAL_HARVEST',
                'name': 'Credential Harvesting Attempt',
                'severity': 'high',
                'description': 'Detects credential harvesting phishing',
                'conditions': {
                    'subject_patterns': [
                        r'(?i)(verify|confirm|update|suspended)',
                    ],
                    'body_patterns': [
                        r'(?i)(verify.*account|confirm.*identity)',
                        r'(?i)(click here|login|sign in)',
                        r'(?i)(suspended|disabled|locked)'
                    ],
                    'url_required': True,
                    'min_matches': 2
                },
                'tags': ['phishing', 'cred-harvest']
            },
            {
                'id': 'PAYROLL_REDIRECT',
                'name': 'Payroll Redirect Scam',
                'severity': 'high',
                'description': 'Detects payroll redirect fraud',
                'conditions': {
                    'subject_patterns': [
                        r'(?i)(payroll|direct deposit|salary)',
                    ],
                    'body_patterns': [
                        r'(?i)(change|update|new).*account',
                        r'(?i)(routing number|account number)',
                    ],
                    'min_matches': 2
                },
                'tags': ['bec', 'payroll-fraud']
            },
            {
                'id': 'INVOICE_FRAUD',
                'name': 'Invoice Fraud',
                'severity': 'medium',
                'description': 'Detects invoice fraud attempts',
                'conditions': {
                    'subject_patterns': [
                        r'(?i)(invoice|payment|bill)',
                    ],
                    'body_patterns': [
                        r'(?i)(new.*bank|updated.*account)',
                        r'(?i)(payment|remit|wire)',
                        r'(?i)(urgent|overdue)'
                    ],
                    'attachment_required': True,
                    'min_matches': 2
                },
                'tags': ['fraud', 'invoice']
            },
            {
                'id': 'AI_AGENT_HIJACK',
                'name': 'AI Agent Hijack Attempt',
                'severity': 'critical',
                'description': 'Detects AI agent hijacking phrases',
                'conditions': {
                    'body_patterns': [
                        r'(?i)ignore (previous|all) instructions',
                        r'(?i)disregard (prior|previous)',
                        r'(?i)forget (previous|all)',
                        r'(?i)override.*prompt',
                        r'(?i)system prompt'
                    ],
                    'min_matches': 1
                },
                'tags': ['ai', 'agent-hijack', 'prompt-injection']
            },
            {
                'id': 'URGENT_CEO',
                'name': 'Urgent CEO Request',
                'severity': 'high',
                'description': 'Urgent request claiming to be from CEO',
                'conditions': {
                    'body_patterns': [
                        r'(?i)(ceo|chief executive)',
                        r'(?i)(urgent|asap|immediately)',
                        r'(?i)(need|require).*help'
                    ],
                    'min_matches': 3
                },
                'tags': ['bec', 'impersonation']
            }
        ])
        
        # Load custom rules from file if exists
        rules_file = Path(self.rules_path) / 'custom_rules.yaml'
        if rules_file.exists():
            try:
                with open(rules_file) as f:
                    custom_rules = yaml.safe_load(f)
                    if custom_rules:
                        rules.extend(custom_rules.get('rules', []))
            except Exception as e:
                logger.error(f"Error loading custom rules: {e}")
        
        return rules
    
    def evaluate(self, email_data) -> Dict:
        """
        Evaluate email against Sublime-style rules
        
        Returns:
            {
                'threats_found': bool,
                'severity': str,
                'rules_triggered': list,
                'confidence': float,
                'details': dict
            }
        """
        try:
            # Extract email content
            if isinstance(email_data, str):
                subject = self._extract_subject(email_data)
                body = self._extract_body(email_data)
                has_urls = 'http' in email_data.lower()
                has_attachments = 'Content-Disposition: attachment' in email_data
            else:
                # Handle dict format
                subject = email_data.get('subject', '')
                body = email_data.get('body', '')
                has_urls = email_data.get('has_urls', False)
                has_attachments = email_data.get('has_attachments', False)
            
            # Evaluate rules
            triggered_rules = []
            max_severity = 'low'
            severity_order = ['low', 'medium', 'high', 'critical']
            
            for rule in self.rules:
                if self._evaluate_rule(rule, subject, body, has_urls, has_attachments):
                    triggered_rules.append({
                        'id': rule['id'],
                        'name': rule['name'],
                        'severity': rule['severity'],
                        'tags': rule.get('tags', [])
                    })
                    
                    # Update max severity
                    if severity_order.index(rule['severity']) > severity_order.index(max_severity):
                        max_severity = rule['severity']
            
            # Calculate confidence
            if triggered_rules:
                # More rules = higher confidence
                confidence = min(0.5 + (len(triggered_rules) * 0.15), 0.95)
            else:
                confidence = 0.3
            
            return {
                'threats_found': len(triggered_rules) > 0,
                'severity': max_severity if triggered_rules else 'none',
                'rules_triggered': [r['id'] for r in triggered_rules],
                'confidence': confidence,
                'details': {
                    'triggered_rules': triggered_rules,
                    'total_rules_evaluated': len(self.rules)
                }
            }
            
        except Exception as e:
            logger.error(f"Sublime evaluation error: {e}")
            return {
                'threats_found': False,
                'severity': 'none',
                'rules_triggered': [],
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _evaluate_rule(
        self,
        rule: Dict,
        subject: str,
        body: str,
        has_urls: bool,
        has_attachments: bool
    ) -> bool:
        """Evaluate a single rule against email"""
        conditions = rule.get('conditions', {})
        
        matches = 0
        min_matches = conditions.get('min_matches', 1)
        
        # Check subject patterns
        subject_patterns = conditions.get('subject_patterns', [])
        for pattern in subject_patterns:
            if re.search(pattern, subject):
                matches += 1
        
        # Check body patterns
        body_patterns = conditions.get('body_patterns', [])
        for pattern in body_patterns:
            if re.search(pattern, body):
                matches += 1
        
        # Check URL requirement
        if conditions.get('url_required') and not has_urls:
            return False
        
        # Check attachment requirement
        if conditions.get('attachment_required') and not has_attachments:
            return False
        
        return matches >= min_matches
    
    def _extract_subject(self, email: str) -> str:
        """Extract subject from raw email"""
        match = re.search(r'^Subject: (.*)$', email, re.MULTILINE | re.IGNORECASE)
        return match.group(1) if match else ''
    
    def _extract_body(self, email: str) -> str:
        """Extract body from raw email"""
        # Simple extraction - split on double newline
        parts = email.split('\n\n', 1)
        return parts[1] if len(parts) > 1 else ''





