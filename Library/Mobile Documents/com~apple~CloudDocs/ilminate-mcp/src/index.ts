#!/usr/bin/env node

/**
 * ilminate MCP Server
 * 
 * Exposes ilminate detection engines as MCP tools for AI assistants
 * and external security platforms.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';

import { analyzeEmailThreat } from './tools/analyze-email-threat.js';
import { mapToMitreAttack } from './tools/map-to-mitre-attack.js';
import { checkDomainReputation } from './tools/check-domain-reputation.js';
import { getCampaignAnalysis } from './tools/get-campaign-analysis.js';
import { scanImageForThreats } from './tools/scan-image-for-threats.js';
import { getDetectionEngineStatus } from './tools/get-detection-engine-status.js';
import { subscribeToThreatFeed } from './tools/subscribe-to-threat-feed.js';
import { updateDetectionRules } from './tools/update-detection-rules.js';
import { getThreatFeedStatus } from './tools/get-threat-feed-status.js';
import { querySecurityAssistantTool } from './tools/query-security-assistant.js';
import { getPortalThreatsTool } from './tools/get-portal-threats.js';
import { enrichSIEMEventTool } from './tools/enrich-siem-event.js';
import { explainDetectionResult } from './tools/explain-detection-result.js';
import { investigateSuspiciousIndicator } from './tools/investigate-suspicious-indicator.js';
import { getDetectionBreakdown } from './tools/get-detection-breakdown.js';
import { authenticateRequest } from './auth.js';
import { logger } from './utils/logger.js';

// Load environment variables
dotenv.config();

const SERVER_NAME = 'ilminate-mcp';
const SERVER_VERSION = '1.0.0';

/**
 * Initialize and start the MCP server
 */
