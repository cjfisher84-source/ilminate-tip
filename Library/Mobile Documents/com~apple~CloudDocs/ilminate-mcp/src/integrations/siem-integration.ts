/**
 * ilminate-siem Integration
 * 
 * Integrates with ilminate-siem (Wazuh SIEM).
 */

import { logger } from '../utils/logger.js';

const SIEM_API_URL = process.env.SIEM_API_URL || 'http://localhost:55000';
const SIEM_API_USER = process.env.SIEM_API_USER || 'wazuh';
const SIEM_API_PASSWORD = process.env.SIEM_API_PASSWORD;

export interface SIEMEvent {
  id: string;
  timestamp: string;
  rule_id: number;
  rule_name: string;
  level: number;
  description: string;
  agent_id: string;
  agent_name: string;
  data: any;
}

export interface EnrichedSIEMEvent extends SIEMEvent {
  threat_intelligence?: {
    domain_reputation?: number;
    ip_reputation?: number;
    mitre_techniques?: string[];
    threat_categories?: string[];
  };
}

/**
 * Enrich SIEM event with threat intelligence
 */
export async function enrichSIEMEvent(
  event: SIEMEvent,
  enrichments: string[] = ['domain_reputation', 'threat_intelligence', 'mitre_mapping']
): Promise<EnrichedSIEMEvent> {
  const enriched: EnrichedSIEMEvent = { ...event, threat_intelligence: {} };

  try {
    // Extract domain/IP from event
    const domain = extractDomainFromEvent(event);
    // const ip = extractIPFromEvent(event); // Reserved for future use

    // Enrich with domain reputation if requested
    if (enrichments.includes('domain_reputation') && domain) {
      try {
        const { callIlminateAPI } = await import('../utils/ilminate-api.js');
        const repResult = await callIlminateAPI('/api/domain/reputation', {
          method: 'POST',
          body: JSON.stringify({ domain }),
        });
        enriched.threat_intelligence!.domain_reputation = repResult.reputation_score;
      } catch (error) {
        logger.debug('Error enriching domain reputation', { error });
      }
    }

    // Enrich with MITRE mapping if requested
    if (enrichments.includes('mitre_mapping')) {
      try {
        const { callIlminateAPI } = await import('../utils/ilminate-api.js');
        const mitreResult = await callIlminateAPI('/api/mitre/map', {
          method: 'POST',
          body: JSON.stringify({ event_text: event.description }),
        });
        enriched.threat_intelligence!.mitre_techniques =
          mitreResult.techniques?.map((t: any) => t.id) || [];
      } catch (error) {
        logger.debug('Error enriching MITRE mapping', { error });
      }
    }

    return enriched;
  } catch (error) {
    logger.error('Error enriching SIEM event', { error });
    return enriched;
  }
}

/**
 * Query SIEM alerts
 */
export async function querySIEMAlerts(
  query: {
    level?: number;
    rule_id?: number;
    agent_id?: string;
    time_range?: string;
    limit?: number;
  }
): Promise<SIEMEvent[]> {
  try {
    // Build Wazuh API query
    const params = new URLSearchParams();
    if (query.level) params.append('level', query.level.toString());
    if (query.rule_id) params.append('rule.id', query.rule_id.toString());
    if (query.agent_id) params.append('agent.id', query.agent_id);
    if (query.time_range) params.append('date', query.time_range);
    if (query.limit) params.append('limit', query.limit.toString());

    const auth = Buffer.from(`${SIEM_API_USER}:${SIEM_API_PASSWORD}`).toString('base64');

    const response = await fetch(
      `${SIEM_API_URL}/events?${params.toString()}`,
      {
        headers: {
          Authorization: `Basic ${auth}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`SIEM API error: ${response.statusText}`);
    }

    const data: any = await response.json();
    return data.data?.items || [];
  } catch (error) {
    logger.error('Error querying SIEM alerts', { error });
    return [];
  }
}

/**
 * Send detection event to SIEM
 */
export async function sendDetectionToSIEM(
  detection: {
    threat_type: string;
    severity: string;
    description: string;
    source: string;
    details: any;
  }
): Promise<boolean> {
  try {
    // Format as syslog message for Wazuh
    const syslogMessage = formatSyslogMessage(detection);

    // Send to SIEM syslog endpoint
    const response = await fetch(`${SIEM_API_URL}/syslog`, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/plain',
      },
      body: syslogMessage,
    });

    return response.ok;
  } catch (error) {
    logger.error('Error sending detection to SIEM', { error });
    return false;
  }
}

/**
 * Extract domain from SIEM event
 */
function extractDomainFromEvent(event: SIEMEvent): string | null {
  // Try to extract domain from event data
  const dataStr = JSON.stringify(event.data);
  const domainMatch = dataStr.match(/([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}/);
  return domainMatch ? domainMatch[0] : null;
}

/**
 * Extract IP from SIEM event
 * Reserved for future use
 */
// function extractIPFromEvent(event: SIEMEvent): string | null {
//   // Try to extract IP from event data
//   const dataStr = JSON.stringify(event.data);
//   const ipMatch = dataStr.match(/\b(?:\d{1,3}\.){3}\d{1,3}\b/);
//   return ipMatch ? ipMatch[0] : null;
// }

/**
 * Format detection as syslog message
 */
function formatSyslogMessage(detection: any): string {
  const timestamp = new Date().toISOString();
  const severity = mapSeverityToSyslog(detection.severity);
  
  return `<${severity}>${timestamp} ilminate-mcp ${detection.source}: ${detection.description} ${JSON.stringify(detection.details)}`;
}

/**
 * Map severity to syslog priority
 */
function mapSeverityToSyslog(severity: string): number {
  const severityMap: Record<string, number> = {
    low: 6,      // INFO
    medium: 4,   // WARNING
    high: 3,     // ERROR
    critical: 2, // CRITICAL
  };
  return severityMap[severity.toLowerCase()] || 6;
}

