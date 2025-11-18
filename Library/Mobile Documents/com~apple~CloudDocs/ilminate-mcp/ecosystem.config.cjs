module.exports = {
  apps: [
    {
      name: 'apex-bridge',
      script: 'python3',
      args: 'bridge/apex_bridge.py',
      cwd: '/opt/ilminate-mcp',
      env: {
        APEX_BRIDGE_PORT: '8888',
        PYTHONUNBUFFERED: '1',
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
      env: {
        APEX_BRIDGE_URL: 'http://localhost:8888',
        NODE_ENV: 'production',
        LOG_LEVEL: 'info',
      },
      autorestart: true,
      watch: false,
      error_file: '/opt/ilminate-mcp/logs/mcp-server-error.log',
      out_file: '/opt/ilminate-mcp/logs/mcp-server-out.log',
    },
  ],
};

