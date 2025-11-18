# Quick Start Guide

**Get up and running in 5 minutes**

---

## Prerequisites

- Node.js 18+
- Python 3.8+
- ilminate-agent repository accessible

---

## Step 1: Install Dependencies

```bash
npm install
cd bridge && pip install -r requirements.txt && cd ..
```

---

## Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration (see TESTING_GUIDE.md)
```

**Minimum required**:
```bash
APEX_BRIDGE_URL=http://localhost:8888
```

---

## Step 3: Start Services

### Terminal 1: Start APEX Bridge
```bash
cd bridge
python3 apex_bridge.py
```

### Terminal 2: Start MCP Server
```bash
npm run build
npm start
```

---

## Step 4: Test Basic Functionality

### Test Detection Engine Status
```bash
# Using MCP client (if you have one)
# Or use the example in examples/basic-usage.ts
```

### Test Threat Feed Subscription
```typescript
// See TESTING_GUIDE.md for full examples
```

---

## Step 5: Verify Everything Works

```bash
# Check APEX Bridge
curl http://localhost:8888/health

# Should return: {"status":"healthy","apex_available":true,"apex_initialized":true}
```

---

## Common Issues

### "APEX Bridge not found"
- Make sure bridge is running: `python3 bridge/apex_bridge.py`
- Check port 8888 is not in use

### "ilminate-agent not found"
- Verify ilminate-agent is in sibling directory
- Check path in `bridge/apex_bridge.py`

### "MCP server won't start"
- Check Node.js version: `node --version` (should be 18+)
- Run `npm install` again
- Check for TypeScript errors: `npm run type-check`

---

## Next Steps

1. Read `TESTING_GUIDE.md` for detailed testing
2. Configure cross-repo integrations in `.env`
3. Test threat feed subscriptions
4. Add custom MCP tools

---

**Need help?** Check `TESTING_GUIDE.md` for detailed instructions.

