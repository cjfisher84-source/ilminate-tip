/**
 * subscribe_to_threat_feed tool
 * 
 * Subscribe to threat intelligence feed updates via MCP.
 */

import { logger } from '../utils/logger.js';
import { threatFeedManager, ThreatFeed } from '../services/threat-feed-manager.js';

interface SubscribeToThreatFeedInput {
  feed_name: string;
  feed_type: 'ioc' | 'yara' | 'domain' | 'ip' | 'url' | 'signature';
  mcp_server_url?: string;
  mcp_server_command?: string;
  mcp_server_args?: string[];
  update_interval_minutes?: number;
  enabled?: boolean;
}

interface SubscribeToThreatFeedOutput {
  success: boolean;
  feed_name: string;
  subscription_id: string;
  message: string;
}

/**
 * Subscribe to a threat intelligence feed
 */
export async function subscribeToThreatFeed(
  input: SubscribeToThreatFeedInput
): Promise<SubscribeToThreatFeedOutput> {
  logger.info('Subscribing to threat feed', { input });

  try {
    const feed: ThreatFeed = {
      name: input.feed_name,
      type: input.feed_type,
      mcp_server_url: input.mcp_server_url,
      mcp_server_command: input.mcp_server_command,
      mcp_server_args: input.mcp_server_args,
      enabled: input.enabled !== false,
      update_interval_minutes: input.update_interval_minutes || 60,
    };

    // Subscribe with callback to handle updates
    await threatFeedManager.subscribe(feed, async (update) => {
      logger.info(`Received update from ${feed.name}`, {
        update_type: update.update_type,
        timestamp: update.timestamp,
      });

      // Updates are automatically handled by ThreatFeedManager
      // which calls updateDetectionEngines()
    });

    return {
      success: true,
      feed_name: feed.name,
      subscription_id: feed.name, // Use feed name as subscription ID
      message: `Successfully subscribed to threat feed: ${feed.name}`,
    };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error';
    logger.error('Failed to subscribe to threat feed', { error, input });

    return {
      success: false,
      feed_name: input.feed_name,
      subscription_id: '',
      message: `Failed to subscribe: ${errorMessage}`,
    };
  }
}

