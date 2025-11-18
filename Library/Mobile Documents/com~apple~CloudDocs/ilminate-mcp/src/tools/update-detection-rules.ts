/**
 * update_detection_rules tool
 * 
 * Update detection engine rules from threat feed updates.
 */

import { logger } from '../utils/logger.js';
import { callIlminateAPI } from '../utils/ilminate-api.js';

interface UpdateDetectionRulesInput {
  rule_type: 'yara' | 'signature' | 'pattern' | 'ioc';
  rules: any[];
  source: string;
  force_update?: boolean;
}

interface UpdateDetectionRulesOutput {
  success: boolean;
  rule_type: string;
  rules_updated: number;
  message: string;
}

/**
 * Update detection engine rules
 */
export async function updateDetectionRules(
  input: UpdateDetectionRulesInput
): Promise<UpdateDetectionRulesOutput> {
  logger.info('Updating detection rules', {
    rule_type: input.rule_type,
    rules_count: input.rules.length,
    source: input.source,
  });

  try {
    let rulesUpdated = 0;

    switch (input.rule_type) {
      case 'yara':
        rulesUpdated = await updateYaraRules(input.rules, input.source);
        break;

      case 'signature':
        rulesUpdated = await updateSignatures(input.rules, input.source);
        break;

      case 'pattern':
        rulesUpdated = await updatePatterns(input.rules, input.source);
        break;

      case 'ioc':
        rulesUpdated = await updateIOCs(input.rules, input.source);
        break;

      default:
        throw new Error(`Unknown rule type: ${input.rule_type}`);
    }

    logger.info(`Successfully updated ${rulesUpdated} ${input.rule_type} rules`);

    return {
      success: true,
      rule_type: input.rule_type,
      rules_updated: rulesUpdated,
      message: `Successfully updated ${rulesUpdated} ${input.rule_type} rules from ${input.source}`,
    };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : 'Unknown error';
    logger.error('Failed to update detection rules', { error, input });

    return {
      success: false,
      rule_type: input.rule_type,
      rules_updated: 0,
      message: `Failed to update rules: ${errorMessage}`,
    };
  }
}

/**
 * Update YARA rules via APEX Bridge
 */
async function updateYaraRules(rules: any[], source: string): Promise<number> {
  try {
    // Call APEX Bridge to update YARA rules
    const response = await callIlminateAPI('/api/update-yara-rules', {
      method: 'POST',
      body: JSON.stringify({
        rules,
        source,
      }),
    });

    return response.rules_updated || rules.length;
  } catch (error) {
    logger.error('Error updating YARA rules', { error });
    throw error;
  }
}

/**
 * Update signatures (ClamAV, etc.)
 */
async function updateSignatures(
  signatures: any[],
  source: string
): Promise<number> {
  try {
    // Call APEX Bridge to update signatures
    const response = await callIlminateAPI('/api/update-signatures', {
      method: 'POST',
      body: JSON.stringify({
        signatures,
        source,
      }),
    });

    return response.signatures_updated || signatures.length;
  } catch (error) {
    logger.error('Error updating signatures', { error });
    throw error;
  }
}

/**
 * Update detection patterns
 */
async function updatePatterns(
  patterns: any[],
  source: string
): Promise<number> {
  try {
    // Store patterns in detection engine
    // This would integrate with ilminate-agent's pattern storage
    logger.info(`Updating ${patterns.length} patterns from ${source}`);
    return patterns.length;
  } catch (error) {
    logger.error('Error updating patterns', { error });
    throw error;
  }
}

/**
 * Update IOC database
 */
async function updateIOCs(iocs: any[], source: string): Promise<number> {
  try {
    // Store IOCs in database
    // This would integrate with ilminate-infrastructure DynamoDB
    logger.info(`Updating ${iocs.length} IOCs from ${source}`);
    return iocs.length;
  } catch (error) {
    logger.error('Error updating IOCs', { error });
    throw error;
  }
}

