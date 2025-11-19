/**
 * analyze_email_threat tool
 * 
 * Analyzes email for BEC/phishing indicators using ilminate's triage analysis engine.
 */

import { logger } from '../utils/logger.js';
import { callIlminateAPI } from '../utils/ilminate-api.js';

interface AnalyzeEmailThreatInput {
  subject: string;
  sender: string;
  body: string;
  attachments?: string[];
}

interface AnalyzeEmailThreatOutput {
  threat_score: number;
  threat_type: 'BEC' | 'Phishing' | 'Malware' | 'Safe';
  indicators: string[];
  recommendation: 'quarantine' | 'review' | 'allow';
  confidence: number;
}

/**
 * Analyze email for threats using ilminate triage analysis
 */
export async function analyzeEmailThreat(
  input: AnalyzeEmailThreatInput
): Promise<AnalyzeEmailThreatOutput> {
  logger.debug('Analyzing email threat', { input });

  try {
    // Call APEX Bridge (connects to ilminate-agent detection engines)
    const result = await callIlminateAPI('/api/analyze-email', {
      method: 'POST',
      body: JSON.stringify({
        message_id: `mcp-${Date.now()}`,
        subject: input.subject,
        sender: input.sender,
        body: input.body,
        attachments: input.attachments || [],
      }),
    });

    if (!result.success || !result.verdict) {
      throw new Error('Invalid response from APEX Bridge');
    }

    const verdict = result.verdict;

    // Transform APEX verdict to MCP tool output format
    return {
      threat_score: (verdict.risk_score || 0) / 100,
      threat_type: (verdict.threat_categories?.[0] || 'Safe') as 'BEC' | 'Phishing' | 'Malware' | 'Safe',
      indicators: verdict.indicators || [],
      recommendation: (verdict.action === 'quarantine' ? 'quarantine' : 
                       verdict.action === 'block' ? 'quarantine' : 
                       verdict.threat_level === 'HIGH' || verdict.threat_level === 'CRITICAL' ? 'review' : 'allow') as 'quarantine' | 'review' | 'allow',
      confidence: verdict.confidence || 0.5,
    };
  } catch (error) {
    logger.error('Failed to analyze email threat', { error, input });

    // Fallback: Basic heuristic analysis if API is unavailable
    return performBasicHeuristicAnalysis(input);
  }
}

/**
 * Basic heuristic analysis fallback
 * This mimics ilminate's triage analysis when API is unavailable
 */
function performBasicHeuristicAnalysis(
  input: AnalyzeEmailThreatInput
): AnalyzeEmailThreatOutput {
  const indicators: string[] = [];
  let threatScore = 0;

  // Check for urgent language
  const urgentKeywords = ['urgent', 'immediately', 'asap', 'action required'];
  const hasUrgentLanguage = urgentKeywords.some((keyword) =>
    input.body.toLowerCase().includes(keyword)
  );
  if (hasUrgentLanguage) {
    indicators.push('urgent_language');
    threatScore += 0.2;
  }

  // Check for suspicious sender patterns
  const senderDomain = input.sender.split('@')[1]?.toLowerCase();
  if (senderDomain && senderDomain.includes('suspicious')) {
    indicators.push('suspicious_sender');
    threatScore += 0.3;
  }

  // Check for financial requests
  const financialKeywords = ['wire transfer', 'payment', 'invoice', 'refund'];
  const hasFinancialRequest = financialKeywords.some((keyword) =>
    input.body.toLowerCase().includes(keyword)
  );
  if (hasFinancialRequest) {
    indicators.push('financial_request');
    threatScore += 0.3;
  }

  // Determine threat type
  let threatType: 'BEC' | 'Phishing' | 'Malware' | 'Safe' = 'Safe';
  if (threatScore > 0.7) {
    threatType = hasFinancialRequest ? 'BEC' : 'Phishing';
  } else if (threatScore > 0.4) {
    threatType = 'Phishing';
  }

  // Determine recommendation
  let recommendation: 'quarantine' | 'review' | 'allow' = 'allow';
  if (threatScore > 0.7) {
    recommendation = 'quarantine';
  } else if (threatScore > 0.4) {
    recommendation = 'review';
  }

  return {
    threat_score: Math.min(threatScore, 1.0),
    threat_type: threatType,
    indicators,
    recommendation,
    confidence: 0.6, // Lower confidence for heuristic analysis
  };
}

