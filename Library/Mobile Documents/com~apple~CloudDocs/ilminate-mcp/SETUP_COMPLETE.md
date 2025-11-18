# ilminate MCP Server - Complete Setup Guide

**Status:** ✅ Setup Complete  
**Date:** November 17, 2024

---

## 🎯 Overview

The ilminate MCP Server is now fully configured and ready to use. This document provides a complete guide for running and integrating the MCP server.

---

## 📋 What Has Been Set Up

### ✅ Configuration Files
- `.env.template` - Environment variable template
- `.env.example` - Example configuration (if needed)

### ✅ Setup Scripts
- `scripts/setup.sh` - Complete setup automation
- `scripts/start-bridge.sh` - Start APEX Bridge service
- `scripts/test-connectivity.sh` - Test all connections

### ✅ Dependencies
- Node.js dependencies installed (`node_modules/`)
- Python dependencies installed (`bridge/venv/`)
- TypeScript build complete (`dist/`)

### ✅ Integration Points
- APEX Bridge configured to connect to ilminate-agent
- MCP tools ready for use
- Service integrations configured

---

## 🚀 Quick Start

### 1. Initial Setup (One-Time)

```bash
cd /path/to/ilminate-mcp
./scripts/setup.sh
```

This will:
- Check prerequisites
- Install all dependencies
- Build TypeScript
- Create configuration files

### 2. Configure Environment

```bash
# Copy template to .env
cp .env.template .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Minimum required configuration:**
```bash
APEX_BRIDGE_URL=http://localhost:8888
LOG_LEVEL=info
```

### 3. Start Services

**Terminal 1: Start APEX Bridge**
```bash
./scripts/start-bridge.sh
```

**Terminal 2: Start MCP Server**
```bash
npm start
```

### 4. Test Connectivity

```bash
./scripts/test-connectivity.sh
```

---

## 🔧 Configuration Details

### Environment Variables

#### Required
- `APEX_BRIDGE_URL` - URL to APEX Bridge service (default: http://localhost:8888)

#### Optional
- `LOG_LEVEL` - Logging level: debug, info, warn, error (default: info)
- `API_KEY_REQUIRED` - Require API key authentication (default: false)
- `API_KEY` - API key for authentication (if required)

#### Service Integration URLs
- `ILMINATE_API_URL` - Fallback API URL
- `APEX_API_URL` - ilminate-apex API URL
- `PORTAL_API_URL` - ilminate-portal API URL
- `SIEM_API_URL` - ilminate-siem API URL
- `EMAIL_API_URL` - ilminate-email API URL
- `SANDBOX_API_URL` - ilminate-sandbox API URL

---

## 📡 Available MCP Tools

The MCP server exposes 12+ tools:

1. **`analyze_email_threat`** - Analyze email for BEC/phishing
2. **`map_to_mitre_attack`** - Map events to MITRE ATT&CK
3. **`check_domain_reputation`** - Check domain reputation
4. **`get_campaign_analysis`** - Get campaign analysis
5. **`scan_image_for_threats`** - Scan images for threats
6. **`get_detection_engine_status`** - Get engine status
7. **`subscribe_to_threat_feed`** - Subscribe to threat feeds
8. **`update_detection_rules`** - Update detection rules
9. **`get_threat_feed_status`** - Get feed status
10. **`query_security_assistant`** - Query Security Assistant
11. **`get_portal_threats`** - Get portal threats
12. **`enrich_siem_event`** - Enrich SIEM events

---

## 🔌 Integration with ilminate Services

### ilminate-agent (✅ Integrated)
- **Status:** Fully integrated via APEX Bridge
- **Connection:** Automatic via `bridge/apex_bridge.py`
- **Path:** `../ilminate-agent` (sibling directory)

### ilminate-apex (🔄 Planned)
- **Status:** Integration planned
- **Use Case:** Security Assistant can use MCP tools
- **Configuration:** Set `APEX_API_URL` in `.env`

### ilminate-portal (📋 Planned)
- **Status:** Integration planned
- **Use Case:** Portal can query threats via MCP
- **Configuration:** Set `PORTAL_API_URL` in `.env`

### ilminate-siem (📋 Planned)
- **Status:** Integration planned
- **Use Case:** Enrich SIEM events with threat intelligence
- **Configuration:** Set `SIEM_API_URL` in `.env`

---

## 🧪 Testing

### Test APEX Bridge
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

### Test Detection Engine Status
```bash
curl http://localhost:8888/api/status
```

### Test Email Analysis
```bash
curl -X POST http://localhost:8888/api/analyze-email \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test email"
  }'
```

---

## 📚 Using with Claude Desktop

1. **Install Claude Desktop** (if not already installed)

2. **Configure Claude Desktop**:
   
   Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`
   
   Add:
   ```json
   {
     "mcpServers": {
       "ilminate": {
         "command": "node",
         "args": ["/path/to/ilminate-mcp/dist/index.js"],
         "env": {
           "APEX_BRIDGE_URL": "http://localhost:8888"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

4. **Verify**: Claude Desktop should now have access to ilminate MCP tools

---

## 🐛 Troubleshooting

### APEX Bridge Not Starting
- Check Python version: `python3 --version` (need 3.8+)
- Check dependencies: `cd bridge && source venv/bin/activate && pip list`
- Check ilminate-agent path: Should be at `../ilminate-agent`

### MCP Server Not Starting
- Check Node.js version: `node --version` (need 18+)
- Rebuild: `npm run build`
- Check for errors: `npm run type-check`

### Connection Issues
- Verify APEX Bridge is running: `curl http://localhost:8888/health`
- Check port conflicts: `lsof -i :8888`
- Review logs for errors

---

## 📊 Architecture

```
┌─────────────────────────────────────┐
│   External AI Assistants/Tools     │
│   (Claude Desktop, Custom Apps)    │
└──────────────┬──────────────────────┘
               │ MCP Protocol
               ▼
┌─────────────────────────────────────┐
│   ilminate MCP Server (Node.js)    │
│   - 12+ MCP Tools                  │
│   - Authentication                 │
│   - Logging                        │
└──────────────┬──────────────────────┘
               │ HTTP
               ▼
┌─────────────────────────────────────┐
│   APEX Bridge (Python Flask)       │
│   - HTTP API                       │
│   - CORS enabled                  │
│   - Port 8888                     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   ilminate-agent Detection Engines │
│   - APEX Detection Engine          │
│   - 18+ Detection Engines         │
│   - Deep Learning AI               │
└─────────────────────────────────────┘
```

---

## 🎯 Next Steps

1. **Start Services**: Use the scripts provided
2. **Test Connectivity**: Run `./scripts/test-connectivity.sh`
3. **Integrate with Claude Desktop**: Follow instructions above
4. **Configure Service URLs**: Update `.env` with your service URLs
5. **Test MCP Tools**: Use Claude Desktop or MCP client to test tools

---

## 📝 Additional Resources

- **README.md** - Complete overview
- **QUICK_START.md** - Quick start guide
- **DEPLOYMENT.md** - Deployment instructions
- **CROSS_REPO_INTEGRATION.md** - Integration plan
- **TESTING_GUIDE.md** - Testing guide

---

**Setup Complete!** 🎉

The ilminate MCP Server is ready to use. Start the services and begin integrating with your ilminate ecosystem.

