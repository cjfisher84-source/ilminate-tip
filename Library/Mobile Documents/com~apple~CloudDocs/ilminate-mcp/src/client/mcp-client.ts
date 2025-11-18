/**
 * MCP Client for Phase 1 Integration
 * 
 * This client can be used by ilminate-apex Security Assistant to connect
 * to external threat intelligence MCP servers.
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { logger } from '../utils/logger.js';

/**
 * MCP Client wrapper for connecting to external MCP servers
 */
export class MCPClient {
  private client: Client;
  private transport: StdioClientTransport;
  private connected: boolean = false;

  constructor(
    private serverCommand: string,
    private serverArgs?: string[]
  ) {
    this.client = new Client(
      {
        name: 'ilminate-mcp-client',
        version: '1.0.0',
      },
      {
        capabilities: {},
      }
    );

    this.transport = new StdioClientTransport({
      command: this.serverCommand,
      args: this.serverArgs || [],
    });
  }

  /**
   * Connect to MCP server
   */
  async connect(): Promise<void> {
    if (this.connected) {
      return;
    }

    try {
      await this.client.connect(this.transport);
      this.connected = true;
      logger.info('Connected to MCP server', {
        command: this.serverCommand,
      });
    } catch (error) {
      logger.error('Failed to connect to MCP server', { error });
      throw error;
    }
  }

  /**
   * Disconnect from MCP server
   */
  async disconnect(): Promise<void> {
    if (!this.connected) {
      return;
    }

    try {
      await this.client.close();
      this.connected = false;
      logger.info('Disconnected from MCP server');
    } catch (error) {
      logger.error('Error disconnecting from MCP server', { error });
    }
  }

  /**
   * List available tools from MCP server
   */
  async listTools(): Promise<any[]> {
    if (!this.connected) {
      await this.connect();
    }

    const response = await this.client.listTools();
    return response.tools || [];
  }

  /**
   * Call a tool on the MCP server
   */
  async callTool(toolName: string, args: any): Promise<any> {
    if (!this.connected) {
      await this.connect();
    }

    try {
      const response = await this.client.callTool({
        name: toolName,
        arguments: args,
      });

      // Extract text content from response
      if (response.content && Array.isArray(response.content) && response.content.length > 0) {
        const textContent = response.content.find((c: any) => c.type === 'text');
        if (textContent && 'text' in textContent) {
          return JSON.parse(textContent.text);
        }
      }

      return response;
    } catch (error) {
      logger.error(`Failed to call tool ${toolName}`, { error, args });
      throw error;
    }
  }
}

/**
 * Create MCP client for threat intelligence server
 */
export function createThreatIntelClient(
  serverUrl?: string
): MCPClient | null {
  // Example: Connect to Malware Patrol MCP server
  // In production, this would be configured via environment variables
  const command = process.env.MALWARE_PATROL_MCP_COMMAND || 'npx';
  const args = process.env.MALWARE_PATROL_MCP_ARGS
    ? process.env.MALWARE_PATROL_MCP_ARGS.split(' ')
    : ['-y', '@malwarepatrol/mcp-server'];

  if (!serverUrl && !command) {
    logger.warn('No threat intelligence MCP server configured');
    return null;
  }

  return new MCPClient(command, args);
}

