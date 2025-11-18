/**
 * Utility for calling ilminate detection engines
 * 
 * This module handles communication with the APEX bridge service,
 * which connects to ilminate-agent detection engines.
 */

import { logger } from './logger.js';

// APEX Bridge URL (Python HTTP service that wraps detection engines)
const APEX_BRIDGE_URL =
  process.env.APEX_BRIDGE_URL || 'http://localhost:8888';

// Fallback to ilminate-apex API if bridge is not available
const ILMINATE_API_URL =
  process.env.ILMINATE_API_URL || 'http://localhost:3000';
const ILMINATE_API_KEY = process.env.ILMINATE_API_KEY;

interface ApiRequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: string;
  params?: Record<string, string>;
  headers?: Record<string, string>;
}

/**
 * Call APEX Bridge service (preferred) or ilminate-apex API (fallback)
 */
export async function callIlminateAPI(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<any> {
  // Try APEX Bridge first (connects to ilminate-agent detection engines)
  try {
    return await callAPEXBridge(endpoint, options);
  } catch (bridgeError: unknown) {
    logger.debug('APEX Bridge unavailable, trying ilminate-apex API', {
      error: bridgeError,
    });

    // Fallback to ilminate-apex API
    return await callIlminateApexAPI(endpoint, options);
  }
}

/**
 * Call APEX Bridge service (Python HTTP service wrapping detection engines)
 */
async function callAPEXBridge(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<any> {
  const method = options.method || 'GET';
  const body = options.body;
  const params = options.params;
  const headers = options.headers || {};

  // Map MCP endpoints to APEX Bridge endpoints
  const endpointMap: Record<string, string> = {
    '/api/triage/analyze': '/api/analyze-email',
    '/api/mitre/map': '/api/map-mitre',
    '/api/domain/reputation': '/api/check-domain',
    '/api/images/scan': '/api/scan-image',
    '/health': '/health',
  };

  const bridgeEndpoint = endpointMap[endpoint] || endpoint;
  const url = new URL(bridgeEndpoint, APEX_BRIDGE_URL);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });
  }

  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  };

  try {
    logger.debug(`Calling APEX Bridge: ${method} ${url.toString()}`);

    const response = await fetch(url.toString(), {
      method,
      headers: requestHeaders,
      body,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `APEX Bridge error: ${response.status} ${response.statusText} - ${errorText}`
      );
    }

    const data: any = await response.json();

    // Transform APEX Bridge response to expected format
    if (data.success && data.verdict) {
      // Transform verdict to match expected format
      return {
        threat_score: data.verdict.risk_score / 100, // Convert 0-100 to 0-1
        threat_type: mapThreatType(data.verdict.threat_categories),
        indicators: data.verdict.indicators || [],
        recommendation: mapActionToRecommendation(data.verdict.action),
        confidence: data.verdict.confidence,
        ...data.verdict,
      };
    }

    return data;
  } catch (error) {
    logger.error('Failed to call APEX Bridge', {
      error,
      endpoint: bridgeEndpoint,
      method,
    });
    throw error;
  }
}

/**
 * Call ilminate-apex API (fallback)
 */
async function callIlminateApexAPI(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<any> {
  const { method = 'GET', body, params, headers = {} } = options;

  const url = new URL(endpoint, ILMINATE_API_URL);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });
  }

  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  };

  if (ILMINATE_API_KEY) {
    requestHeaders['X-API-Key'] = ILMINATE_API_KEY;
  }

  try {
    logger.debug(`Calling ilminate-apex API: ${method} ${url.toString()}`);

    const response = await fetch(url.toString(), {
      method,
      headers: requestHeaders,
      body,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `ilminate API error: ${response.status} ${response.statusText} - ${errorText}`
      );
    }

    const data = await response.json();
    return data;
  } catch (error) {
    logger.error('Failed to call ilminate API', {
      error,
      endpoint,
      method,
    });
    throw error;
  }
}

/**
 * Map threat categories to threat type
 */
function mapThreatType(categories: string[]): string {
  if (!categories || categories.length === 0) {
    return 'Safe';
  }

  const categoryStr = categories.join(' ').toLowerCase();

  if (categoryStr.includes('bec')) {
    return 'BEC';
  }
  if (categoryStr.includes('phish')) {
    return 'Phishing';
  }
  if (categoryStr.includes('malware') || categoryStr.includes('virus')) {
    return 'Malware';
  }

  return 'Phishing'; // Default
}

/**
 * Map APEX action to recommendation
 */
function mapActionToRecommendation(action: string): string {
  const actionMap: Record<string, string> = {
    BLOCK: 'quarantine',
    QUARANTINE: 'quarantine',
    WARN: 'review',
    TAG: 'review',
    ALLOW: 'allow',
  };

  return actionMap[action.toUpperCase()] || 'review';
}

/**
 * Check if APEX Bridge or ilminate API is available
 */
export async function checkIlminateAPIHealth(): Promise<boolean> {
  // Try APEX Bridge first
  try {
    const response = await fetch(`${APEX_BRIDGE_URL}/health`);
    if (response.ok) {
      const data: any = await response.json();
      return data.apex_initialized === true;
    }
  } catch (error) {
    logger.debug('APEX Bridge health check failed', { error });
  }

  // Fallback to ilminate-apex API
  try {
    await callIlminateAPI('/health', { method: 'GET' });
    return true;
  } catch (error) {
    logger.warn('ilminate API health check failed', { error });
    return false;
  }
}

