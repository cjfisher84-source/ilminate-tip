"""
YARA Integration for APEX Detection Engine

Wrapper for YARA pattern-based threat detection
"""

import logging
from typing import Dict, List
from pathlib import Path

# YARA library (optional)
try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False
    logging.warning("YARA Python library not available")

logger = logging.getLogger('ilminate.apex.yara')


class YARADetector:
    """YARA pattern-based detection wrapper"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.rules_path = config.get('rules_path', '/etc/ilminate-agent/deployment/ansible/files/yara')
        self.rules = self._load_rules()
        
        if YARA_AVAILABLE and self.rules:
            logger.info(f"YARA detector initialized with rules from {self.rules_path}")
        else:
            logger.warning("YARA detector running in limited mode")
    
    def _load_rules(self):
        """Load YARA rules"""
        if not YARA_AVAILABLE:
            logger.warning("YARA library not available")
            return None
        
        try:
            rules_dir = Path(self.rules_path)
            
            if not rules_dir.exists():
                logger.warning(f"YARA rules directory not found: {self.rules_path}")
                return None
            
            # Compile all .yar files
            rule_files = {}
            for rule_file in rules_dir.glob('*.yar'):
                try:
                    rule_files[rule_file.stem] = str(rule_file)
                except Exception as e:
                    logger.error(f"Error loading {rule_file}: {e}")
            
            if rule_files:
                rules = yara.compile(filepaths=rule_files)
                logger.info(f"Loaded {len(rule_files)} YARA rule files")
                return rules
            else:
                logger.warning("No YARA rule files found")
                return None
                
        except Exception as e:
            logger.error(f"Error compiling YARA rules: {e}")
            return None
    
    def scan(self, email_data) -> Dict:
        """
        Scan email with YARA rules
        
        Returns:
            {
                'matches': list of matched rules,
                'match_count': int,
                'categories': list of threat categories,
                'severity': str
            }
        """
        if not YARA_AVAILABLE or not self.rules:
            return {
                'matches': [],
                'match_count': 0,
                'categories': [],
                'severity': 'none',
                'error': 'YARA not available'
            }
        
        try:
            # Get email content
            if isinstance(email_data, str):
                content = email_data
            else:
                content = getattr(email_data, 'raw_content', '')
            
            # Scan with YARA
            matches = self.rules.match(data=content.encode('utf-8'))
            
            # Process matches
            processed_matches = []
            categories = set()
            max_severity = 'low'
            severity_order = ['low', 'medium', 'high', 'critical']
            
            for match in matches:
                # Extract metadata
                meta = match.meta
                severity = meta.get('severity', 'medium')
                category = meta.get('category', 'unknown')
                
                processed_matches.append({
                    'rule': match.rule,
                    'namespace': match.namespace,
                    'tags': match.tags,
                    'severity': severity,
                    'category': category,
                    'description': meta.get('description', ''),
                    'mitre_attack': meta.get('mitre_attack', '')
                })
                
                categories.add(category)
                
                # Update max severity
                if severity_order.index(severity) > severity_order.index(max_severity):
                    max_severity = severity
            
            return {
                'matches': processed_matches,
                'match_count': len(processed_matches),
                'categories': list(categories),
                'severity': max_severity if processed_matches else 'none'
            }
            
        except Exception as e:
            logger.error(f"YARA scan error: {e}")
            return {
                'matches': [],
                'match_count': 0,
                'categories': [],
                'severity': 'none',
                'error': str(e)
            }







