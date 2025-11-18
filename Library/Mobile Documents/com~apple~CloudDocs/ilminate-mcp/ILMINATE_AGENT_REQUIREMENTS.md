# ilminate-agent Requirements Checklist

**What ilminate-agent must provide for ilminate-mcp integration**

---

## ✅ Required Files & Structure

```
ilminate-agent/
├── plugins/
│   └── apex_detection_engine.py    ← REQUIRED
├── config/
│   └── apex-detection-engine.yml   ← Optional (uses defaults)
└── requirements.txt                 ← Required (for dependencies)
```

---

## ✅ Required Python Classes

### 1. `APEXDetectionEngine` Class

**File:** `plugins/apex_detection_engine.py`

**Required Methods:**

```python
class APEXDetectionEngine:
    def __init__(self, config: dict):
        """
        Initialize detection engine.
        
        Args:
            config: Dict with structure:
                {
                    'whitelist': list,
                    'blacklist': list,
                    'detection_layers': {
                        'yara': {'enabled': bool},
                        'deep_learning': {'enabled': bool},
                        'spamassassin': {'enabled': bool},
                        'clamav': {'enabled': bool},
                        'sublime': {'enabled': bool},
                        'feature_ml': {'enabled': bool}
                    },
                    'mosint': {'enabled': bool}
                }
        """
        pass
    
    async def analyze_email(self, email_data) -> APEXVerdict:
        """
        Analyze email for threats.
        
        Args:
            email_data: Object with attributes:
                - message_id: str
                - sender: str
                - sender_email: str
                - sender_domain: str
                - subject: str
                - body: str
                - raw_content: str
                - attachments: list
        
        Returns:
            APEXVerdict object
        """
        pass
```

**Optional Attributes:**

- `self.mosint` - Mosint instance (if enabled)
- `self.config` - Configuration dict

### 2. `APEXVerdict` Class

**File:** `plugins/apex_detection_engine.py`

**Required Attributes:**

```python
class APEXVerdict:
    def __init__(self):
        self.action: str              # "allow" | "quarantine" | "block"
        self.threat_level: str        # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
        self.risk_score: float        # 0.0 - 100.0
        self.confidence: float        # 0.0 - 1.0
        self.threat_categories: list  # ["phishing", "bec", "malware", etc.]
        self.indicators: list         # List of threat indicators
        self.layers: list             # Detection layer results
```

---

## ✅ Optional: Image Scanner

**File:** `plugins/image_scanner.py`

```python
class ImageScanner:
    def scan_image(self, image_url: str) -> dict:
        """
        Scan image for threats.
        
        Returns:
            {
                'threats_found': bool,
                'qr_codes': list,
                'logo_impersonation': bool,
                'logo_impersonation_target': str,
                'hidden_links': list,
                'threat_score': float
            }
        """
        pass
```

---

## ✅ Configuration File (Optional)

**File:** `config/apex-detection-engine.yml`

```yaml
apex_engine:
  whitelist: []
  blacklist: []
  detection_layers:
    spamassassin:
      enabled: false
    clamav:
      enabled: false
    sublime:
      enabled: false
    yara:
      enabled: true
    feature_ml:
      enabled: false
    deep_learning:
      enabled: true
  mosint:
    enabled: true
```

**Note:** If file doesn't exist, APEX Bridge uses defaults.

---

## ✅ Dependencies

**File:** `requirements.txt`

Minimum required packages:

```
pyyaml>=6.0
requests>=2.31.0
```

Common additional packages:

```
numpy>=1.24.0
scikit-learn>=1.3.0
torch>=2.0.0  # If using deep learning
# Add your specific dependencies
```

---

## ✅ Verification Checklist

Before deploying, verify:

- [ ] `plugins/apex_detection_engine.py` exists
- [ ] `APEXDetectionEngine` class is defined
- [ ] `APEXVerdict` class is defined
- [ ] `APEXDetectionEngine.__init__(config)` exists
- [ ] `APEXDetectionEngine.analyze_email(email_data)` exists (async)
- [ ] `requirements.txt` includes all dependencies
- [ ] Python import works: `from plugins.apex_detection_engine import APEXDetectionEngine, APEXVerdict`

---

## 🧪 Test Import Locally

```python
# Test script
python3 << EOF
import sys
sys.path.insert(0, '/path/to/ilminate-agent')

try:
    from plugins.apex_detection_engine import APEXDetectionEngine, APEXVerdict
    print("✅ Import successful!")
    
    # Test initialization
    config = {
        'whitelist': [],
        'blacklist': [],
        'detection_layers': {
            'yara': {'enabled': True},
            'deep_learning': {'enabled': True}
        },
        'mosint': {'enabled': True}
    }
    
    engine = APEXDetectionEngine(config)
    print("✅ Initialization successful!")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
EOF
```

---

## 📦 Deployment

Once verified, deploy to EC2:

```bash
# From ilminate-agent directory
./deploy-agent-from-repo.sh

# Or manual:
rsync -avz --exclude=.git \
  -e "ssh -i ~/.ssh/ilminate-mcp-key.pem" \
  ./ ec2-user@54.237.174.195:/opt/ilminate-agent/

ssh -i ~/.ssh/ilminate-mcp-key.pem ec2-user@54.237.174.195 \
  'cd /opt/ilminate-agent && pip3 install -r requirements.txt && pm2 restart apex-bridge'
```

---

## ✅ Summary

**Minimum Requirements:**

1. ✅ `plugins/apex_detection_engine.py` with `APEXDetectionEngine` and `APEXVerdict`
2. ✅ `APEXDetectionEngine.__init__(config)` method
3. ✅ `APEXDetectionEngine.analyze_email(email_data)` async method
4. ✅ `requirements.txt` with dependencies

**That's it!** The APEX Bridge will handle the rest. 🚀

