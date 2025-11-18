# How ilminate-mcp Works with ilminate-agent

**Complete guide to the integration architecture**

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    External AI Assistants                    │
│              (Claude Desktop, Custom AI Apps)                 │
└──────────────────────┬───────────────────────────────────────┘
                       │ MCP Protocol (JSON-RPC)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ilminate-mcp Server (Node.js)                   │
│  • MCP Protocol Handler                                     │
│  • Tool Registry                                            │
│  • Request Router                                           │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP (REST API)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            APEX Bridge Service (Python Flask)                │
│  • HTTP API Wrapper                                         │
│  • Converts HTTP → Python calls                             │
│  • Error handling & logging                                 │
└──────────────────────┬───────────────────────────────────────┘
                       │ Python Import
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ilminate-agent (Python)                        │
│  • APEX Detection Engine                                    │
│  • Detection plugins                                         │
│  • ML/AI models                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 How It Works

### 1. **MCP Server (Node.js)**
- Receives MCP protocol requests from AI assistants
- Routes requests to appropriate tools
- Calls APEX Bridge via HTTP

### 2. **APEX Bridge (Python Flask)**
- Provides HTTP REST API endpoints
- Imports and uses ilminate-agent modules
- Handles async operations
- Returns JSON responses

### 3. **ilminate-agent (Python)**
- Contains the actual detection logic
- APEX Detection Engine class
- Detection plugins and models

---

## 📋 What ilminate-agent Must Provide

### Required Structure

```
/opt/ilminate-agent/
├── plugins/
│   ├── apex_detection_engine.py    ← REQUIRED
│   └── image_scanner.py             ← Optional (for image scanning)
├── config/
│   └── apex-detection-engine.yml   ← Optional (uses defaults if missing)
└── requirements.txt                 ← For Python dependencies
```

### Required Classes

#### 1. `APEXDetectionEngine` Class

**Location:** `plugins/apex_detection_engine.py`

**Must have:**

```python
class APEXDetectionEngine:
    def __init__(self, config: dict):
        """
        Initialize with configuration dict.
        Config structure:
        {
            'whitelist': [],
            'blacklist': [],
            'detection_layers': {
                'yara': {'enabled': True},
                'deep_learning': {'enabled': True},
                ...
            },
            'mosint': {'enabled': True}
        }
        """
        self.config = config
        # Initialize detection layers
        # Initialize Mosint if enabled
        # etc.
    
    async def analyze_email(self, email_data) -> APEXVerdict:
        """
        Analyze email for threats.
        
        Args:
            email_data: Object with:
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
        # Detection logic here
        pass
```

#### 2. `APEXVerdict` Class

**Location:** `plugins/apex_detection_engine.py`

**Must have:**

```python
class APEXVerdict:
    def __init__(self):
        self.action: str              # "allow", "quarantine", "block"
        self.threat_level: str         # "LOW", "MEDIUM", "HIGH", "CRITICAL"
        self.risk_score: float          # 0.0 - 100.0
        self.confidence: float          # 0.0 - 1.0
        self.threat_categories: list    # ["phishing", "bec", etc.]
        self.indicators: list           # List of threat indicators
        self.layers: list              # Detection layer results
```

#### 3. Optional: `ImageScanner` Class

**Location:** `plugins/image_scanner.py`

**For image scanning features:**

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

## 🔌 How APEX Bridge Uses ilminate-agent

### Import Process

```python
# 1. Add ilminate-agent to Python path
ilminate_agent_path = "/opt/ilminate-agent"
sys.path.insert(0, ilminate_agent_path)

# 2. Import required classes
from plugins.apex_detection_engine import APEXDetectionEngine, APEXVerdict

# 3. Initialize engine
config = load_config()  # From YAML or defaults
apex_engine = APEXDetectionEngine(config)

# 4. Use engine
verdict = await apex_engine.analyze_email(email_data)
```

### API Endpoints → ilminate-agent Calls

| Bridge Endpoint | ilminate-agent Method | Purpose |
|----------------|----------------------|---------|
| `POST /api/analyze-email` | `apex_engine.analyze_email()` | Analyze email threats |
| `POST /api/check-domain` | `apex_engine.mosint.get_reputation()` | Domain reputation |
| `POST /api/scan-image` | `ImageScanner.scan_image()` | Scan images for threats |
| `POST /api/map-mitre` | Uses verdict data | Map to MITRE ATT&CK |

---

## ✅ What Needs to Happen on ilminate-agent

### Step 1: Verify Structure

Ensure your ilminate-agent has:

```bash
# Check structure
ls -la plugins/apex_detection_engine.py
ls -la config/apex-detection-engine.yml  # Optional
```

### Step 2: Verify Classes Exist

The `plugins/apex_detection_engine.py` file must export:

- ✅ `APEXDetectionEngine` class
- ✅ `APEXVerdict` class

### Step 3: Verify Methods

`APEXDetectionEngine` must have:

