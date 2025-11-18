/**
 * ilminate-sandbox Integration
 * 
 * Integrates with ilminate-sandbox file analysis service.
 */

import { logger } from '../utils/logger.js';

const SANDBOX_API_URL = process.env.SANDBOX_API_URL || 'http://localhost:3003';
const SANDBOX_API_KEY = process.env.SANDBOX_API_KEY;

export interface SandboxAnalysisRequest {
  file_url?: string;
  file_hash?: string;
  file_content?: Buffer;
  analysis_type?: 'static' | 'dynamic' | 'both';
}

export interface SandboxAnalysisResult {
  analysis_id: string;
  file_hash: string;
  file_type: string;
  threat_score: number;
  is_malicious: boolean;
  threat_family?: string;
  indicators: string[];
  static_analysis?: any;
  dynamic_analysis?: any;
  verdict: 'clean' | 'suspicious' | 'malicious';
}

/**
 * Analyze file in sandbox
 */
export async function analyzeFileInSandbox(
  request: SandboxAnalysisRequest
): Promise<SandboxAnalysisResult> {
  try {
    const formData = new FormData();
    
    if (request.file_url) {
      formData.append('file_url', request.file_url);
    }
    if (request.file_hash) {
      formData.append('file_hash', request.file_hash);
    }
    if (request.file_content) {
      formData.append('file', new Blob([request.file_content]));
    }
    if (request.analysis_type) {
      formData.append('analysis_type', request.analysis_type);
    }

    const response = await fetch(`${SANDBOX_API_URL}/api/analyze`, {
      method: 'POST',
      headers: {
        ...(SANDBOX_API_KEY && { 'X-API-Key': SANDBOX_API_KEY }),
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Sandbox API error: ${response.statusText}`);
    }

    const data: any = await response.json();
    return data.analysis || data;
  } catch (error) {
    logger.error('Error analyzing file in sandbox', { error });
    throw error;
  }
}

/**
 * Get sandbox analysis results
 */
export async function getSandboxResults(
  analysisId: string
): Promise<SandboxAnalysisResult | null> {
  try {
    const response = await fetch(`${SANDBOX_API_URL}/api/analysis/${analysisId}`, {
      headers: {
        ...(SANDBOX_API_KEY && { 'X-API-Key': SANDBOX_API_KEY }),
      },
    });

    if (!response.ok) {
      return null;
    }

    const data: any = await response.json();
    return data.analysis || data;
  } catch (error) {
    logger.error('Error getting sandbox results', { error });
    return null;
  }
}

/**
 * Check file reputation via sandbox
 */
export async function checkFileReputation(
  fileHash: string
): Promise<{
  reputation_score: number;
  is_malicious: boolean;
  threat_family?: string;
  first_seen?: Date;
  last_seen?: Date;
}> {
  try {
    const response = await fetch(
      `${SANDBOX_API_URL}/api/reputation/${fileHash}`,
      {
        headers: {
          ...(SANDBOX_API_KEY && { 'X-API-Key': SANDBOX_API_KEY }),
        },
      }
    );

    if (!response.ok) {
      return {
        reputation_score: 0.5,
        is_malicious: false,
      };
    }

    const data: any = await response.json();
    return {
      reputation_score: data.reputation_score || 0.5,
      is_malicious: data.is_malicious || false,
      threat_family: data.threat_family,
      first_seen: data.first_seen ? new Date(data.first_seen) : undefined,
      last_seen: data.last_seen ? new Date(data.last_seen) : undefined,
    };
  } catch (error) {
    logger.error('Error checking file reputation', { error });
    return {
      reputation_score: 0.5,
      is_malicious: false,
    };
  }
}

