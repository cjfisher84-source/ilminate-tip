# 🚀 ilminate MCP Server - Start Here

**Quick guide to get up and running in 5 minutes**

---

## ✅ Prerequisites Check

Before starting, ensure you have:
- ✅ Node.js 18+ installed
- ✅ Python 3.8+ installed
- ✅ ilminate-agent repository accessible (sibling directory)

---

## 🎯 Quick Start (3 Steps)

### Step 1: Setup (One-Time)
```bash
cd /path/to/ilminate-mcp
./scripts/setup.sh
```

### Step 2: Configure
```bash
# Create .env from template
cp .env.template .env

# Edit if needed (defaults work for local development)
nano .env
```

### Step 3: Start Services

**Terminal 1 - APEX Bridge:**
```bash
./scripts/start-bridge.sh
```

**Terminal 2 - MCP Server:**
```bash
npm start
```

---

## ✅ Verify It's Working

### Test 1: APEX Bridge Health
```bash
curl http://localhost:8888/health
```

Should return:
```json
{"status":"healthy","apex_available":true,"apex_initialized":true}
```

### Test 2: Run Connectivity Test
```bash
./scripts/test-connectivity.sh
```

---

## 🔌 Using with Claude Desktop

1. Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Add:
```json
{
  "mcpServers": {
    "ilminate": {
      "command": "node",
      "args": ["/absolute/path/to/ilminate-mcp/dist/index.js"],
      "env": {
        "APEX_BRIDGE_URL": "http://localhost:8888"
      }
    }
  }
}
```

3. Restart Claude Desktop

4. You now have access to ilminate detection tools! 🎉

---

## 📚 Available MCP Tools

Once connected, you can use:
- `analyze_email_threat` - Analyze emails for threats
- `check_domain_reputation` - Check domain reputation
- `scan_image_for_threats` - Scan images for QR codes/threats
- `get_detection_engine_status` - Get engine status
- And 8+ more tools...

---

## 🆘 Troubleshooting

**Bridge won't start?**
- Check Python: `python3 --version`
- Check ilminate-agent: `ls ../ilminate-agent`

**MCP Server won't start?**
- Check Node.js: `node --version`
- Rebuild: `npm run build`

**Connection issues?**
- Run: `./scripts/test-connectivity.sh`
- Check logs for errors

---

## 📖 More Information

- **SETUP_COMPLETE.md** - Complete setup guide
- **README.md** - Full documentation
- **QUICK_START.md** - Detailed quick start
- **DEPLOYMENT.md** - Production deployment

---

**Ready to go!** Start the services and begin using ilminate MCP tools. 🚀

