/**
 * ilminate-apex Integration
 * 
 * Integrates with ilminate-apex Security Assistant and API endpoints.
 */

import { logger } from '../utils/logger.js';

const APEX_API_URL = process.env.APEX_API_URL || 'http://localhost:3000';
const APEX_API_KEY = process.env.APEX_API_KEY;

export interface ApexThreat {
  id: string;
  customer_id: string;
  threat_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'new' | 'investigating' | 'resolved' | 'false_positive';
  detected_at: Date;
  details: any;
}

export interface ApexCustomer {
  id: string;
  name: string;
  tenant_id: string;
}

/**
 * Query Security Assistant
 */
export async function querySecurityAssistant(
  query: string,
  context?: any
): Promise<string> {
  try {
    const response = await fetch(`${APEX_API_URL}/api/assistant`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(APEX_API_KEY && { 'X-API-Key': APEX_API_KEY }),
      },
      body: JSON.stringify({
        query,
        context,
      }),
    });

    if (!response.ok) {
      throw new Error(`Apex API error: ${response.statusText}`);
    }

    const data: any = await response.json();
    return data.response || data.message || '';
  } catch (error) {
    logger.error('Error querying Security Assistant', { error });
    throw error;
  }
}

/**
 * Get threats for a specific customer
 */
export async function getCustomerThreats(
  customerId: string,
  filters?: {
    status?: string;
    severity?: string;
    time_range?: string;
  }
): Promise<ApexThreat[]> {
  try {
    const params = new URLSearchParams({
      customer_id: customerId,
      ...(filters?.status && { status: filters.status }),
      ...(filters?.severity && { severity: filters.severity }),
      ...(filters?.time_range && { time_range: filters.time_range }),
    });

    const response = await fetch(
      `${APEX_API_URL}/api/threats?${params.toString()}`,
      {
        headers: {
          ...(APEX_API_KEY && { 'X-API-Key': APEX_API_KEY }),
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Apex API error: ${response.statusText}`);
    }

    const data: any = await response.json();
    return data.threats || [];
  } catch (error) {
    logger.error('Error getting customer threats', { error });
    return [];
  }
}

/**
 * Update threat status
 */
export async function updateThreatStatus(
  threatId: string,
  status: string,
  notes?: string
): Promise<boolean> {
  try {
    const response = await fetch(`${APEX_API_URL}/api/threats/${threatId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...(APEX_API_KEY && { 'X-API-Key': APEX_API_KEY }),
      },
      body: JSON.stringify({
        status,
        notes,
      }),
    });

    return response.ok;
  } catch (error) {
    logger.error('Error updating threat status', { error });
    return false;
  }
}

/**
 * Get customer information
 */
export async function getCustomer(customerId: string): Promise<ApexCustomer | null> {
  try {
    const response = await fetch(`${APEX_API_URL}/api/customers/${customerId}`, {
      headers: {
        ...(APEX_API_KEY && { 'X-API-Key': APEX_API_KEY }),
      },
    });

    if (!response.ok) {
      return null;
    }

    const data: any = await response.json();
    return data.customer || null;
  } catch (error) {
    logger.error('Error getting customer', { error });
    return null;
  }
}

