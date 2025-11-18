# Testing Guide: Threat Feeds & Cross-Repo Integration

**Step-by-step guide to test all new features**

---

## Step 1: Configure API Endpoints in .env

### Create/Update .env File

```bash
# Copy example if it doesn't exist
cp .env.example .env
```

### Add Configuration

Edit `.env` file with your actual endpoints:

```bash
# MCP Server Configuration
MCP_SERVER_PORT=3000
MCP_SERVER_HOST=localhost

# Authentication
API_KEY=your-api-key-here
API_KEY_REQUIRED=false  # Set to true in production

# ilminate-agent Integration (via APEX Bridge)
APEX_BRIDGE_URL=http://localhost:8888
ILMINATE_API_URL=http://localhost:3000  # Fallback
ILMINATE_API_KEY=your-ilminate-api-key

# Cross-Repo Integration URLs
APEX_API_URL=http://localhost:3000
PORTAL_API_URL=http://localhost:3001
SIEM_API_URL=http://localhost:55000
EMAIL_API_URL=http://localhost:3002
SANDBOX_API_URL=http://localhost:3003

# Cross-Repo API Keys
APEX_API_KEY=your-apex-api-key
PORTAL_API_KEY=your-portal-api-key
SIEM_API_USER=wazuh
SIEM_API_PASSWORD=your-siem-password
EMAIL_API_KEY=your-email-api-key
SANDBOX_API_KEY=your-sandbox-api-key

# Threat Feed Configuration
THREAT_FEED_POLLING_INTERVAL=60  # minutes

# Logging
LOG_LEVEL=info
```

### Verify Configuration

```bash
# Check if .env is loaded
node -e "require('dotenv').config(); console.log(process.env.APEX_BRIDGE_URL)"
```

---

## Step 2: Start Required Services

### 1. Start APEX Bridge (Required for detection engines)

```bash
# Option 1: Use startup script
./scripts/start-bridge.sh

# Option 2: Manual start
cd bridge
pip install -r requirements.txt
python3 apex_bridge.py
```

**Verify**: `curl http://localhost:8888/health`

### 2. Start MCP Server

```bash
# Install dependencies
npm install

# Build
npm run build

# Start server
npm start

# Or in development mode
npm run dev
```

**Verify**: Server should start without errors

---

## Step 3: Test Threat Feed Subscriptions

### Test 1: Subscribe to a Mock Threat Feed

Create a test script `test-threat-feed.ts`:

```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

async function testThreatFeed() {
  const client = new Client(
    { name: 'test-client', version: '1.0.0' },
    { capabilities: {} }
  );

  const transport = new StdioClientTransport({
    command: 'node',
    args: ['dist/index.js'],
  });

  await client.connect(transport);

  try {
    // Subscribe to threat feed
    console.log('Subscribing to threat feed...');
    const subscribeResult = await client.callTool({
      name: 'subscribe_to_threat_feed',
      arguments: {
        feed_name: 'test_malware_feed',
        feed_type: 'yara',
        update_interval_minutes: 5,  // Check every 5 minutes for testing
        enabled: true,
      },
    });
    console.log('Subscribe result:', JSON.stringify(subscribeResult, null, 2));

    // Check feed status
    console.log('\nChecking feed status...');
    const statusResult = await client.callTool({
      name: 'get_threat_feed_status',
      arguments: {},
    });
    console.log('Status result:', JSON.stringify(statusResult, null, 2));

    // Update detection rules manually (simulating feed update)
    console.log('\nUpdating detection rules...');
    const updateResult = await client.callTool({
      name: 'update_detection_rules',
      arguments: {
        rule_type: 'yara',
        rules: [
          {
            name: 'test_malware',
            rule: 'rule TestMalware { strings: $a = "test" condition: $a }',
          },
        ],
        source: 'test_malware_feed',
      },
    });
    console.log('Update result:', JSON.stringify(updateResult, null, 2));
  } finally {
    await client.close();
  }
}

testThreatFeed().catch(console.error);
```

**Run test**:
```bash
npm run build
tsx test-threat-feed.ts
```

### Test 2: Subscribe to Real MCP Threat Feed Server

If you have access to a real threat feed MCP server (e.g., Malware Patrol):

```typescript
const subscribeResult = await client.callTool({
  name: 'subscribe_to_threat_feed',
  arguments: {
    feed_name: 'malware_patrol',
    feed_type: 'yara',
    mcp_server_command: 'npx',
    mcp_server_args: ['-y', '@malwarepatrol/mcp-server'],
    update_interval_minutes: 60,
    enabled: true,
  },
});
```

---

## Step 4: Test Cross-Repo Integrations

### Test ilminate-apex Integration

Create `test-apex-integration.ts`:

