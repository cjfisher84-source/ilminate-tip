/**
 * ilminate-email Integration
 * 
 * Integrates with ilminate-email email processing service.
 */

import { logger } from '../utils/logger.js';

const EMAIL_API_URL = process.env.EMAIL_API_URL || 'http://localhost:3002';
const EMAIL_API_KEY = process.env.EMAIL_API_KEY;

export interface EmailMessage {
  id: string;
  message_id: string;
  from: string;
  to: string;
  subject: string;
  body: string;
  attachments?: string[];
  received_at: Date;
}

export interface EmailAnalysisResult {
  threat_score: number;
  threat_type: string;
  indicators: string[];
  recommendation: string;
}

/**
 * Analyze email message using detection engines
 */
export async function analyzeEmailMessage(
  email: EmailMessage
): Promise<EmailAnalysisResult> {
  try {
    // Use MCP tool to analyze email
    const { callIlminateAPI } = await import('../utils/ilminate-api.js');
    
    const result = await callIlminateAPI('/api/triage/analyze', {
      method: 'POST',
      body: JSON.stringify({
        message_id: email.message_id,
        subject: email.subject,
        sender: email.from,
        body: email.body,
        attachments: email.attachments || [],
      }),
    });

    return {
      threat_score: result.threat_score || 0,
      threat_type: result.threat_type || 'Safe',
      indicators: result.indicators || [],
      recommendation: result.recommendation || 'allow',
    };
  } catch (error) {
    logger.error('Error analyzing email message', { error });
    throw error;
  }
}

/**
 * Get email threats for a tenant
 */
export async function getEmailThreats(
  tenantId: string,
  filters?: {
    time_range?: string;
    threat_type?: string;
    status?: string;
  }
): Promise<any[]> {
  try {
    const params = new URLSearchParams({
      tenant_id: tenantId,
      ...(filters?.time_range && { time_range: filters.time_range }),
      ...(filters?.threat_type && { threat_type: filters.threat_type }),
      ...(filters?.status && { status: filters.status }),
    });

    const response = await fetch(
      `${EMAIL_API_URL}/api/threats?${params.toString()}`,
      {
        headers: {
          ...(EMAIL_API_KEY && { 'X-API-Key': EMAIL_API_KEY }),
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Email API error: ${response.statusText}`);
    }

    const data: any = await response.json();
    return data.threats || [];
  } catch (error) {
    logger.error('Error getting email threats', { error });
    return [];
  }
}

/**
 * Quarantine email via MCP
 */
export async function quarantineEmail(
  emailId: string,
  reason: string
): Promise<boolean> {
  try {
    const response = await fetch(`${EMAIL_API_URL}/api/emails/${emailId}/quarantine`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(EMAIL_API_KEY && { 'X-API-Key': EMAIL_API_KEY }),
      },
      body: JSON.stringify({
        reason,
      }),
    });

    return response.ok;
  } catch (error) {
    logger.error('Error quarantining email', { error });
    return false;
  }
}

