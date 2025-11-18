/**
 * get_threat_feed_status tool
 * 
 * Get status of threat feed subscriptions.
 */

import { logger } from '../utils/logger.js';
import { threatFeedManager } from '../services/threat-feed-manager.js';

interface GetThreatFeedStatusInput {
  feed_name?: string;
}

interface ThreatFeedStatus {
  feed_name: string;
  feed_type: string;
  enabled: boolean;
  last_update?: string;
  next_check?: string;
  update_interval_minutes: number;
  status: 'active' | 'inactive' | 'error';
}

interface GetThreatFeedStatusOutput {
  feeds: ThreatFeedStatus[];
  total_feeds: number;
  active_feeds: number;
}

/**
 * Get threat feed subscription status
 */
export async function getThreatFeedStatus(
  input?: GetThreatFeedStatusInput
): Promise<GetThreatFeedStatusOutput> {
  logger.debug('Getting threat feed status', { input });

  try {
    const subscriptions = threatFeedManager.getSubscriptions();
    const feeds: ThreatFeedStatus[] = [];

    for (const subscription of subscriptions) {
      // Filter by feed_name if provided
      if (input?.feed_name && subscription.feed.name !== input.feed_name) {
        continue;
      }

      const { feed, last_check } = subscription;
      const nextCheck = last_check
        ? new Date(
            last_check.getTime() +
              feed.update_interval_minutes * 60 * 1000
          )
        : undefined;

      feeds.push({
        feed_name: feed.name,
        feed_type: feed.type,
        enabled: feed.enabled,
        last_update: feed.last_update?.toISOString(),
        next_check: nextCheck?.toISOString(),
        update_interval_minutes: feed.update_interval_minutes,
        status: feed.enabled ? 'active' : 'inactive',
      });
    }

    const activeFeeds = feeds.filter((f) => f.status === 'active').length;

    return {
      feeds,
      total_feeds: feeds.length,
      active_feeds: activeFeeds,
    };
  } catch (error) {
    logger.error('Failed to get threat feed status', { error });
    return {
      feeds: [],
      total_feeds: 0,
      active_feeds: 0,
    };
  }
}