```typescript
import { 
  querySecurityAssistant, 
  getCustomerThreats,
  getIntegrationStatus 
} from './src/integrations/apex-integration.js';

async function testApexIntegration() {
  try {
    // Check integration status
    console.log('Checking integration status...');
    const status = await getIntegrationStatus();
    console.log('Integration status:', status);

    // Test Security Assistant query
    console.log('\nQuerying Security Assistant...');
    const response = await querySecurityAssistant(
      'What threats have been detected recently?',
      { customer_id: 'test-customer' }
    );
    console.log('Assistant response:', response);

    // Test getting customer threats
    console.log('\nGetting customer threats...');
    const threats = await getCustomerThreats('test-customer', {
      status: 'new',
      severity: 'high',
      time_range: '7d',
    });
    console.log('Customer threats:', threats);
  } catch (error) {
    console.error('Integration test failed:', error);
  }
}

testApexIntegration();
```

**Run test**:
```bash
tsx test-apex-integration.ts
```

### Test ilminate-portal Integration

Create `test-portal-integration.ts`:

```typescript
import { 
  getPortalThreats, 
  getPortalAnalytics 
} from './src/integrations/portal-integration.js';

async function testPortalIntegration() {
  try {
    // Get threats for portal
    console.log('Getting portal threats...');
    const threats = await getPortalThreats('tenant-123', {
      limit: 10,
      status: 'new',
    });
    console.log('Portal threats:', threats);

    // Get analytics
    console.log('\nGetting portal analytics...');
    const analytics = await getPortalAnalytics('tenant-123', '7d');
    console.log('Analytics:', analytics);
  } catch (error) {
    console.error('Portal integration test failed:', error);
  }
}

testPortalIntegration();
```

### Test ilminate-siem Integration

Create `test-siem-integration.ts`:

```typescript
import { 
  enrichSIEMEvent, 
  querySIEMAlerts,
  sendDetectionToSIEM 
} from './src/integrations/siem-integration.js';

async function testSIEMIntegration() {
  try {
    // Test event enrichment
    console.log('Enriching SIEM event...');
    const event = {
      id: 'event-123',
      timestamp: new Date().toISOString(),
      rule_id: 1001,
      rule_name: 'Suspicious Activity',
      level: 5,
      description: 'Suspicious connection to malicious-domain.com',
      agent_id: '001',
      agent_name: 'test-agent',
      data: { domain: 'malicious-domain.com' },
    };

    const enriched = await enrichSIEMEvent(event, [
      'domain_reputation',
      'mitre_mapping',
    ]);
    console.log('Enriched event:', JSON.stringify(enriched, null, 2));

    // Test querying alerts
    console.log('\nQuerying SIEM alerts...');
    const alerts = await querySIEMAlerts({
      level: 5,
      time_range: '24h',
      limit: 10,
    });
    console.log('Alerts:', alerts);

    // Test sending detection to SIEM
    console.log('\nSending detection to SIEM...');
    const sent = await sendDetectionToSIEM({
      threat_type: 'phishing',
      severity: 'high',
      description: 'Phishing email detected',
      source: 'ilminate-mcp',
      details: { email_id: 'email-123' },
    });
    console.log('Detection sent:', sent);
  } catch (error) {
    console.error('SIEM integration test failed:', error);
  }
}

testSIEMIntegration();
```

---

## Step 5: Add MCP Tools That Expose Cross-Repo Capabilities

### Example: Add "query_security_assistant" MCP Tool

Create `src/tools/query-security-assistant.ts`:

```typescript
import { logger } from '../utils/logger.js';
import { querySecurityAssistant } from '../integrations/apex-integration.js';

interface QuerySecurityAssistantInput {
  query: string;
  context?: any;
}

interface QuerySecurityAssistantOutput {
  response: string;
  context_used?: any;
}

export async function querySecurityAssistantTool(
  input: QuerySecurityAssistantInput
): Promise<QuerySecurityAssistantOutput> {
  logger.info('Querying Security Assistant', { query: input.query });

  try {
    const response = await querySecurityAssistant(input.query, input.context);

    return {
      response,
      context_used: input.context,
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    logger.error('Failed to query Security Assistant', { error });

    return {
      response: `Error: ${errorMessage}`,
    };
  }
}
```

**Register in `src/index.ts`**:

```typescript
import { querySecurityAssistantTool } from './tools/query-security-assistant.js';

// Add to tools list
{
  name: 'query_security_assistant',
  description: 'Query ilminate-apex Security Assistant with context',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'Question or query for the Security Assistant',
      },
      context: {
        type: 'object',
        description: 'Additional context for the query',
      },
    },
    required: ['query'],
  },
}

// Add to switch statement
case 'query_security_assistant':
  result = await querySecurityAssistantTool(args as any);
  break;
```

### Example: Add "get_portal_threats" MCP Tool

Create `src/tools/get-portal-threats.ts`:

