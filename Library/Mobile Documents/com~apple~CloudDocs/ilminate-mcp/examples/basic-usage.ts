/**
 * Example: Basic usage of ilminate MCP Server
 * 
 * This demonstrates how to use the MCP server tools programmatically.
 * In practice, MCP servers are typically used via stdio transport with
 * AI assistants like Claude Desktop.
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

async function example() {
  // Create MCP client
  const client = new Client(
    {
      name: 'example-client',
      version: '1.0.0',
    },
    {
      capabilities: {},
    }
  );

  // Connect to ilminate MCP server via stdio
  const transport = new StdioClientTransport({
    command: 'node',
    args: ['dist/index.js'],
  });

  await client.connect(transport);

  try {
    // List available tools
    console.log('Available tools:');
    const tools = await client.listTools();
    tools.tools.forEach((tool) => {
      console.log(`  - ${tool.name}: ${tool.description}`);
    });

    // Example 1: Analyze email threat
    console.log('\n1. Analyzing email threat...');
    const emailAnalysis = await client.callTool({
      name: 'analyze_email_threat',
      arguments: {
        subject: 'Urgent: Action Required',
        sender: 'ceo@company.com',
        body: 'Please wire transfer $50,000 immediately to account 12345',
      },
    });
    console.log('Email Analysis:', JSON.stringify(emailAnalysis, null, 2));

    // Example 2: Map to MITRE ATT&CK
    console.log('\n2. Mapping to MITRE ATT&CK...');
    const mitreMapping = await client.callTool({
      name: 'map_to_mitre_attack',
      arguments: {
        event_text: 'Phishing email with malicious attachment detected',
      },
    });
    console.log('MITRE Mapping:', JSON.stringify(mitreMapping, null, 2));

    // Example 3: Check domain reputation
    console.log('\n3. Checking domain reputation...');
    const domainRep = await client.callTool({
      name: 'check_domain_reputation',
      arguments: {
        domain: 'suspicious-domain.com',
      },
    });
    console.log('Domain Reputation:', JSON.stringify(domainRep, null, 2));

    // Example 4: Get campaign analysis
    console.log('\n4. Getting campaign analysis...');
    const campaign = await client.callTool({
      name: 'get_campaign_analysis',
      arguments: {
        campaign_name: 'Example Campaign',
        time_range: '7d',
      },
    });
    console.log('Campaign Analysis:', JSON.stringify(campaign, null, 2));

    // Example 5: Scan image for threats
    console.log('\n5. Scanning image for threats...');
    const imageScan = await client.callTool({
      name: 'scan_image_for_threats',
      arguments: {
        image_url: 'https://example.com/suspicious-image.png',
        message_context: {
          subject: 'Verify your account',
          sender: 'security@example.com',
        },
      },
    });
    console.log('Image Scan:', JSON.stringify(imageScan, null, 2));
  } finally {
    await client.close();
  }
}

// Run example
example().catch((error) => {
  console.error('Example failed:', error);
  process.exit(1);
});

