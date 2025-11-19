#!/usr/bin/env python3
"""
APEX Detection Engine Bridge for MCP Server
Provides HTTP API to access ilminate-agent detection engines
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)
except ImportError:
    # dotenv not installed, use environment variables only
    pass

# Add ilminate-agent to path
ilminate_agent_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    '..', 'ilminate-agent'
)
sys.path.insert(0, ilminate_agent_path)

# Import APEX detection engine
try:
    from plugins.apex_detection_engine import APEXDetectionEngine, APEXVerdict
    APEX_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import APEX detection engine: {e}")
    APEX_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[APEX-Bridge] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('apex_bridge')

app = Flask(__name__)
CORS(app)

# API Key authentication
API_KEY = os.environ.get('APEX_BRIDGE_API_KEY', '')
REQUIRE_AUTH = os.environ.get('APEX_BRIDGE_REQUIRE_AUTH', 'false').lower() == 'true'

# Global APEX engine instance
apex_engine: Optional[APEXDetectionEngine] = None


def require_api_key(f):
    """Decorator to require API key authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if REQUIRE_AUTH:
            if not API_KEY:
                logger.warning("API key required but not configured")
                return jsonify({'error': 'API key not configured'}), 500
            
            # Check for API key in headers
            provided_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
            
            if not provided_key or provided_key != API_KEY:
                logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
                return jsonify({'error': 'Unauthorized - Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def load_config() -> Dict:
    """Load APEX configuration"""
    config_path = os.path.join(
        ilminate_agent_path,
        'config',
        'apex-detection-engine.yml'
    )
    
    # Default config if file doesn't exist
    default_config = {
        'whitelist': [],
        'blacklist': [],
        'detection_layers': {
            'spamassassin': {'enabled': False},
            'clamav': {'enabled': False},
            'sublime': {'enabled': False},
            'yara': {'enabled': True},
            'feature_ml': {'enabled': False},
            'deep_learning': {'enabled': True}
        },
        'mosint': {'enabled': True}
    }
    
    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('apex_engine', default_config)
        except Exception as e:
            logger.warning(f"Could not load config file: {e}")
    
    return default_config


def initialize_apex():
    """Initialize APEX detection engine"""
    global apex_engine
    
    if not APEX_AVAILABLE:
        logger.error("APEX detection engine not available")
        return False
    
    try:
        config = load_config()
        apex_engine = APEXDetectionEngine(config)
        logger.info("✅ APEX Detection Engine initialized")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize APEX: {e}")
        return False


@app.route('/health', methods=['GET'])
@require_api_key
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy' if apex_engine else 'unavailable',
        'apex_available': APEX_AVAILABLE,
        'apex_initialized': apex_engine is not None
    })