```typescript
import { logger } from '../utils/logger.js';
import { getPortalThreats } from '../integrations/portal-integration.js';

interface GetPortalThreatsInput {
  tenant_id: string;
  limit?: number;
  offset?: number;
  status?: string;
  severity?: string;
}

export async function getPortalThreatsTool(
  input: GetPortalThreatsInput
): Promise<any> {
  logger.info('Getting portal threats', { tenant_id: input.tenant_id });

  try {
    const threats = await getPortalThreats(input.tenant_id, {
      limit: input.limit,
      offset: input.offset,
      status: input.status,
      severity: input.severity,
    });

    return {
      threats,
      count: threats.length,
      tenant_id: input.tenant_id,
    };
  } catch (error) {
    logger.error('Failed to get portal threats', { error });
    return {
      threats: [],
      count: 0,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}
```

---

## Step 6: End-to-End Testing

### Create Comprehensive Test Script

Create `test-all-integrations.ts`:

```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

async function testAllIntegrations() {
  const client = new Client(
    { name: 'integration-test', version: '1.0.0' },
    { capabilities: {} }
  );

  const transport = new StdioClientTransport({
    command: 'node',
    args: ['dist/index.js'],
  });

  await client.connect(transport);

  try {
    console.log('=== Testing All Integrations ===\n');

    // 1. Test Detection Engine Status
    console.log('1. Testing Detection Engine Status...');
    const engineStatus = await client.callTool({
      name: 'get_detection_engine_status',
      arguments: {},
    });
    console.log('✓ Detection engines:', engineStatus.content[0].text);

    // 2. Test Threat Feed Subscription
    console.log('\n2. Testing Threat Feed Subscription...');
    const feedSub = await client.callTool({
      name: 'subscribe_to_threat_feed',
      arguments: {
        feed_name: 'test_feed',
        feed_type: 'yara',
        update_interval_minutes: 60,
      },
    });
    console.log('✓ Feed subscription:', feedSub.content[0].text);

    // 3. Test Email Threat Analysis
    console.log('\n3. Testing Email Threat Analysis...');
    const emailAnalysis = await client.callTool({
      name: 'analyze_email_threat',
      arguments: {
        subject: 'Urgent: Action Required',
        sender: 'test@example.com',
        body: 'Please click this link immediately',
      },
    });
    console.log('✓ Email analysis:', emailAnalysis.content[0].text);

    // 4. Test Domain Reputation
    console.log('\n4. Testing Domain Reputation...');
    const domainRep = await client.callTool({
      name: 'check_domain_reputation',
      arguments: {
        domain: 'example.com',
      },
    });
    console.log('✓ Domain reputation:', domainRep.content[0].text);

    // 5. Test Threat Feed Status
    console.log('\n5. Testing Threat Feed Status...');
    const feedStatus = await client.callTool({
      name: 'get_threat_feed_status',
      arguments: {},
    });
    console.log('✓ Feed status:', feedStatus.content[0].text);

    console.log('\n=== All Tests Complete ===');
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await client.close();
  }
}

testAllIntegrations().catch(console.error);
```

**Run**:
```bash
npm run build
tsx test-all-integrations.ts
```

---

## Step 7: Verify Services Are Running

### Health Check Script

Create `check-services.sh`:

```bash
#!/bin/bash

echo "Checking ilminate services..."

# APEX Bridge
echo -n "APEX Bridge: "
curl -s http://localhost:8888/health | grep -q "healthy" && echo "✓" || echo "✗"

# ilminate-apex (if running)
echo -n "ilminate-apex: "
curl -s http://localhost:3000/health 2>/dev/null | grep -q "ok" && echo "✓" || echo "✗ (not running)"

# ilminate-portal (if running)
echo -n "ilminate-portal: "
curl -s http://localhost:3001/health 2>/dev/null | grep -q "ok" && echo "✓" || echo "✗ (not running)"

# ilminate-siem (if running)
echo -n "ilminate-siem: "
curl -s http://localhost:55000/health 2>/dev/null | grep -q "ok" && echo "✓" || echo "✗ (not running)"

echo "Done!"
```

**Run**:
```bash
chmod +x check-services.sh
./check-services.sh
```

---

## Troubleshooting

### Issue: APEX Bridge not starting
- Check Python 3 is installed: `python3 --version`
- Check ilminate-agent path is correct
- Check dependencies: `pip install -r bridge/requirements.txt`

### Issue: MCP server not connecting
- Verify APEX_BRIDGE_URL in .env
- Check bridge is running: `curl http://localhost:8888/health`
- Check logs for connection errors

### Issue: Cross-repo integrations failing
- Verify API URLs in .env match actual service URLs
- Check API keys are correct
- Verify services are running and accessible
- Check network/firewall settings

### Issue: Threat feed subscriptions not working
- Verify MCP server command/args are correct
- Check feed type matches available tools
- Review ThreatFeedManager logs
- Test MCP server connection manually

---

## Next Steps After Testing

1. **Production Configuration**
   - Set `API_KEY_REQUIRED=true`
   - Use secure API keys
   - Enable HTTPS for all services

2. **Monitoring**
   - Set up logging aggregation
   - Monitor threat feed update frequency
   - Track integration health

3. **Scaling**
   - Consider persistent storage for subscriptions
   - Add caching for frequent queries
   - Implement rate limiting

---

**Ready to test!** Start with Step 1 and work through each step systematically.

