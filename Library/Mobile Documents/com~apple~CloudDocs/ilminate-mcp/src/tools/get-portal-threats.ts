/**
 * get_portal_threats tool
 * 
 * Get threats for ilminate-portal display.
 */

import { logger } from '../utils/logger.js';
import { getPortalThreats } from '../integrations/portal-integration.js';

interface GetPortalThreatsInput {
  tenant_id: string;
  limit?: number;
  offset?: number;
  status?: string;
  severity?: string;
}

interface GetPortalThreatsOutput {
  threats: any[];
  count: number;
  tenant_id: string;
  success: boolean;
}

/**
 * Get portal threats
 */
export async function getPortalThreatsTool(
  input: GetPortalThreatsInput
): Promise<GetPortalThreatsOutput> {
  logger.info('Getting portal threats', { tenant_id: input.tenant_id });

  try {
    const threats = await getPortalThreats(input.tenant_id, {
      limit: input.limit,
      offset: input.offset,
      status: input.status,
      severity: input.severity,
    });

    return {
      threats,
      count: threats.length,
      tenant_id: input.tenant_id,
      success: true,
    };
  } catch (error) {
    logger.error('Failed to get portal threats', { error });
    return {
      threats: [],
      count: 0,
      tenant_id: input.tenant_id,
      success: false,
    };
  }
}