async function main() {
  // Create MCP server instance
  const server = new Server(
    {
      name: SERVER_NAME,
      version: SERVER_VERSION,
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // List available tools
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    const tools: Tool[] = [
      {
        name: 'analyze_email_threat',
        description:
          'Analyze email for BEC/phishing indicators using ilminate triage analysis',
        inputSchema: {
          type: 'object',
          properties: {
            subject: {
              type: 'string',
              description: 'Email subject line',
            },
            sender: {
              type: 'string',
              description: 'Email sender address',
            },
            body: {
              type: 'string',
              description: 'Email body content',
            },
            attachments: {
              type: 'array',
              items: { type: 'string' },
              description: 'List of attachment filenames',
            },
          },
          required: ['subject', 'sender', 'body'],
        },
      },
      {
        name: 'map_to_mitre_attack',
        description: 'Map security event to MITRE ATT&CK techniques',
        inputSchema: {
          type: 'object',
          properties: {
            event_text: {
              type: 'string',
              description: 'Security event text to analyze',
            },
          },
          required: ['event_text'],
        },
      },
      {
        name: 'check_domain_reputation',
        description: 'Check domain reputation and threat intelligence',
        inputSchema: {
          type: 'object',
          properties: {
            domain: {
              type: 'string',
              description: 'Domain name to check',
            },
          },
          required: ['domain'],
        },
      },
      {
        name: 'get_campaign_analysis',
        description: 'Get analysis of active threat campaigns',
        inputSchema: {
          type: 'object',
          properties: {
            campaign_name: {
              type: 'string',
              description: 'Name of the campaign to analyze',
            },
            time_range: {
              type: 'string',
              description: 'Time range for analysis (e.g., "7d", "30d")',
              default: '7d',
            },
          },
          required: ['campaign_name'],
        },
      },
      {
        name: 'scan_image_for_threats',
        description:
          'Analyze image for QR codes, logo impersonation, hidden links',
        inputSchema: {
          type: 'object',
          properties: {
            image_url: {
              type: 'string',
              description: 'URL of the image to scan',
            },
            message_context: {
              type: 'object',
              description: 'Context about the message containing the image',
              properties: {
                subject: { type: 'string' },
                sender: { type: 'string' },
              },
            },
          },
          required: ['image_url'],
        },
      },
      {
        name: 'get_detection_engine_status',
        description:
          'Get status and capabilities of ilminate detection engines',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'subscribe_to_threat_feed',
        description:
          'Subscribe to threat intelligence feed updates via MCP',
        inputSchema: {
          type: 'object',
          properties: {
            feed_name: {
              type: 'string',
              description: 'Name of the threat feed',
            },
            feed_type: {
              type: 'string',
              enum: ['ioc', 'yara', 'domain', 'ip', 'url', 'signature'],
              description: 'Type of threat feed',
            },
            mcp_server_url: {
              type: 'string',
              description: 'URL of MCP server (if HTTP-based)',
            },
            mcp_server_command: {
              type: 'string',
              description: 'Command to run MCP server (if stdio-based)',
            },
            mcp_server_args: {
              type: 'array',
              items: { type: 'string' },
              description: 'Arguments for MCP server command',
            },
            update_interval_minutes: {
              type: 'number',
              description: 'How often to check for updates (minutes)',
              default: 60,
            },
            enabled: {
              type: 'boolean',
              description: 'Whether the feed is enabled',
              default: true,
            },
          },
          required: ['feed_name', 'feed_type'],
        },
      },
      {
        name: 'update_detection_rules',
        description:
          'Update detection engine rules from threat feed updates',
        inputSchema: {
          type: 'object',
          properties: {
            rule_type: {
              type: 'string',
              enum: ['yara', 'signature', 'pattern', 'ioc'],
              description: 'Type of rules to update',
            },
            rules: {
              type: 'array',
              description: 'Rules to update',
            },
            source: {
              type: 'string',
              description: 'Source of the rules (feed name)',
            },
            force_update: {
              type: 'boolean',
              description: 'Force update even if rules exist',
              default: false,
            },
          },
          required: ['rule_type', 'rules', 'source'],
        },
      },
      {
        name: 'get_threat_feed_status',
        description: 'Get status of threat feed subscriptions',
        inputSchema: {
          type: 'object',
          properties: {
            feed_name: {
              type: 'string',
              description: 'Specific feed name (optional, returns all if omitted)',
            },
          },
        },
      },
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
      },
      {
        name: 'get_portal_threats',
        description: 'Get threats for ilminate-portal display',
        inputSchema: {
          type: 'object',
          properties: {
            tenant_id: {
              type: 'string',
              description: 'Tenant ID',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of threats to return',
            },
            offset: {
              type: 'number',
              description: 'Offset for pagination',
            },
            status: {
              type: 'string',
              description: 'Filter by threat status',
            },
            severity: {
              type: 'string',
              description: 'Filter by threat severity',
            },
          },
          required: ['tenant_id'],
        },
      },
      {
        name: 'enrich_siem_event',
        description: 'Enrich SIEM events with threat intelligence',
        inputSchema: {
          type: 'object',
          properties: {
            event: {
              type: 'object',
              description: 'SIEM event to enrich',
            },
            enrichments: {
              type: 'array',
              items: { type: 'string' },
              description: 'Types of enrichments to apply',
            },
          },
          required: ['event'],
        },
      },
      {
        name: 'explain_detection_result',
        description: 'Explains why an email was flagged as malicious or suspicious. Provides detailed breakdown of indicators, detection layers, and reasoning. Use this when you need to understand WHY something was detected.',
        inputSchema: {
          type: 'object',
          properties: {
            subject: {
              type: 'string',
              description: 'Email subject line',
            },
            sender: {
              type: 'string',
              description: 'Email sender address',
            },
            body: {
              type: 'string',
              description: 'Email body content',
            },
            message_id: {
              type: 'string',
              description: 'Optional message ID if available',
            },
            verdict_data: {
              type: 'object',
              description: 'Optional verdict data from previous analysis',
            },
          },
          required: ['subject', 'sender', 'body'],
        },
      },
      {
        name: 'investigate_suspicious_indicator',
        description: 'Performs lightweight, fast checks on specific suspicious indicators when there is doubt. Designed to be non-resource-intensive and quick. Use this to investigate specific indicators like domains, URLs, or content patterns.',
        inputSchema: {
          type: 'object',
          properties: {
            indicator_type: {
              type: 'string',
              enum: ['sender', 'domain', 'url', 'attachment', 'content_pattern', 'other'],
              description: 'Type of indicator to investigate',
            },
            indicator_value: {
              type: 'string',
              description: 'The actual indicator value to investigate (e.g., domain name, URL, attachment filename)',
            },
            context: {
              type: 'object',
              description: 'Optional context about the email (subject, sender, risk_score)',
            },
          },
          required: ['indicator_type', 'indicator_value'],
        },
      },
      {
        name: 'get_detection_breakdown',
        description: 'Provides detailed breakdown of which detection layers triggered and why. Shows the detection pipeline results for transparency. Use this to understand the complete detection process.',
        inputSchema: {
          type: 'object',
          properties: {
            subject: {
              type: 'string',
              description: 'Email subject line',
            },
            sender: {
              type: 'string',
              description: 'Email sender address',
            },
            body: {
              type: 'string',
              description: 'Email body content',
            },
            message_id: {
              type: 'string',
              description: 'Optional message ID',
            },
            attachments: {
              type: 'array',
              items: { type: 'string' },
              description: 'List of attachment filenames',
            },
          },
          required: ['subject', 'sender', 'body'],
        },
      },
    ];

    return { tools };
  });

  // Handle tool execution requests
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    // Authenticate request (if API key is required)
    if (process.env.MCP_REQUIRE_AUTH === 'true') {
      const authResult = await authenticateRequest(request);
      if (!authResult.authenticated) {
        throw new Error(`Authentication failed: ${authResult.error}`);
      }
    }

    logger.info(`Tool call: ${name}`, { args });

    try {
      let result;

      switch (name) {
        case 'analyze_email_threat':
          result = await analyzeEmailThreat(args as any);
          break;

        case 'map_to_mitre_attack':
          result = await mapToMitreAttack(args as any);
          break;

        case 'check_domain_reputation':
          result = await checkDomainReputation(args as any);
          break;

        case 'get_campaign_analysis':
          result = await getCampaignAnalysis(args as any);
          break;

        case 'scan_image_for_threats':
          result = await scanImageForThreats(args as any);
          break;

        case 'get_detection_engine_status':
          result = await getDetectionEngineStatus();
          break;

        case 'subscribe_to_threat_feed':
          result = await subscribeToThreatFeed(args as any);
          break;

        case 'update_detection_rules':
          result = await updateDetectionRules(args as any);
          break;

        case 'get_threat_feed_status':
          result = await getThreatFeedStatus(args as any);
          break;

        case 'query_security_assistant':
          result = await querySecurityAssistantTool(args as any);
          break;

        case 'get_portal_threats':
          result = await getPortalThreatsTool(args as any);
          break;

        case 'enrich_siem_event':
          result = await enrichSIEMEventTool(args as any);
          break;

        case 'explain_detection_result':
          result = await explainDetectionResult(args as any);
          break;

        case 'investigate_suspicious_indicator':
          result = await investigateSuspiciousIndicator(args as any);
          break;

        case 'get_detection_breakdown':
          result = await getDetectionBreakdown(args as any);
          break;

        default:
          throw new Error(`Unknown tool: ${name}`);
      }

      logger.info(`Tool ${name} completed successfully`);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error';
      logger.error(`Tool ${name} failed: ${errorMessage}`, { error });

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                error: errorMessage,
                tool: name,
              },
              null,
              2
            ),
          },
        ],
        isError: true,
      };
    }
  });

  // Connect to stdio transport (standard for MCP servers)
  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info(`${SERVER_NAME} v${SERVER_VERSION} started`);
}

// Start the server
main().catch((error) => {
  logger.error('Failed to start server', { error });
  process.exit(1);
});

