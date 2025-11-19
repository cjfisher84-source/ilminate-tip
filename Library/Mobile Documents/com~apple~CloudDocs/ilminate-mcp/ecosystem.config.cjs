require('dotenv').config({ path: '/opt/ilminate-mcp/.env' });

module.exports = {
  apps: [
    {
      name: 'apex-bridge',
      script: 'python3',
      args: 'bridge/apex_bridge.py',
      cwd: '/opt/ilminate-mcp',
      env_file: '/opt/ilminate-mcp/.env',
      env: {
        APEX_BRIDGE_PORT: '8888',
        PYTHONUNBUFFERED: '1',
        APEX_BRIDGE_REQUIRE_AUTH: process.env.APEX_BRIDGE_REQUIRE_AUTH || 'false',
        APEX_BRIDGE_API_KEY: process.env.APEX_BRIDGE_API_KEY || '',
      },
      autorestart: true,
      watch: false,
      error_file: '/opt/ilminate-mcp/logs/apex-bridge-error.log',
      out_file: '/opt/ilminate-mcp/logs/apex-bridge-out.log',
    },
    {
      name: 'mcp-server',
      script: 'dist/index.js',
      cwd: '/opt/ilminate-mcp',
      env_file: '/opt/ilminate-mcp/.env',
      env: {
        APEX_BRIDGE_URL: 'http://localhost:8888',
        NODE_ENV: 'production',
        LOG_LEVEL: 'info',
        MCP_REQUIRE_AUTH: process.env.MCP_REQUIRE_AUTH || 'false',
        MCP_API_KEY: process.env.MCP_API_KEY || '',
        APEX_BRIDGE_API_KEY: process.env.APEX_BRIDGE_API_KEY || '',
      },
      autorestart: true,
      watch: false,
      error_file: '/opt/ilminate-mcp/logs/mcp-server-error.log',
      out_file: '/opt/ilminate-mcp/logs/mcp-server-out.log',
    },
  ],
};

