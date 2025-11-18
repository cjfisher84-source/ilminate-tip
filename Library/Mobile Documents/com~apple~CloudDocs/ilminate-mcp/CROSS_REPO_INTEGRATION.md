# Cross-Repo Integration Plan

**Goal**: Make ilminate-mcp the central integration hub for all ilminate services

---

## 🎯 Vision

ilminate-mcp should:
1. **Know about** all ilminate-* repositories
2. **Integrate with** all ilminate services
3. **Expose** unified capabilities via MCP
4. **Enable** cross-service communication
5. **Provide** threat intelligence aggregation

---

## 📦 ilminate Ecosystem Repositories

### ✅ **ilminate-agent** (INTEGRATED)
**Status**: ✅ Fully integrated via APEX Bridge  
**Purpose**: Detection engines, multi-layer threat detection  
**Integration**: Direct via Python bridge service  
**MCP Tools**: All detection tools use this

### 🔄 **ilminate-apex** (IN PROGRESS)
**Status**: 🔄 Integration planned  
**Purpose**: Security Assistant, API endpoints, customer portal backend  
**Integration Points**:
- Security Assistant can use MCP client to call detection engines
- MCP server can expose apex-specific tools
- API endpoints can be accessed via MCP

**Planned MCP Tools**:
- `query_security_assistant` - Query AI assistant with context
- `get_customer_threats` - Get threats for specific customer
- `update_threat_status` - Update threat status in apex

### 📋 **ilminate-portal** (TO INTEGRATE)
**Status**: 📋 Planned  
**Purpose**: Customer-facing portal, threat dashboard  
**Integration Points**:
- Portal can query MCP server for threat data
- MCP can expose portal-specific capabilities
- Real-time threat updates via MCP

**Planned MCP Tools**:
- `get_portal_threats` - Get threats for portal display
- `update_portal_settings` - Update customer settings
- `get_portal_analytics` - Get analytics for dashboard

### 🛡️ **ilminate-siem** (TO INTEGRATE)
**Status**: 📋 Planned  
**Purpose**: Wazuh SIEM, log aggregation, alert management  
**Integration Points**:
- SIEM events can be enriched via MCP
- MCP can query SIEM for threat context
- Detection engines can send events to SIEM via MCP

**Planned MCP Tools**:
- `enrich_siem_event` - Add threat intelligence to SIEM events
- `query_siem_alerts` - Query SIEM for alerts
- `send_detection_to_siem` - Send detection events to SIEM

### 📧 **ilminate-email** (TO INTEGRATE)
**Status**: 📋 Planned  
**Purpose**: Email processing, mailbox protection, email scanning  
**Integration Points**:
- Email analysis can use MCP detection engines
- MCP can expose email-specific capabilities
- Email threats can be shared via MCP

**Planned MCP Tools**:
- `analyze_email_message` - Analyze email using detection engines
- `get_email_threats` - Get email-specific threats
- `quarantine_email` - Quarantine email via MCP

### 🧪 **ilminate-sandbox** (TO INTEGRATE)
**Status**: 📋 Planned  
**Purpose**: Sandbox analysis, file detonation, dynamic analysis  
**Integration Points**:
- Sandbox analysis can be exposed as MCP tool
- Detection engines can trigger sandbox analysis
- Sandbox results can enrich detections

**Planned MCP Tools**:
- `analyze_file_in_sandbox` - Submit file for sandbox analysis
- `get_sandbox_results` - Get sandbox analysis results
- `check_file_reputation` - Check file reputation via sandbox

### ☁️ **ilminate-infrastructure** (TO INTEGRATE)
**Status**: 📋 Planned  
**Purpose**: AWS infrastructure, Lambda functions, deployment  
**Integration Points**:
- Infrastructure status can be queried via MCP
- MCP can trigger infrastructure actions
- Infrastructure metrics can be exposed

**Planned MCP Tools**:
- `get_infrastructure_status` - Get AWS infrastructure status
- `get_lambda_metrics` - Get Lambda function metrics
- `trigger_deployment` - Trigger infrastructure deployment

### 🔐 **ilminate-sso-aws** (TO INTEGRATE)
**Status**: 📋 Planned  
**Purpose**: Single Sign-On, authentication  
**Integration Points**:
- MCP can verify authentication tokens
- SSO can be used for MCP authentication
- User context can be passed via MCP

**Planned MCP Tools**:
- `verify_auth_token` - Verify authentication token
- `get_user_context` - Get user context from SSO

### 🌐 **ilminate** (TO INTEGRATE)
**Status**: 📋 Planned  
**Purpose**: Marketing website  
**Integration Points**:
- Website can display threat intelligence via MCP
- MCP can expose public threat data
- Blog posts can reference MCP threat data

**Planned MCP Tools**:
- `get_public_threat_stats` - Get public threat statistics
- `get_threat_intelligence_feed` - Get threat intelligence for website

---

## 🔌 Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ilminate Ecosystem                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ ilminate-    │  │ ilminate-    │  │ ilminate-    │    │
│  │ apex         │  │ portal       │  │ siem         │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                  │            │
│  ┌──────▼─────────────────▼──────────────────▼───────┐    │
│  │         ilminate-mcp (Central Hub)                │    │
│  │  - Unified MCP Interface                          │    │
│  │  - Cross-service Communication                    │    │
│  │  - Threat Intelligence Aggregation               │    │
│  └──────┬─────────────────┬──────────────────┬───────┘    │
│         │                 │                  │            │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐    │
│  │ ilminate-    │  │ ilminate-    │  │ ilminate-    │    │
│  │ agent        │  │ email        │  │ sandbox      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Implementation Plan

