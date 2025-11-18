/**
 * get_campaign_analysis tool
 * 
 * Gets analysis of active threat campaigns from ilminate's campaign tracking system.
 */

import { logger } from '../utils/logger.js';
import { callIlminateAPI } from '../utils/ilminate-api.js';

interface GetCampaignAnalysisInput {
  campaign_name: string;
  time_range?: string; // e.g., "7d", "30d"
}

interface CampaignTimelineEvent {
  timestamp: string;
  event_type: string;
  description: string;
  threat_count?: number;
}

interface GetCampaignAnalysisOutput {
  campaign_name: string;
  threat_count: number;
  affected_domains: string[];
  techniques: string[]; // MITRE ATT&CK technique IDs
  timeline: CampaignTimelineEvent[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'dormant' | 'resolved';
}

/**
 * Get analysis of active threat campaigns
 */
export async function getCampaignAnalysis(
  input: GetCampaignAnalysisInput
): Promise<GetCampaignAnalysisOutput> {
  logger.debug('Getting campaign analysis', { input });

  try {
    // Call ilminate-apex campaign analysis API
    const timeRange = input.time_range || '7d';
    const result = await callIlminateAPI(
      `/api/campaigns/${encodeURIComponent(input.campaign_name)}`,
      {
        method: 'GET',
        params: { time_range: timeRange },
      }
    );

    return {
      campaign_name: result.campaign_name || input.campaign_name,
      threat_count: result.threat_count || 0,
      affected_domains: result.affected_domains || [],
      techniques: result.techniques || [],
      timeline: result.timeline || [],
      severity: result.severity || 'medium',
      status: result.status || 'active',
    };
  } catch (error) {
    logger.error('Failed to get campaign analysis', { error, input });

    // Fallback: Return empty campaign data
    return {
      campaign_name: input.campaign_name,
      threat_count: 0,
      affected_domains: [],
      techniques: [],
      timeline: [],
      severity: 'low',
      status: 'dormant',
    };
  }
}

