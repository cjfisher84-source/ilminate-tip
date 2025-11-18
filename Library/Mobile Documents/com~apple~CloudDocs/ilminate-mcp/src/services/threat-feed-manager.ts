/**
 * Threat Feed Manager
 * 
 * Manages subscriptions to threat intelligence feeds via MCP
 * and handles detection engine updates.
 */

import { logger } from '../utils/logger.js';
import { MCPClient } from '../client/mcp-client.js';

export interface ThreatFeed {
  name: string;
  type: 'ioc' | 'yara' | 'domain' | 'ip' | 'url' | 'signature';
  mcp_server_url?: string;
  mcp_server_command?: string;
  mcp_server_args?: string[];
  enabled: boolean;
  last_update?: Date;
  update_interval_minutes: number;
}

export interface ThreatFeedUpdate {
  feed_name: string;
  update_type: 'new_ioc' | 'updated_ioc' | 'expired_ioc' | 'yara_rule' | 'signature';
  data: any;
  timestamp: Date;
}

export interface ThreatFeedSubscription {
  feed: ThreatFeed;
  client?: MCPClient;
  callback?: (update: ThreatFeedUpdate) => Promise<void>;
  last_check?: Date;
}

class ThreatFeedManager {
  private subscriptions: Map<string, ThreatFeedSubscription> = new Map();
  private updateCallbacks: Map<string, (update: ThreatFeedUpdate) => Promise<void>> = new Map();

  /**
   * Subscribe to a threat intelligence feed
   */
  async subscribe(
    feed: ThreatFeed,
    callback?: (update: ThreatFeedUpdate) => Promise<void>
  ): Promise<void> {
    logger.info(`Subscribing to threat feed: ${feed.name}`);

    try {
      let client: MCPClient | undefined;

      // Create MCP client if MCP server info provided
      if (feed.mcp_server_command) {
        client = new MCPClient(feed.mcp_server_command, feed.mcp_server_args);
        await client.connect();
        logger.info(`Connected to MCP server for feed: ${feed.name}`);
      }

      const subscription: ThreatFeedSubscription = {
        feed,
        client,
        callback,
        last_check: new Date(),
      };

      this.subscriptions.set(feed.name, subscription);

      if (callback) {
        this.updateCallbacks.set(feed.name, callback);
      }

      // Start polling for updates
      this.startPolling(feed.name);

      logger.info(`Successfully subscribed to threat feed: ${feed.name}`);
    } catch (error) {
      logger.error(`Failed to subscribe to threat feed ${feed.name}`, { error });
      throw error;
    }
  }

  /**
   * Unsubscribe from a threat feed
   */
  async unsubscribe(feedName: string): Promise<void> {
    logger.info(`Unsubscribing from threat feed: ${feedName}`);

    const subscription = this.subscriptions.get(feedName);
    if (subscription?.client) {
      await subscription.client.disconnect();
    }

    this.subscriptions.delete(feedName);
    this.updateCallbacks.delete(feedName);

    logger.info(`Unsubscribed from threat feed: ${feedName}`);
  }

  /**
   * Start polling a threat feed for updates
   */
  private startPolling(feedName: string): void {
    const subscription = this.subscriptions.get(feedName);
    if (!subscription) {
      return;
    }

    const { feed } = subscription;
    const intervalMs = feed.update_interval_minutes * 60 * 1000;

    // Initial check
    this.checkForUpdates(feedName);

    // Set up polling interval
    setInterval(() => {
      this.checkForUpdates(feedName);
    }, intervalMs);
  }

  /**
   * Check for updates from a threat feed
   */
  private async checkForUpdates(feedName: string): Promise<void> {
    const subscription = this.subscriptions.get(feedName);
    if (!subscription || !subscription.feed.enabled) {
      return;
    }

    try {
      logger.debug(`Checking for updates from feed: ${feedName}`);

      // If MCP client available, query for updates
      if (subscription.client) {
        const updates = await this.queryMCPFeed(subscription);
        for (const update of updates) {
          await this.handleUpdate(feedName, update);
        }
      } else {
        // Fallback: Use HTTP API or other method
        logger.warn(`No MCP client for feed ${feedName}, skipping update check`);
      }

      subscription.last_check = new Date();
      subscription.feed.last_update = new Date();
    } catch (error) {
      logger.error(`Error checking for updates from feed ${feedName}`, { error });
    }
  }