- ✅ `__init__(self, config: dict)` - Constructor
- ✅ `async def analyze_email(self, email_data)` - Email analysis

### Step 4: Verify Dependencies

Check `requirements.txt` includes all needed packages:

```python
# Common dependencies
pyyaml>=6.0
requests>=2.31.0
numpy>=1.24.0
scikit-learn>=1.3.0
# Add your specific dependencies
```

### Step 5: Test Import Locally

```python
# Test import works
python3 << EOF
import sys
sys.path.insert(0, '/path/to/ilminate-agent')
from plugins.apex_detection_engine import APEXDetectionEngine, APEXVerdict
print("✅ Import successful!")
EOF
```

---

## 🚀 Next Steps

### 1. **Deploy ilminate-agent to EC2**

From ilminate-agent directory:

```bash
# Option A: Use automated script
./deploy-agent-from-repo.sh

# Option B: Manual rsync
rsync -avz --exclude=.git \
  -e "ssh -i ~/.ssh/ilminate-mcp-key.pem" \
  ./ ec2-user@54.237.174.195:/opt/ilminate-agent/

# Then install dependencies
ssh -i ~/.ssh/ilminate-mcp-key.pem ec2-user@54.237.174.195 \
  'cd /opt/ilminate-agent && pip3 install -r requirements.txt && pm2 restart apex-bridge'
```

### 2. **Verify Deployment**

```bash
# Test import on EC2
ssh -i ~/.ssh/ilminate-mcp-key.pem ec2-user@54.237.174.195 \
  'python3 -c "import sys; sys.path.insert(0, \"/opt/ilminate-agent\"); from plugins.apex_detection_engine import APEXDetectionEngine; print(\"OK\")"'

# Test health endpoint
curl http://54.237.174.195:8888/health

# Check PM2 status
ssh -i ~/.ssh/ilminate-mcp-key.pem ec2-user@54.237.174.195 'pm2 status'
```

### 3. **Test MCP Tools**

Once deployed, test MCP tools:

```bash
# Test email analysis (via MCP)
# This will call: MCP Server → APEX Bridge → ilminate-agent
```

---

## 🔍 Troubleshooting

### "No module named 'plugins'"

**Cause:** ilminate-agent not at `/opt/ilminate-agent`

**Fix:**
```bash
# Verify location
ssh ec2-user@54.237.174.195 'ls -la /opt/ilminate-agent/plugins/'
```

### "NameError: name 'APEXDetectionEngine' is not defined"

**Cause:** Import failed but code still references it

**Fix:** Check import works:
```bash
ssh ec2-user@54.237.174.195 'python3 -c "import sys; sys.path.insert(0, \"/opt/ilminate-agent\"); from plugins.apex_detection_engine import APEXDetectionEngine"'
```

### "APEX engine not initialized"

**Cause:** Initialization failed

**Fix:** Check logs:
```bash
ssh ec2-user@54.237.174.195 'pm2 logs apex-bridge --lines 50'
```

---

## 📊 Data Flow Example

### Email Analysis Request

```
1. AI Assistant → MCP Server
   {
     "method": "tools/call",
     "params": {
       "name": "analyze_email_threat",
       "arguments": {
         "sender": "bad@example.com",
         "subject": "Urgent payment",
         "body": "..."
       }
     }
   }

2. MCP Server → APEX Bridge (HTTP POST)
   POST http://localhost:8888/api/analyze-email
   {
     "message_id": "msg-123",
     "sender": "bad@example.com",
     "subject": "Urgent payment",
     "body": "..."
   }

3. APEX Bridge → ilminate-agent (Python)
   verdict = await apex_engine.analyze_email(email_data)

4. ilminate-agent → APEX Bridge (Python object)
   APEXVerdict(
     action="quarantine",
     threat_level="HIGH",
     risk_score=85.5,
     ...
   )

5. APEX Bridge → MCP Server (JSON)
   {
     "success": true,
     "verdict": {
       "action": "quarantine",
       "threat_level": "HIGH",
       ...
     }
   }

6. MCP Server → AI Assistant (MCP response)
   {
     "result": {
       "action": "quarantine",
       "threat_level": "HIGH",
       ...
     }
   }
```

---

## ✅ Summary

**What ilminate-agent needs:**

1. ✅ **Structure:** `/opt/ilminate-agent/plugins/apex_detection_engine.py`
2. ✅ **Classes:** `APEXDetectionEngine` and `APEXVerdict`
3. ✅ **Methods:** `analyze_email()` async method
4. ✅ **Dependencies:** All Python packages in `requirements.txt`
5. ✅ **Config:** Optional YAML config file

**What happens:**

1. APEX Bridge imports ilminate-agent modules
2. Initializes `APEXDetectionEngine` with config
3. Receives HTTP requests from MCP Server
4. Calls ilminate-agent methods
5. Returns JSON responses to MCP Server

**Next:** Deploy ilminate-agent to EC2! 🚀

