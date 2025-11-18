/**
 * check_domain_reputation tool
 * 
 * Checks domain reputation and threat intelligence using ilminate's domain analysis.
 */

import { logger } from '../utils/logger.js';
import { callIlminateAPI } from '../utils/ilminate-api.js';

interface CheckDomainReputationInput {
  domain: string;
}

interface CheckDomainReputationOutput {
  reputation_score: number; // 0.0 (malicious) to 1.0 (safe)
  is_malicious: boolean;
  threat_types: string[];
  first_seen?: string;
  last_seen?: string;
  whois_data?: {
    registrar?: string;
    creation_date?: string;
    expiration_date?: string;
  };
  dns_records?: {
    a?: string[];
    mx?: string[];
    txt?: string[];
  };
}

/**
 * Check domain reputation and threat intelligence
 */
export async function checkDomainReputation(
  input: CheckDomainReputationInput
): Promise<CheckDomainReputationOutput> {
  logger.debug('Checking domain reputation', { input });

  try {
    // Call APEX Bridge domain reputation (uses Mosint OSINT from ilminate-agent)
    const result = await callIlminateAPI('/api/domain/reputation', {
      method: 'POST',
      body: JSON.stringify({
        domain: input.domain,
      }),
    });

    return {
      reputation_score: result.reputation_score || 0.5,
      is_malicious: result.is_malicious || false,
      threat_types: result.threat_types || [],
      first_seen: result.first_seen,
      last_seen: result.last_seen,
      whois_data: result.whois_data,
      dns_records: result.dns_records,
    };
  } catch (error) {
    logger.error('Failed to check domain reputation', { error, input });

    // Fallback: Basic domain analysis
    return performBasicDomainAnalysis(input);
  }
}

/**
 * Basic domain analysis fallback
 */
function performBasicDomainAnalysis(
  input: CheckDomainReputationInput
): CheckDomainReputationOutput {
  const domain = input.domain.toLowerCase();
  const threatTypes: string[] = [];
  let reputationScore = 0.5;
  let isMalicious = false;

  // Check for suspicious domain patterns
  const suspiciousPatterns = [
    /^[0-9]+\./,
    /^xn--/,
    /bit\.ly|tinyurl|goo\.gl/i,
  ];

  const hasSuspiciousPattern = suspiciousPatterns.some((pattern) =>
    pattern.test(domain)
  );

  if (hasSuspiciousPattern) {
    threatTypes.push('suspicious_pattern');
    reputationScore = 0.3;
  }

  // Check for known malicious TLDs (basic check)
  const suspiciousTLDs = ['.tk', '.ml', '.ga', '.cf'];
  const hasSuspiciousTLD = suspiciousTLDs.some((tld) => domain.endsWith(tld));

  if (hasSuspiciousTLD) {
    threatTypes.push('suspicious_tld');
    reputationScore = Math.min(reputationScore, 0.4);
  }

  // Very new domains might be suspicious
  // (In real implementation, would check WHOIS data)

  if (reputationScore < 0.4) {
    isMalicious = true;
  }

  return {
    reputation_score: reputationScore,
    is_malicious: isMalicious,
    threat_types: threatTypes,
  };
}

