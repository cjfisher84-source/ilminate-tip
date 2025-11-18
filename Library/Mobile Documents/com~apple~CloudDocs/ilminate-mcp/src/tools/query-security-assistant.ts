/**
 * query_security_assistant tool
 * 
 * Query ilminate-apex Security Assistant with context.
 */

import { logger } from '../utils/logger.js';
import { querySecurityAssistant } from '../integrations/apex-integration.js';

interface QuerySecurityAssistantInput {
  query: string;
  context?: any;
}

interface QuerySecurityAssistantOutput {
  response: string;
  context_used?: any;
  success: boolean;
}

/**
 * Query Security Assistant
 */
export async function querySecurityAssistantTool(
  input: QuerySecurityAssistantInput
): Promise<QuerySecurityAssistantOutput> {
  logger.info('Querying Security Assistant', { query: input.query });

  try {
    const response = await querySecurityAssistant(input.query, input.context);

    return {
      response,
      context_used: input.context,
      success: true,
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    logger.error('Failed to query Security Assistant', { error });

    return {
      response: `Error: ${errorMessage}`,
      success: false,
    };
  }
}

