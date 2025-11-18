/**
 * ilminate-portal Integration
 * 
 * Integrates with ilminate-portal customer portal.
 */

import { logger } from '../utils/logger.js';

const PORTAL_API_URL = process.env.PORTAL_API_URL || 'http://localhost:3001';
const PORTAL_API_KEY = process.env.PORTAL_API_KEY;

export interface PortalThreat {
  id: string;
  tenant_id: string;
  threat_type: string;
  severity: string;
  detected_at: string;
  status: string;
  summary: string;
}

export interface PortalAnalytics {
  total_threats: number;
  threats_by_type: Record<string, number>;
  threats_by_severity: Record<string, number>;
  recent_threats: PortalThreat[];
}

/**
 * Get threats for portal display
 */
export async function getPortalThreats(
  tenantId: string,
  options?: {
    limit?: number;
    offset?: number;
    status?: string;
    severity?: string;
  }
): Promise<PortalThreat[]> {
  try {
    const params = new URLSearchParams({
      tenant_id: tenantId,
      ...(options?.limit && { limit: options.limit.toString() }),
      ...(options?.offset && { offset: options.offset.toString() }),
      ...(options?.status && { status: options.status }),
      ...(options?.severity && { severity: options.severity }),
    });

    const response = await fetch(
      `${PORTAL_API_URL}/api/threats?${params.toString()}`,
      {
        headers: {
          ...(PORTAL_API_KEY && { 'X-API-Key': PORTAL_API_KEY }),
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Portal API error: ${response.statusText}`);
    }

    const data: any = await response.json();
    return data.threats || [];
  } catch (error) {
    logger.error('Error getting portal threats', { error });
    return [];
  }
}

/**
 * Get portal analytics
 */
export async function getPortalAnalytics(
  tenantId: string,
  timeRange: string = '7d'
): Promise<PortalAnalytics> {
  try {
    const response = await fetch(
      `${PORTAL_API_URL}/api/analytics?tenant_id=${tenantId}&time_range=${timeRange}`,
      {
        headers: {
          ...(PORTAL_API_KEY && { 'X-API-Key': PORTAL_API_KEY }),
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Portal API error: ${response.statusText}`);
    }

    const data: any = await response.json();
    return data.analytics || {
      total_threats: 0,
      threats_by_type: {},
      threats_by_severity: {},
      recent_threats: [],
    };
  } catch (error) {
    logger.error('Error getting portal analytics', { error });
    return {
      total_threats: 0,
      threats_by_type: {},
      threats_by_severity: {},
      recent_threats: [],
    };
  }
}

/**
 * Update portal settings
 */
export async function updatePortalSettings(
  tenantId: string,
  settings: Record<string, any>
): Promise<boolean> {
  try {
    const response = await fetch(`${PORTAL_API_URL}/api/settings/${tenantId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...(PORTAL_API_KEY && { 'X-API-Key': PORTAL_API_KEY }),
      },
      body: JSON.stringify(settings),
    });

    return response.ok;
  } catch (error) {
    logger.error('Error updating portal settings', { error });
    return false;
  }
}

