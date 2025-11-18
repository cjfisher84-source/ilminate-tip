# ilminate-agent Integration Guide

This document explains how the MCP server integrates with ilminate-agent detection engines.

## Overview

The MCP server connects to **ilminate-agent** detection engines through a Python bridge service. This architecture allows the Node.js MCP server to access Python-based detection engines without requiring a direct Python integration.

## Architecture

```
┌─────────────────────────────────────────┐
│   MCP Client (Claude Desktop, etc.)     │
└──────────────┬──────────────────────────┘
               │ MCP Protocol (stdio)
               ▼
┌─────────────────────────────────────────┐
│   ilminate MCP Server (Node.js)        │
│   - MCP Protocol Handler                │
│   - Tool Implementations                │
└──────────────┬──────────────────────────┘
               │ HTTP REST API
               ▼
┌─────────────────────────────────────────┐
│   APEX Bridge Service (Python)          │
│   - HTTP API Server                     │
│   - Wraps APEX Detection Engine         │
└──────────────┬──────────────────────────┘
               │ Direct Python Import
               ▼
┌─────────────────────────────────────────┐
│   ilminate-agent Detection Engines      │
│   - APEXDetectionEngine                  │
│   - Multi-layer detection                │
│   - Deep Learning models                 │
│   - Image/QR scanners                    │
│   - Mosint OSINT                         │
└─────────────────────────────────────────┘
```

## Detection Engines Available

### APEX Detection Engine (Main)

Located in: `ilminate-agent/plugins/apex_detection_engine.py`

**Multi-Layer Detection:**
- **Layer 0**: Pre-filtering (whitelist/blacklist, email verification)
- **Layer 1**: Traditional scanning (ClamAV, Sublime Security, SpamAssassin)
- **Layer 2**: YARA pattern matching
- **Layer 3**: Feature-based ML (GBDT)
- **Layer 4**: Deep Learning AI (BERT, RoBERTa, Vision models)
- **Layer 4.5**: Image & QR code scanning

**Specialized Engines:**
- BEC (Business Email Compromise) Detector
- ATO (Account Takeover) Detector
- AI-Generated Content Detector

**OSINT Integration:**
- Mosint platform integration
- Hunter.io (related domains)
- Intelligence X (breach checking)
- EmailRep.io (reputation)

## MCP Tools Mapping

| MCP Tool | APEX Bridge Endpoint | Detection Engine Used |
|----------|---------------------|----------------------|
| `analyze_email_threat` | `/api/analyze-email` | APEXDetectionEngine (all layers) |
| `map_to_mitre_attack` | `/api/map-mitre` | APEXDetectionEngine (threat categorization) |
| `check_domain_reputation` | `/api/check-domain` | MosintDetector (OSINT) |
| `scan_image_for_threats` | `/api/scan-image` | ImageScanner plugin |
| `get_campaign_analysis` | N/A | (Future: Campaign tracking) |
| `get_detection_engine_status` | `/api/status` | APEXDetectionEngine statistics |

## Setup Instructions

### 1. Prerequisites

- **ilminate-agent** repository must be accessible
  - Should be in sibling directory: `../ilminate-agent`
  - Or update path in `bridge/apex_bridge.py`

- **Python 3.8+** with required packages
  - See `bridge/requirements.txt`

- **Node.js 18+** for MCP server

### 2. Start APEX Bridge Service

```bash
# Option 1: Use startup script
./scripts/start-bridge.sh

# Option 2: Manual start
cd bridge
pip install -r requirements.txt
python3 apex_bridge.py
```

The bridge service runs on `http://localhost:8888` by default.

### 3. Configure MCP Server

Set environment variables:

```bash
# .env file
APEX_BRIDGE_URL=http://localhost:8888
```

### 4. Start MCP Server

```bash
npm install
npm run build
npm start
```

## Configuration

### APEX Detection Engine Configuration

The bridge service loads configuration from:
- `../ilminate-agent/config/apex-detection-engine.yml`

Key configuration sections:
- `detection_layers` - Enable/disable detection layers
- `deep_learning.models` - Configure AI models
- `mosint` - OSINT integration settings
- `performance` - Timeouts and resource limits

### Bridge Service Configuration

Environment variables:
- `APEX_BRIDGE_PORT` - Port for bridge service (default: 8888)
- `ILMINATE_AGENT_PATH` - Path to ilminate-agent (auto-detected)

## Testing the Integration

### 1. Check Bridge Health

```bash
curl http://localhost:8888/health
```

Expected response:
```json
{
  "status": "healthy",
  "apex_available": true,
  "apex_initialized": true
}
```

### 2. Test Email Analysis

```bash
curl -X POST http://localhost:8888/api/analyze-email \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test@example.com",
    "subject": "Urgent: Action Required",
    "body": "Please wire transfer $50,000 immediately"
  }'
```

### 3. Test MCP Server

Use the MCP client example:
```bash
npm run build
node examples/basic-usage.js
```

## Troubleshooting

### Bridge Service Won't Start

1. **Check Python path:**
   ```bash
   python3 --version
   ```

2. **Check ilminate-agent path:**
   - Verify `../ilminate-agent` exists
   - Or update path in `bridge/apex_bridge.py`

3. **Check dependencies:**
   ```bash
   cd bridge
   pip install -r requirements.txt
   ```

### APEX Engine Not Initializing

1. **Check configuration file:**
   - Verify `ilminate-agent/config/apex-detection-engine.yml` exists
   - Check for syntax errors

2. **Check Python imports:**
   ```bash
   cd ../ilminate-agent
   python3 -c "from plugins.apex_detection_engine import APEXDetectionEngine"
   ```

3. **Check logs:**
   - Bridge service logs errors to console
   - Look for import errors or configuration issues

### MCP Server Can't Connect to Bridge

1. **Verify bridge is running:**
   ```bash
   curl http://localhost:8888/health
   ```

2. **Check APEX_BRIDGE_URL:**
   ```bash
   echo $APEX_BRIDGE_URL
   ```

3. **Check firewall/network:**
   - Ensure port 8888 is accessible
   - Check for firewall rules blocking localhost

## Performance Considerations

- **Bridge Service**: Single-threaded Flask server
  - For production, use gunicorn or uvicorn
  - Consider multiple worker processes

- **Detection Engine**: Multi-layer analysis
  - Average processing time: ~400ms per email
  - Deep learning layers add ~200ms
  - OSINT checks add ~100ms (strategic use)

- **Caching**: Consider implementing caching for:
  - Domain reputation checks
  - Image scan results
  - Model predictions

## Future Enhancements

1. **Direct Python Integration**: Use Python subprocess or FFI instead of HTTP bridge
2. **WebSocket Support**: Real-time detection updates
3. **Batch Processing**: Process multiple emails in parallel
4. **Campaign Tracking**: Integrate campaign analysis from ilminate-agent
5. **Metrics Export**: Prometheus metrics from detection engines

## Security Considerations

- **Bridge Service**: Runs on localhost by default
  - For remote access, add authentication
  - Use HTTPS in production

- **API Keys**: Store securely in environment variables
  - Never commit API keys to version control

- **Rate Limiting**: Implement rate limiting on bridge service
  - Prevent abuse of detection engines

## Support

For issues with:
- **MCP Server**: Check `src/utils/logger.ts` for logs
- **Bridge Service**: Check console output
- **Detection Engines**: Check `ilminate-agent` logs

