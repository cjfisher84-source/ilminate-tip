/**
 * Cross-Repo Integration Hub
 * 
 * Central export for all ilminate repository integrations.
 */

export * from './apex-integration.js';
export * from './portal-integration.js';
export * from './siem-integration.js';
export * from './email-integration.js';
export * from './sandbox-integration.js';

/**
 * Get integration status for all repos
 */
export async function getIntegrationStatus(): Promise<Record<string, boolean>> {
  const status: Record<string, boolean> = {};

  // Check each integration
  try {
    // ilminate-agent (always available via APEX Bridge)
    status['ilminate-agent'] = true;

    // Check other integrations
    const integrations = [
      { name: 'ilminate-apex', url: process.env.APEX_API_URL },
      { name: 'ilminate-portal', url: process.env.PORTAL_API_URL },
      { name: 'ilminate-siem', url: process.env.SIEM_API_URL },
      { name: 'ilminate-email', url: process.env.EMAIL_API_URL },
      { name: 'ilminate-sandbox', url: process.env.SANDBOX_API_URL },
    ];

    for (const integration of integrations) {
      if (integration.url) {
        try {
          const response = await fetch(`${integration.url}/health`, {
            signal: AbortSignal.timeout(2000),
          });
          status[integration.name] = response.ok;
        } catch {
          status[integration.name] = false;
        }
      } else {
        status[integration.name] = false;
      }
    }
  } catch (error) {
    // If check fails, assume all unavailable
    Object.keys(status).forEach((key) => {
      status[key] = false;
    });
  }

  return status;
}

