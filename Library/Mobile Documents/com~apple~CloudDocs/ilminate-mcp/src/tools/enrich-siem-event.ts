/**
 * enrich_siem_event tool
 * 
 * Enrich SIEM events with threat intelligence.
 */

import { logger } from '../utils/logger.js';
import { enrichSIEMEvent } from '../integrations/siem-integration.js';

interface EnrichSIEMEventInput {
  event: {
    id: string;
    timestamp: string;
    rule_id: number;
    rule_name: string;
    level: number;
    description: string;
    agent_id: string;
    agent_name: string;
    data: any;
  };
  enrichments?: string[];
}

interface EnrichSIEMEventOutput {
  enriched_event: any;
  success: boolean;
}

/**
 * Enrich SIEM event
 */
export async function enrichSIEMEventTool(
  input: EnrichSIEMEventInput
): Promise<EnrichSIEMEventOutput> {
  logger.info('Enriching SIEM event', { event_id: input.event.id });

  try {
    const enrichments = input.enrichments || [
      'domain_reputation',
      'threat_intelligence',
      'mitre_mapping',
    ];

    const enriched = await enrichSIEMEvent(input.event, enrichments);

    return {
      enriched_event: enriched,
      success: true,
    };
  } catch (error) {
    logger.error('Failed to enrich SIEM event', { error });
    return {
      enriched_event: input.event,
      success: false,
    };
  }
}