  /**
   * Query MCP feed for updates
   */
  private async queryMCPFeed(
    subscription: ThreatFeedSubscription
  ): Promise<ThreatFeedUpdate[]> {
    const { feed, client } = subscription;
    if (!client) {
      return [];
    }

    try {
      // Try to call MCP tool for threat feed updates
      // Tool name depends on feed type
      const toolName = this.getToolNameForFeedType(feed.type);

      const result = await client.callTool(toolName, {
        feed_name: feed.name,
        since: subscription.last_check?.toISOString() || new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      });

      // Transform MCP result to ThreatFeedUpdate format
      const updates: ThreatFeedUpdate[] = [];
      if (result.updates && Array.isArray(result.updates)) {
        for (const updateData of result.updates) {
          updates.push({
            feed_name: feed.name,
            update_type: updateData.type || 'new_ioc',
            data: updateData,
            timestamp: new Date(updateData.timestamp || Date.now()),
          });
        }
      }

      return updates;
    } catch (error) {
      logger.error(`Error querying MCP feed ${feed.name}`, { error });
      return [];
    }
  }

  /**
   * Get MCP tool name for feed type
   */
  private getToolNameForFeedType(type: string): string {
    const toolMap: Record<string, string> = {
      ioc: 'get_ioc_updates',
      yara: 'get_yara_rule_updates',
      domain: 'get_domain_updates',
      ip: 'get_ip_updates',
      url: 'get_url_updates',
      signature: 'get_signature_updates',
    };

    return toolMap[type] || 'get_threat_updates';
  }

  /**
   * Handle a threat feed update
   */
  private async handleUpdate(
    feedName: string,
    update: ThreatFeedUpdate
  ): Promise<void> {
    logger.info(`Received update from feed ${feedName}: ${update.update_type}`);

    // Call registered callback
    const callback = this.updateCallbacks.get(feedName);
    if (callback) {
      try {
        await callback(update);
      } catch (error) {
        logger.error(`Error in callback for feed ${feedName}`, { error });
      }
    }

    // Default handling: Update detection engines
    await this.updateDetectionEngines(update);
  }

  /**
   * Update detection engines with threat feed data
   */
  private async updateDetectionEngines(update: ThreatFeedUpdate): Promise<void> {
    try {
      switch (update.update_type) {
        case 'yara_rule':
          await this.updateYaraRules(update);
          break;
        case 'new_ioc':
        case 'updated_ioc':
          await this.updateIOCDatabase(update);
          break;
        case 'signature':
          await this.updateSignatures(update);
          break;
        default:
          logger.debug(`No specific handler for update type: ${update.update_type}`);
      }
    } catch (error) {
      logger.error('Error updating detection engines', { error, update });
    }
  }

  /**
   * Update YARA rules
   */
  private async updateYaraRules(update: ThreatFeedUpdate): Promise<void> {
    logger.info(`Updating YARA rules from feed: ${update.feed_name}`);

    // Call APEX Bridge to update YARA rules
    try {
      const response = await fetch(
        `${process.env.APEX_BRIDGE_URL || 'http://localhost:8888'}/api/update-yara-rules`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            rules: update.data.rules || [],
            source: update.feed_name,
          }),
        }
      );

      if (response.ok) {
        logger.info(`Successfully updated YARA rules from ${update.feed_name}`);
      } else {
        logger.error(`Failed to update YARA rules: ${response.statusText}`);
      }
    } catch (error) {
      logger.error('Error updating YARA rules via APEX Bridge', { error });
    }
  }

  /**
   * Update IOC database
   */
  private async updateIOCDatabase(update: ThreatFeedUpdate): Promise<void> {
    logger.info(`Updating IOC database from feed: ${update.feed_name}`);

    // Store IOCs in database or cache
    // This would integrate with ilminate-agent's IOC storage
    const iocs = update.data.iocs || [];
    logger.info(`Received ${iocs.length} IOCs from ${update.feed_name}`);

    // TODO: Store IOCs in DynamoDB or cache
    // This would be integrated with ilminate-infrastructure or ilminate-agent
  }

  /**
   * Update signatures
   */
  private async updateSignatures(update: ThreatFeedUpdate): Promise<void> {
    logger.info(`Updating signatures from feed: ${update.feed_name}`);

    // Update ClamAV or other signature databases
    // This would integrate with ilminate-agent's signature management
  }

  /**
   * Get all active subscriptions
   */
  getSubscriptions(): ThreatFeedSubscription[] {
    return Array.from(this.subscriptions.values());
  }

  /**
   * Get subscription by name
   */
  getSubscription(feedName: string): ThreatFeedSubscription | undefined {
    return this.subscriptions.get(feedName);
  }
}

// Singleton instance
export const threatFeedManager = new ThreatFeedManager();

