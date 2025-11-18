# 🚀 ilminate MCP Server - Services Status

**Last Updated:** November 18, 2024

---

## 📊 Current Status

### ✅ APEX Bridge Service
- **Status:** ✅ Running
- **Port:** 8889 (8888 was in use by Jupyter)
- **URL:** http://localhost:8889
- **Health Endpoint:** http://localhost:8889/health
- **Logs:** `bridge/bridge.log`

### 🔄 MCP Server
- **Status:** Ready to start
- **Protocol:** MCP (stdio)
- **Start Command:** `npm start`
- **Note:** MCP servers communicate via stdio, typically started by MCP clients

---

## 🔧 What Each Service Does

### 1. APEX Bridge (Python Flask) - ✅ RUNNING

**Purpose:** HTTP API bridge between Node.js MCP server and Python detection engines

**What It Does:**
- Provides REST API endpoints for threat detection
- Connects to ilminate-agent detection engines
- Translates HTTP requests to Python function calls
- Returns JSON responses with threat analysis

**Available Endpoints:**
- `GET /health` - Health check
- `GET /api/status` - Detection engine status
- `POST /api/analyze-email` - Analyze email for threats
- `POST /api/map-mitre` - Map to MITRE ATT&CK
- `POST /api/check-domain` - Check domain reputation
- `POST /api/scan-image` - Scan images for threats

**How to Use:**
```bash
# Check health
curl http://localhost:8889/health

# Analyze email
curl -X POST http://localhost:8889/api/analyze-email \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test@example.com",
    "subject": "Test",
    "body": "Test email"
  }'
```

### 2. MCP Server (Node.js) - Ready

**Purpose:** Exposes ilminate detection capabilities via Model Context Protocol

**What It Does:**
- Implements MCP protocol for AI assistant integration
- Exposes 12+ MCP tools for threat detection
- Routes tool calls to APEX Bridge
- Formats responses for MCP protocol

**MCP Tools Available:**
1. `analyze_email_threat` - Email threat analysis
2. `map_to_mitre_attack` - MITRE ATT&CK mapping
3. `check_domain_reputation` - Domain reputation
4. `get_campaign_analysis` - Campaign analysis
5. `scan_image_for_threats` - Image scanning
6. `get_detection_engine_status` - Engine status
7. `subscribe_to_threat_feed` - Threat feed subscription
8. `update_detection_rules` - Rule updates
9. `get_threat_feed_status` - Feed status
10. `query_security_assistant` - Security Assistant queries
11. `get_portal_threats` - Portal threats
12. `enrich_siem_event` - SIEM event enrichment

**How to Use:**
- MCP servers are typically started by MCP clients (like Claude Desktop)
- For testing, you can start manually: `npm start`
- Configure in Claude Desktop: See `START_HERE.md`

### 3. Detection Engines (ilminate-agent) - Connected

**Purpose:** Core threat detection logic

**What It Does:**
- Multi-layer threat detection (18+ engines)
- Deep learning AI models (BERT, RoBERTa, Vision)
- OSINT integration (Mosint, Hunter.io, Intelligence X, HaveIBeenPwned)
- Image scanning (QR codes, logo impersonation)
- BEC/ATO detection
- AI-generated content detection

---

## 🔄 How They Work Together

```
1. AI Assistant (Claude Desktop)
   ↓ MCP Protocol
2. MCP Server (Node.js)
   ↓ HTTP Request
3. APEX Bridge (Python Flask)
   ↓ Python Import
4. Detection Engines (ilminate-agent)
   ↓ Analysis
5. Results flow back through chain
```

---

## 📝 Quick Commands

### Check APEX Bridge
```bash
curl http://localhost:8889/health
```

### View Bridge Logs
```bash
tail -f bridge/bridge.log
```

### Test Email Analysis
```bash
curl -X POST http://localhost:8889/api/analyze-email \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "suspicious@example.com",
    "subject": "Urgent: Action Required",
    "body": "Click here immediately!"
  }'
```

### Start MCP Server (for testing)
```bash
cd /path/to/ilminate-mcp
npm start
```

---

## 🎯 Summary

**APEX Bridge:** ✅ Running on port 8889  
**MCP Server:** Ready (started by MCP clients)  
**Detection Engines:** Connected and available  

**All services are operational and ready to detect threats!** 🚀

