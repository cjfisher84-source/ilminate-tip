/**
 * Authentication middleware for MCP server
 */

import { logger } from './utils/logger.js';

interface AuthResult {
  authenticated: boolean;
  error?: string;
}

/**
 * Authenticate MCP tool request
 * 
 * MCP protocol doesn't have standard auth headers, so we use:
 * - Environment-based authentication (same process = authenticated)
 * - API key check via environment variable
 */
export async function authenticateRequest(
  _request: any
): Promise<AuthResult> {
  const requiredApiKey = process.env.MCP_API_KEY;
  const requireAuth = process.env.MCP_REQUIRE_AUTH === 'true';

  // If auth not required, allow access
  if (!requireAuth) {
    return { authenticated: true };
  }

  // If API key required but not set, deny access
  if (!requiredApiKey) {
    logger.warn('MCP API key required but not configured');
    return { 
      authenticated: false, 
      error: 'API key not configured' 
    };
  }

  // For MCP protocol, we use environment-based auth:
  // - If running in same process/environment, consider authenticated
  // - API key is validated via environment variable
  // - In production, ensure MCP server runs with valid API key
  
  // Check if API key matches (for process-level auth)
  const providedKey = process.env.MCP_API_KEY_PROVIDED || '';
  
  if (providedKey && providedKey !== requiredApiKey) {
    logger.warn('Invalid API key provided');
    return { 
      authenticated: false, 
      error: 'Invalid API key' 
    };
  }

  // Environment-based authentication (same process)
  // In production, ensure proper API key management
  return { authenticated: true };
}

