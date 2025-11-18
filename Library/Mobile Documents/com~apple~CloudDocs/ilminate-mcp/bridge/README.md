# APEX Bridge Service

HTTP bridge service that connects the MCP server to ilminate-agent detection engines.

## Purpose

The MCP server is written in Node.js/TypeScript, but the detection engines are in Python. This bridge service provides an HTTP API that the MCP server can call to access the Python detection engines.

## Setup

1. **Install Python dependencies:**
   ```bash
   cd bridge
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export APEX_BRIDGE_PORT=8888
   ```

3. **Start the bridge service:**
   ```bash
   python3 apex_bridge.py
   ```

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "apex_available": true,
  "apex_initialized": true
}
```

### `POST /api/analyze-email`
Analyze email for threats using APEX detection engine.

**Request:**
```json
{
  "message_id": "msg-123",
  "sender": "sender@example.com",
  "subject": "Email subject",
  "body": "Email body content",
  "attachments": ["file.pdf"]
}
```

**Response:**
```json
{
  "success": true,
  "verdict": {
    "action": "quarantine",
    "threat_level": "HIGH",
    "risk_score": 85.5,
    "confidence": 0.92,
    "threat_categories": ["phishing", "bec"],
    "indicators": [...],
    "layers": [...]
  }
}
```

### `POST /api/map-mitre`
Map security event to MITRE ATT&CK techniques.

**Request:**
```json
{
  "event_text": "Phishing email with malicious attachment detected"
}
```

**Response:**
```json
{
  "success": true,
  "techniques": [
    {
      "id": "T1566.001",
      "name": "Phishing: Spearphishing Attachment",
      "confidence": 0.9
    }
  ],
  "primary_technique": {...}
}
```

### `POST /api/check-domain`
Check domain reputation.

**Request:**
```json
{
  "domain": "example.com"
}
```

**Response:**
```json
{
  "success": true,
  "reputation_score": 0.2,
  "is_malicious": true,
  "threat_types": ["phishing"],
  "first_seen": "2024-01-15",
  "last_seen": "2024-01-20"
}
```

### `POST /api/scan-image`
Scan image for threats (QR codes, logo impersonation).

**Request:**
```json
{
  "image_url": "https://example.com/image.png"
}
```

**Response:**
```json
{
  "success": true,
  "threats_found": true,
  "qr_codes": [...],
  "logo_impersonation": true,
  "logo_impersonation_target": "Microsoft",
  "hidden_links": [],
  "threat_score": 0.85
}
```

### `GET /api/status`
Get APEX engine status and statistics.

**Response:**
```json
{
  "available": true,
  "statistics": {
    "engine_version": "2.0.0",
    "active_layers": ["YARA", "Deep-Learning"],
    "whitelist_size": 0,
    "blacklist_size": 0
  }
}
```

## Configuration

The bridge service automatically loads configuration from:
- `../ilminate-agent/config/apex-detection-engine.yml`

If the config file doesn't exist, it uses default settings.

## Integration with MCP Server

The MCP server should be configured to call this bridge service:

```env
APEX_BRIDGE_URL=http://localhost:8888
```

The MCP server's `ilminate-api.ts` utility will call these endpoints instead of trying to call ilminate-apex API directly.