### Phase 1: Discovery & Mapping (Week 1)
- [ ] Document each repo's APIs and capabilities
- [ ] Create integration matrix
- [ ] Identify authentication mechanisms
- [ ] Map data flows between services

### Phase 2: Core Integrations (Weeks 2-4)
- [ ] **ilminate-apex**: Security Assistant MCP client
- [ ] **ilminate-portal**: Threat data queries
- [ ] **ilminate-siem**: Event enrichment
- [ ] **ilminate-email**: Email analysis integration

### Phase 3: Advanced Integrations (Weeks 5-8)
- [ ] **ilminate-sandbox**: Sandbox analysis tools
- [ ] **ilminate-infrastructure**: Status and metrics
- [ ] **ilminate-sso-aws**: Authentication integration
- [ ] **ilminate**: Public threat data

### Phase 4: Unified Ecosystem (Weeks 9-12)
- [ ] Service discovery mechanism
- [ ] Cross-service communication
- [ ] Unified monitoring
- [ ] Threat intelligence aggregation

---

## 📝 Integration Details

### ilminate-apex Integration

**MCP Client Integration**:
```typescript
// In ilminate-apex Security Assistant
import { MCPClient } from '@ilminate/mcp-client';

const mcpClient = new MCPClient({
  serverUrl: 'http://localhost:3000/mcp'
});

// Use in Security Assistant
async function analyzeThreat(emailData) {
  // Query detection engines via MCP
  const detection = await mcpClient.callTool('analyze_email_threat', {
    subject: emailData.subject,
    sender: emailData.sender,
    body: emailData.body
  });
  
  // Enrich with external threat intel
  const domainRep = await mcpClient.callTool('check_domain_reputation', {
    domain: emailData.senderDomain
  });
  
  return { detection, domainRep };
}
```

**New MCP Tools to Add**:
- `query_security_assistant` - Query AI assistant
- `get_customer_threats` - Customer-specific threats
- `update_threat_status` - Update threat status

### ilminate-portal Integration

**Portal MCP Integration**:
```typescript
// In ilminate-portal frontend
const threats = await fetch('/api/mcp/threats', {
  method: 'POST',
  body: JSON.stringify({
    tool: 'get_portal_threats',
    args: { tenant_id: 'acme', time_range: '7d' }
  })
});
```

**New MCP Tools to Add**:
- `get_portal_threats` - Get threats for portal
- `update_portal_settings` - Update settings
- `get_portal_analytics` - Get analytics

### ilminate-siem Integration

**SIEM Event Enrichment**:
```typescript
// Enrich SIEM events with threat intelligence
const enrichedEvent = await mcpClient.callTool('enrich_siem_event', {
  event: siemEvent,
  enrichments: ['domain_reputation', 'threat_intelligence', 'mitre_mapping']
});
```

**New MCP Tools to Add**:
- `enrich_siem_event` - Enrich SIEM events
- `query_siem_alerts` - Query SIEM
- `send_detection_to_siem` - Send to SIEM

---

## 🔄 Threat Feed Integration via MCP

### Current State
- MCP server can **consume** threat intelligence
- Detection engines can be **queried** via MCP

### Planned Enhancements

#### 1. Threat Feed Subscriptions
```typescript
// Subscribe to threat feed updates
await mcpClient.callTool('subscribe_to_threat_feed', {
  feed_name: 'malware_patrol',
  feed_type: 'ioc',
  update_types: ['new_ioc', 'updated_ioc', 'expired_ioc']
});
```

#### 2. Detection Engine Updates
```typescript
// Update detection rules from threat feed
await mcpClient.callTool('update_detection_rules', {
  rule_type: 'yara',
  rules: newYaraRules,
  source: 'malware_patrol_mcp'
});
```

#### 3. Threat Intelligence Aggregation
```typescript
// Aggregate threat intelligence from multiple sources
const aggregatedIntel = await mcpClient.callTool('aggregate_threat_intel', {
  domain: 'suspicious-domain.com',
  sources: ['malware_patrol', 'virustotal', 'abuseipdb']
});
```

---

## 📊 Service Discovery

### Registry System
Create a service registry that all ilminate services can use:

```typescript
// Service registry
interface IlminateService {
  name: string;
  type: 'detection' | 'portal' | 'siem' | 'email' | 'infrastructure';
  mcp_endpoint: string;
  capabilities: string[];
  status: 'active' | 'inactive';
}

// Query available services
const services = await mcpClient.callTool('discover_services', {
  type: 'detection',
  capabilities: ['email_analysis', 'threat_detection']
});
```

---

## 🎯 Next Steps

1. **This Week**: Complete ilminate-apex Security Assistant integration
2. **Next Week**: Add ilminate-portal integration
3. **This Month**: Complete ilminate-siem and ilminate-email integrations
4. **Next Month**: Add threat feed subscriptions and detection engine updates

---

**Status**: Foundation complete, ready for cross-repo integration

