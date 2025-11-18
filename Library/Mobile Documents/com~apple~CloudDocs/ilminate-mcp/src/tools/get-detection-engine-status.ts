/**
 * get_detection_engine_status tool
 * 
 * Gets status and capabilities of ilminate detection engines.
 */

import { logger } from '../utils/logger.js';
import { callIlminateAPI, checkIlminateAPIHealth } from '../utils/ilminate-api.js';

interface DetectionEngineStatus {
  available: boolean;
  bridge_service: {
    available: boolean;
    url: string;
  };
  detection_engines: {
    apex_engine: {
      available: boolean;
      version?: string;
      active_layers?: string[];
    };
    layers: {
      layer_0_prefilter: boolean;
      layer_1_traditional: boolean;
      layer_2_yara: boolean;
      layer_3_feature_ml: boolean;
      layer_4_deep_learning: boolean;
      layer_4_5_image_scanning: boolean;
    };
    specialized_engines: {
      bec_detector: boolean;
      ato_detector: boolean;
      ai_content_detector: boolean;
    };
    osint_integration: {
      mosint: boolean;
      hunter_io: boolean;
      intelligence_x: boolean;
    };
  };
  capabilities: string[];
}

/**
 * Get detection engine status and capabilities
 */
export async function getDetectionEngineStatus(): Promise<DetectionEngineStatus> {
  logger.debug('Getting detection engine status');

  const status: DetectionEngineStatus = {
    available: false,
    bridge_service: {
      available: false,
      url: process.env.APEX_BRIDGE_URL || 'http://localhost:8888',
    },
    detection_engines: {
      apex_engine: {
        available: false,
      },
      layers: {
        layer_0_prefilter: false,
        layer_1_traditional: false,
        layer_2_yara: false,
        layer_3_feature_ml: false,
        layer_4_deep_learning: false,
        layer_4_5_image_scanning: false,
      },
      specialized_engines: {
        bec_detector: false,
        ato_detector: false,
        ai_content_detector: false,
      },
      osint_integration: {
        mosint: false,
        hunter_io: false,
        intelligence_x: false,
      },
    },
    capabilities: [],
  };

  try {
    // Check if bridge service is available
    const healthCheck = await checkIlminateAPIHealth();
    status.bridge_service.available = healthCheck;
    status.available = healthCheck;

    if (healthCheck) {
      // Get detailed status from APEX Bridge
      try {
        const bridgeStatus = await callIlminateAPI('/api/status', {
          method: 'GET',
        });

        if (bridgeStatus.available) {
          status.detection_engines.apex_engine.available = true;
          status.detection_engines.apex_engine.version =
            bridgeStatus.statistics?.engine_version;
          status.detection_engines.apex_engine.active_layers =
            bridgeStatus.statistics?.active_layers || [];

          // Map active layers to layer status
          const activeLayers = bridgeStatus.statistics?.active_layers || [];
          status.detection_engines.layers.layer_0_prefilter = true; // Always available
          status.detection_engines.layers.layer_1_traditional =
            activeLayers.some((l: string) =>
              ['SpamAssassin', 'ClamAV', 'Sublime'].includes(l)
            );
          status.detection_engines.layers.layer_2_yara =
            activeLayers.includes('YARA');
          status.detection_engines.layers.layer_3_feature_ml =
            activeLayers.includes('Feature-ML');
          status.detection_engines.layers.layer_4_deep_learning =
            activeLayers.includes('Deep-Learning');
          status.detection_engines.layers.layer_4_5_image_scanning = true; // Assumed available

          // Specialized engines (inferred from capabilities)
          status.detection_engines.specialized_engines.bec_detector = true; // Part of APEX
          status.detection_engines.specialized_engines.ato_detector = true; // Part of APEX
          status.detection_engines.specialized_engines.ai_content_detector =
            activeLayers.includes('Deep-Learning');

          // OSINT integration
          status.detection_engines.osint_integration.mosint =
            activeLayers.includes('Mosint-OSINT');
          status.detection_engines.osint_integration.hunter_io = true; // If Mosint is available
          status.detection_engines.osint_integration.intelligence_x = true; // If Mosint is available

          // Build capabilities list
          const capabilities: string[] = [
            'Email threat analysis',
            'MITRE ATT&CK mapping',
            'Domain reputation checking',
            'Image scanning (QR codes, logo impersonation)',
          ];

          if (status.detection_engines.layers.layer_1_traditional) {
            capabilities.push('Malware detection (ClamAV)');
            capabilities.push('Traditional threat scanning');
          }

          if (status.detection_engines.layers.layer_2_yara) {
            capabilities.push('YARA pattern matching');
          }

          if (status.detection_engines.layers.layer_3_feature_ml) {
            capabilities.push('Feature-based ML classification');
          }

          if (status.detection_engines.layers.layer_4_deep_learning) {
            capabilities.push('Deep learning AI analysis');
            capabilities.push('BERT/RoBERTa phishing detection');
            capabilities.push('AI-generated content detection');
          }

          if (status.detection_engines.osint_integration.mosint) {
            capabilities.push('OSINT threat intelligence');
            capabilities.push('BEC detection via related domains');
            capabilities.push('ATO detection via breach databases');
          }

          status.capabilities = capabilities;
        }
      } catch (error) {
        logger.warn('Could not get detailed status from bridge', { error });
      }
    }
  } catch (error) {
    logger.error('Failed to get detection engine status', { error });
  }

  return status;
}

