# 🚀 ilminate MCP Server - Services Explained

**What Each Service Does and How They Work Together**

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────┐
│   External AI Assistants / Tools          │
│   (Claude Desktop, Custom AI Apps)         │
└──────────────┬──────────────────────────────┘
               │ MCP Protocol (stdio/HTTP)
               ▼
┌─────────────────────────────────────────────┐
│   ilminate MCP Server (Node.js)           │
│   - Exposes 12+ MCP Tools                 │
│   - Handles MCP Protocol                  │
│   - Routes requests to APEX Bridge         │
└──────────────┬──────────────────────────────┘
               │ HTTP (REST API)
               ▼
┌─────────────────────────────────────────────┐
│   APEX Bridge Service (Python Flask)      │
│   - HTTP API Server (Port 8888)           │
│   - Connects to ilminate-agent            │
│   - Wraps detection engines               │
└──────────────┬──────────────────────────────┘
               │ Python Import
               ▼
┌─────────────────────────────────────────────┐
│   ilminate-agent Detection Engines        │
│   - APEX Detection Engine                 │
│   - 18+ Detection Engines                 │
│   - Deep Learning AI Models               │
└─────────────────────────────────────────────┘
```

---

## 🔧 Service 1: APEX Bridge (Python Flask)

### What It Does
The **APEX Bridge** is a Python Flask HTTP service that acts as a bridge between the Node.js MCP server and the Python detection engines in ilminate-agent.

### Key Functions
1. **HTTP API Server**: Runs on port 8888, provides REST endpoints
2. **Detection Engine Wrapper**: Imports and initializes the APEX Detection Engine
3. **Request Handler**: Receives HTTP requests from MCP server, calls detection engines, returns JSON responses
4. **CORS Enabled**: Allows cross-origin requests from MCP server

### Endpoints Provided
- `GET /health` - Health check
- `GET /api/status` - Detection engine status
- `POST /api/analyze-email` - Analyze email for threats
- `POST /api/map-mitre` - Map events to MITRE ATT&CK
- `POST /api/check-domain` - Check domain reputation
- `POST /api/scan-image` - Scan images for threats

### Why It Exists
- **Language Bridge**: Node.js (MCP server) can't directly import Python modules
- **Protocol Translation**: Converts HTTP requests to Python function calls
- **Isolation**: Keeps detection engine code separate from MCP server

### How to Start
```bash
cd /path/to/ilminate-mcp
./scripts/start-bridge.sh
```

### Status Check
```bash
curl http://localhost:8888/health
```

---

## 🔧 Service 2: ilminate MCP Server (Node.js)

### What It Does
The **MCP Server** is a Node.js service that implements the Model Context Protocol (MCP). It exposes ilminate's detection capabilities as standardized MCP tools that can be used by AI assistants and external tools.

### Key Functions
1. **MCP Protocol Handler**: Implements MCP protocol (stdio-based communication)
2. **Tool Registry**: Exposes 12+ MCP tools for threat detection
3. **Request Router**: Routes MCP tool calls to appropriate handlers
4. **API Client**: Calls APEX Bridge HTTP API to execute detection
5. **Response Formatter**: Formats detection results for MCP protocol

### MCP Tools Exposed
1. **`analyze_email_threat`** - Analyze emails for BEC/phishing
2. **`map_to_mitre_attack`** - Map security events to MITRE ATT&CK
3. **`check_domain_reputation`** - Check domain reputation
4. **`get_campaign_analysis`** - Get threat campaign analysis
5. **`scan_image_for_threats`** - Scan images for QR codes/threats
6. **`get_detection_engine_status`** - Get engine status
7. **`subscribe_to_threat_feed`** - Subscribe to threat feeds
8. **`update_detection_rules`** - Update detection rules
9. **`get_threat_feed_status`** - Get feed status
10. **`query_security_assistant`** - Query Security Assistant
11. **`get_portal_threats`** - Get portal threats
12. **`enrich_siem_event`** - Enrich SIEM events

### Why It Exists
- **Standardization**: MCP is a standard protocol for AI tool integration
- **AI Integration**: Enables Claude Desktop and other AI tools to use ilminate detection
- **Extensibility**: Easy to add new tools without changing core infrastructure
- **Cross-Platform**: Works with any MCP-compatible client

### How to Start
```bash
cd /path/to/ilminate-mcp
npm start
```

### How It Works
1. Receives MCP tool call requests via stdio
2. Parses the request (tool name + arguments)
3. Calls APEX Bridge HTTP API with the request
4. Formats the response for MCP protocol
5. Returns response via stdio

---

## 🔧 Service 3: ilminate-agent Detection Engines (Python)

### What It Does
The **ilminate-agent** repository contains the actual detection engines that analyze emails and detect threats. This is the core detection logic.

### Key Components
1. **APEX Detection Engine**: Multi-layer threat detection orchestrator
2. **18+ Detection Engines**: Various detection methods (ClamAV, YARA, ML, AI, etc.)
3. **Deep Learning Models**: BERT, RoBERTa, Vision models for threat detection
4. **OSINT Integration**: Mosint, Hunter.io, Intelligence X, HaveIBeenPwned
5. **Image Scanning**: QR code detection, logo impersonation detection

### Detection Layers
- **Layer 0**: Pre-filtering (whitelist/blacklist)
- **Layer 1**: Traditional scanning (ClamAV, Sublime Security)
- **Layer 2**: YARA pattern matching
- **Layer 3**: Feature-based ML (GBDT)
- **Layer 4**: Deep Learning AI (BERT, RoBERTa, Vision)
- **Layer 4.5**: Image & QR code scanning
- **Specialized**: BEC, ATO, AI-generated content detection

### Why It Exists
- **Core Detection Logic**: This is where actual threat detection happens
- **Multi-Layer Protection**: Combines multiple detection methods
- **AI-Powered**: Uses advanced ML/AI for threat detection
- **Comprehensive**: Covers 10+ threat types

---

## 🔄 How They Work Together

### Request Flow

1. **AI Assistant** (e.g., Claude Desktop) wants to analyze an email
   ```
   User: "Analyze this email for threats"
   ```

2. **MCP Server** receives MCP tool call
   ```
   Tool: analyze_email_threat
   Args: { subject: "...", sender: "...", body: "..." }
   ```

3. **MCP Server** calls APEX Bridge HTTP API
   ```http
   POST http://localhost:8888/api/analyze-email
   Body: { subject: "...", sender: "...", body: "..." }
   ```

4. **APEX Bridge** receives HTTP request and calls detection engine
   ```python
   verdict = apex_engine.analyze_email(email_data)
   ```

5. **Detection Engine** runs multi-layer analysis
   - Pre-filtering
   - Traditional scanning
   - YARA patterns
   - ML models
   - Deep learning AI
   - Image scanning
   - OSINT checks

6. **Results flow back** through the chain
   ```
   Detection Engine → APEX Bridge → MCP Server → AI Assistant
   ```

7. **AI Assistant** receives threat analysis
   ```
   Response: {
     threat_score: 0.85,
     threat_type: "BEC",
     recommendation: "quarantine"
   }
   ```

---

## 🎯 Use Cases

### 1. Claude Desktop Integration
- User asks Claude to analyze an email
- Claude uses MCP to call ilminate detection
- Gets threat analysis and explains to user

### 2. Automated Threat Detection
- External system sends email to MCP server
- Gets threat analysis
- Takes action based on results

### 3. Threat Intelligence Aggregation
- Multiple sources query detection engines
- Unified API via MCP
- Consistent threat analysis

### 4. Security Assistant Enhancement
- Security Assistant queries detection engines
- Gets real-time threat intelligence
- Provides better security recommendations

---

## 📊 Service Status

### Check APEX Bridge
```bash
curl http://localhost:8888/health
```

Expected:
```json
{
  "status": "healthy",
  "apex_available": true,
  "apex_initialized": true
}
```

### Check MCP Server
```bash
# MCP server communicates via stdio
# Status visible in logs or via tool calls
```

### Check Detection Engines
```bash
curl http://localhost:8888/api/status
```

---

## 🔍 Monitoring

### APEX Bridge Logs
```bash
tail -f bridge/bridge.log
```

### MCP Server Logs
```bash
# Check npm start output
# Or configure logging in .env (LOG_LEVEL)
```

### Health Monitoring
```bash
./scripts/test-connectivity.sh
```

---

## 🎉 Summary

**APEX Bridge**: HTTP API server that bridges Node.js and Python  
**MCP Server**: Standardized protocol interface for AI tools  
**Detection Engines**: Core threat detection logic  

Together, they enable:
- ✅ AI assistants to use ilminate detection
- ✅ Standardized threat detection API
- ✅ Multi-layer threat analysis
- ✅ Real-time threat intelligence
- ✅ Cross-platform integration

**All services work together to provide enterprise-grade threat detection via a standardized MCP interface!** 🚀

