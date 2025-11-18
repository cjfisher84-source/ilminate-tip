/**
 * map_to_mitre_attack tool
 * 
 * Maps security events to MITRE ATT&CK techniques using ilminate's ATT&CK mapper.
 */

import { logger } from '../utils/logger.js';
import { callIlminateAPI } from '../utils/ilminate-api.js';

interface MapToMitreAttackInput {
  event_text: string;
}

interface MitreTechnique {
  id: string;
  name: string;
  confidence: number;
  description?: string;
}

interface MapToMitreAttackOutput {
  techniques: MitreTechnique[];
  primary_technique?: MitreTechnique;
}

/**
 * Map security event to MITRE ATT&CK techniques
 */
export async function mapToMitreAttack(
  input: MapToMitreAttackInput
): Promise<MapToMitreAttackOutput> {
  logger.debug('Mapping to MITRE ATT&CK', { input });

  try {
    // Call APEX Bridge MITRE ATT&CK mapper (connects to ilminate-agent)
    const result = await callIlminateAPI('/api/mitre/map', {
      method: 'POST',
      body: JSON.stringify({
        event_text: input.event_text,
      }),
    });

    return {
      techniques: result.techniques || [],
      primary_technique: result.primary_technique,
    };
  } catch (error) {
    logger.error('Failed to map to MITRE ATT&CK', { error, input });

    // Fallback: Basic pattern matching
    return performBasicMitreMapping(input);
  }
}

/**
 * Basic MITRE ATT&CK mapping fallback
 * Uses pattern matching for common techniques
 */
function performBasicMitreMapping(
  input: MapToMitreAttackInput
): MapToMitreAttackOutput {
  const techniques: MitreTechnique[] = [];
  const eventText = input.event_text.toLowerCase();

  // T1566.001 - Phishing: Spearphishing Attachment
  if (
    eventText.includes('phish') ||
    eventText.includes('attachment') ||
    eventText.includes('malicious file')
  ) {
    techniques.push({
      id: 'T1566.001',
      name: 'Phishing: Spearphishing Attachment',
      confidence: 0.7,
      description: 'Adversary sends a malicious attachment via email',
    });
  }

  // T1566.002 - Phishing: Spearphishing Link
  if (
    eventText.includes('phish') ||
    eventText.includes('suspicious link') ||
    eventText.includes('malicious url')
  ) {
    techniques.push({
      id: 'T1566.002',
      name: 'Phishing: Spearphishing Link',
      confidence: 0.7,
      description: 'Adversary sends a malicious link via email',
    });
  }

  // T1071.001 - Application Layer Protocol: Web Protocols
  if (eventText.includes('http') || eventText.includes('https')) {
    techniques.push({
      id: 'T1071.001',
      name: 'Application Layer Protocol: Web Protocols',
      confidence: 0.5,
      description: 'Adversary uses web protocols for communication',
    });
  }

  // T1583.001 - Acquire Infrastructure: Domains
  if (eventText.includes('domain') || eventText.includes('dns')) {
    techniques.push({
      id: 'T1583.001',
      name: 'Acquire Infrastructure: Domains',
      confidence: 0.4,
      description: 'Adversary acquires domains for malicious purposes',
    });
  }

  // If no techniques found, return empty array
  if (techniques.length === 0) {
    techniques.push({
      id: 'T1048',
      name: 'Exfiltration Over Alternative Protocol',
      confidence: 0.3,
      description: 'Generic exfiltration technique',
    });
  }

  return {
    techniques,
    primary_technique: techniques[0],
  };
}