@app.route('/api/analyze-email', methods=['POST'])
@require_api_key
def analyze_email():
    """Analyze email for threats"""
    if not apex_engine:
        return jsonify({
            'error': 'APEX engine not initialized'
        }), 503
    
    try:
        data = request.get_json()
        
        # Create email object from request
        class EmailData:
            def __init__(self, data: Dict):
                self.message_id = data.get('message_id', f"msg-{datetime.now().timestamp()}")
                self.sender = data.get('sender', '')
                self.sender_email = data.get('sender', '')
                self.sender_domain = data.get('sender', '').split('@')[-1] if '@' in data.get('sender', '') else ''
                self.subject = data.get('subject', '')
                self.body = data.get('body', '')
                self.raw_content = data.get('raw_content', '')
                self.attachments = data.get('attachments', [])
        
        email_data = EmailData(data)
        
        # Run APEX analysis
        # Note: Flask doesn't support async routes, so we use asyncio.run for async calls
        import asyncio
        verdict: APEXVerdict = asyncio.run(apex_engine.analyze_email(email_data))
        
        # Convert to JSON-serializable format
        result = verdict.to_dict()
        
        return jsonify({
            'success': True,
            'verdict': result
        })
        
    except Exception as e:
        logger.error(f"Error analyzing email: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/map-mitre', methods=['POST'])
@require_api_key
def map_mitre():
    """Map security event to MITRE ATT&CK"""
    if not apex_engine:
        return jsonify({
            'error': 'APEX engine not initialized'
        }), 503
    
    try:
        data = request.get_json()
        event_text = data.get('event_text', '')
        
        # Create a simple email object for analysis
        class EmailData:
            def __init__(self, text: str):
                self.message_id = f"mitre-{datetime.now().timestamp()}"
                self.sender = 'unknown@unknown.com'
                self.sender_email = 'unknown@unknown.com'
                self.sender_domain = 'unknown.com'
                self.subject = ''
                self.body = text
                self.raw_content = text
        
        email_data = EmailData(event_text)
        
        # Run analysis to get MITRE mapping
        import asyncio
        verdict: APEXVerdict = asyncio.run(apex_engine.analyze_email(email_data))
        
        # Extract MITRE techniques from verdict
        techniques = []
        for layer in verdict.layers:
            if layer.detected:
                # Extract technique information from findings
                findings = layer.findings
                if isinstance(findings, dict):
                    # Look for MITRE technique IDs in findings
                    if 'mitre_techniques' in findings:
                        techniques.extend(findings['mitre_techniques'])
                    elif 'techniques' in findings:
                        techniques.extend(findings['techniques'])
        
        # If no techniques found, infer from threat categories
        if not techniques:
            for category in verdict.threat_categories:
                if 'phish' in category.lower():
                    techniques.append({
                        'id': 'T1566.001',
                        'name': 'Phishing: Spearphishing Attachment',
                        'confidence': 0.7
                    })
                elif 'bec' in category.lower():
                    techniques.append({
                        'id': 'T1566.003',
                        'name': 'Phishing: Spearphishing via Service',
                        'confidence': 0.8
                    })
        
        return jsonify({
            'success': True,
            'techniques': techniques,
            'primary_technique': techniques[0] if techniques else None
        })
        
    except Exception as e:
        logger.error(f"Error mapping MITRE: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/check-domain', methods=['POST'])
@require_api_key
def check_domain():
    """Check domain reputation"""
    if not apex_engine:
        return jsonify({
            'error': 'APEX engine not initialized'
        }), 503
    
    try:
        data = request.get_json()
        domain = data.get('domain', '')
        
        # Use Mosint if available for domain reputation
        if apex_engine.mosint and apex_engine.mosint.enabled:
            try:
                # Create a test email with the domain
                class EmailData:
                    def __init__(self, domain: str):
                        self.message_id = f"domain-{datetime.now().timestamp()}"
                        self.sender = f"test@{domain}"
                        self.sender_email = f"test@{domain}"
                        self.sender_domain = domain
                        self.subject = ''
                        self.body = ''
                        self.raw_content = ''
                
                email_data = EmailData(domain)
                
                # Get reputation from Mosint
                rep_result = apex_engine.mosint.get_reputation(email_data.sender_email)
                
                return jsonify({
                    'success': True,
                    'reputation_score': rep_result.get('score', 0.5),
                    'is_malicious': rep_result.get('score', 0.5) < 0.3,
                    'threat_types': rep_result.get('threat_types', []),
                    'first_seen': rep_result.get('first_seen'),
                    'last_seen': rep_result.get('last_seen')
                })
            except Exception as e:
                logger.warning(f"Mosint domain check failed: {e}")
        
        # Fallback: basic domain analysis
        return jsonify({
            'success': True,
            'reputation_score': 0.5,
            'is_malicious': False,
            'threat_types': [],
            'note': 'Basic analysis - Mosint not available'
        })
        
    except Exception as e:
        logger.error(f"Error checking domain: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/scan-image', methods=['POST'])
@require_api_key
def scan_image():
    """Scan image for threats (QR codes, logo impersonation)"""
    if not apex_engine:
        return jsonify({
            'error': 'APEX engine not initialized'
        }), 503
    
    try:
        data = request.get_json()
        image_url = data.get('image_url', '')
        
        # Check if image scanner plugin is available
        try:
            from plugins.image_scanner import ImageScanner
            scanner = ImageScanner({})
            
            # Download and scan image
            result = asyncio.run(scanner.scan_image_url(image_url))
            
            return jsonify({
                'success': True,
                'threats_found': result.get('threats_found', False),
                'qr_codes': result.get('qr_codes', []),
                'logo_impersonation': result.get('logo_impersonation', False),
                'logo_impersonation_target': result.get('logo_target'),
                'hidden_links': result.get('hidden_links', []),
                'threat_score': result.get('threat_score', 0.0)
            })
        except ImportError:
            logger.warning("Image scanner not available")
            return jsonify({
                'success': False,
                'error': 'Image scanner not available'
            }), 503
        
    except Exception as e:
        logger.error(f"Error scanning image: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/status', methods=['GET'])
@require_api_key
def get_status():
    """Get APEX engine status"""
    if not apex_engine:
        return jsonify({
            'available': False,
            'error': 'APEX engine not initialized'
        })
    
    try:
        stats = apex_engine.get_statistics()
        return jsonify({
            'available': True,
            'statistics': stats,
            'active_layers': stats.get('active_layers', [])
        })
    except Exception as e:
        return jsonify({
            'available': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Initialize APEX on startup
    if initialize_apex():
        port = int(os.environ.get('APEX_BRIDGE_PORT', 8888))
        logger.info(f"🚀 APEX Bridge starting on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        logger.error("Failed to initialize APEX. Exiting.")
        sys.exit(1)

