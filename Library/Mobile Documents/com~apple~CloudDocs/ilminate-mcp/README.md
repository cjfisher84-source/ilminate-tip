# ilminate MCP Server

Model Context Protocol (MCP) server for ilminate Detection Engines. This server exposes ilminate's threat detection capabilities as standardized MCP tools, enabling integration with AI assistants and external security platforms.

## Overview

This MCP server implements **Phase 2** of the ilminate MCP Integration Plan, exposing the following detection capabilities:

- **Email Threat Analysis** - BEC/phishing detection with keyword heuristics
- **MITRE ATT&CK Mapping** - Pattern-based technique mapping
- **Domain Reputation** - Threat intelligence and domain analysis
- **Campaign Analysis** - Active threat campaign tracking
- **Image Scanning** - QR code detection, logo impersonation, hidden links

## Architecture

```
┌─────────────────────────────────────────┐
│   External AI Assistants / Tools       │
│   (Claude Desktop, Custom AI Apps)     │
└──────────────┬──────────────────────────┘
               │ MCP Protocol
               ▼
┌─────────────────────────────────────────┐
│   ilminate MCP Server (Node.js)        │
│   (This Service)                        │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │   MCP Tools:                      │  │
│  │   - analyze_email_threat          │  │
│  │   - map_to_mitre_attack           │  │
│  │   - check_domain_reputation       │  │
│  │   - get_campaign_analysis         │  │
│  │   - scan_image_for_threats        │  │
│  └───────────────────────────────────┘  │
│              │                          │
│              ▼ HTTP                    │
│  ┌───────────────────────────────────┐  │
│  │   APEX Bridge Service (Python)    │  │
│  │   (bridge/apex_bridge.py)         │  │
│  └───────────────────────────────────┘  │
│              │                          │
│              ▼                          │
│  ┌───────────────────────────────────┐  │
│  │   ilminate-agent Detection        │  │
│  │   Engines (Python)                │  │
│  │   - APEX Detection Engine         │  │
│  │   - Multi-layer detection         │  │
│  │   - Deep Learning AI models       │  │
│  │   - Image/QR scanning             │  │
│  │   - Mosint OSINT                  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Installation

```bash
npm install
```

## Configuration

### 1. Setup APEX Bridge (Python Service)

The MCP server connects to ilminate-agent detection engines via a Python bridge service:

```bash
cd bridge
pip install -r requirements.txt
python3 apex_bridge.py
```

The bridge service runs on port 8888 by default.

### 2. Configure MCP Server

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key configuration options:
- `APEX_BRIDGE_URL` - URL to APEX Bridge service (default: http://localhost:8888)
- `ILMINATE_API_URL` - Fallback URL to ilminate-apex API (if bridge unavailable)
- `ILMINATE_API_KEY` - API key for ilminate-apex (if using fallback)
- `API_KEY` - API key for MCP server authentication
- External threat intelligence API keys (optional, for Phase 1 integration)

## Development

```bash
# Run in development mode with hot reload
npm run dev

# Build for production
npm run build

# Run production build
npm start
```

## MCP Tools

### `analyze_email_threat`

Analyze email for BEC/phishing indicators using ilminate's triage analysis engine.

**Input:**
```json
{
  "subject": "string",
  "sender": "string",
  "body": "string",
  "attachments": ["string"]
}
```

**Output:**
```json
{
  "threat_score": 0.85,
  "threat_type": "BEC",
  "indicators": ["urgent_language", "suspicious_sender"],
  "recommendation": "quarantine"
}
```

### `map_to_mitre_attack`

Map security event to MITRE ATT&CK techniques.

**Input:**
```json
{
  "event_text": "string"
}
```

**Output:**
```json
{
  "techniques": [
    {
      "id": "T1566.001",
      "name": "Phishing: Spearphishing Attachment",
      "confidence": 0.9
    }
  ]
}
```

### `check_domain_reputation`

Check domain reputation and threat intelligence.

**Input:**
```json
{
  "domain": "example.com"
}
```

**Output:**
```json
{
  "reputation_score": 0.2,
  "is_malicious": true,
  "threat_types": ["phishing", "malware"],
  "first_seen": "2024-01-15",
  "last_seen": "2024-01-20"
}
```

### `get_campaign_analysis`

Get analysis of active threat campaigns.

**Input:**
```json
{
  "campaign_name": "string",
  "time_range": "7d"
}
```

**Output:**
```json
{
  "campaign_name": "Example Campaign",
  "threat_count": 150,
  "affected_domains": ["example.com"],
  "techniques": ["T1566.001"],
  "timeline": []
}
```

### `scan_image_for_threats`

Analyze image for QR codes, logo impersonation, hidden links.

**Input:**
```json
{
  "image_url": "https://example.com/image.png",
  "message_context": {
    "subject": "string",
    "sender": "string"
  }
}
```

**Output:**
```json
{
  "threats_found": true,
  "qr_codes": [{"data": "malicious-url", "position": {}}],
  "logo_impersonation": true,
  "hidden_links": []
}
```

## Integration with ilminate-agent

This MCP server connects to **ilminate-agent** detection engines via the APEX Bridge service. The detection engines include:

- **APEX Detection Engine** - Multi-layer threat detection
- **Layer 0**: Pre-filtering (whitelist/blacklist)
- **Layer 1**: Traditional scanning (ClamAV, Sublime Security)
- **Layer 2**: YARA pattern matching
- **Layer 3**: Feature-based ML (GBDT)
- **Layer 4**: Deep Learning AI (BERT, RoBERTa, Vision)
- **Layer 4.5**: Image & QR code scanning
- **Specialized**: BEC, ATO, AI-generated content detection
- **OSINT**: Mosint integration for threat intelligence

Ensure:
1. **ilminate-agent** repository is accessible (sibling directory)
2. **APEX Bridge** service is running (`python3 bridge/apex_bridge.py`)
3. Detection engines are properly configured in `ilminate-agent/config/apex-detection-engine.yml`

## Security

- API key authentication required
- Rate limiting per client
- Input validation and sanitization
- Audit logging for all tool calls
- Data privacy compliance (GDPR/CCPA)

## Phase 1: MCP Client Integration

For integrating external threat intelligence MCP servers into ilminate-apex Security Assistant, see the `client/` directory (to be implemented).

## License

MIT

