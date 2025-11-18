# Deployment Guide

## Local Development

Run the MCP server locally for development:

```bash
npm install
npm run build
npm start
```

## Using with Claude Desktop

1. **Install Claude Desktop** (if not already installed)

2. **Configure Claude Desktop** to use ilminate MCP server:
   
   Edit Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

   Add MCP server configuration:
   ```json
   {
     "mcpServers": {
       "ilminate": {
         "command": "node",
         "args": ["/path/to/ilminate-mcp/dist/index.js"],
         "env": {
           "ILMINATE_API_URL": "https://api.ilminate.example.com",
           "ILMINATE_API_KEY": "your-api-key"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

4. **Verify Connection**: Claude Desktop should now have access to ilminate MCP tools

## Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY dist ./dist

CMD ["node", "dist/index.js"]
```

Build and run:

```bash
docker build -t ilminate-mcp .
docker run -e ILMINATE_API_URL=... -e ILMINATE_API_KEY=... ilminate-mcp
```

## AWS Lambda Deployment

The MCP server can be deployed as an AWS Lambda function:

1. **Package for Lambda**:
   ```bash
   npm run build
   zip -r lambda.zip dist/ node_modules/ package.json
   ```

2. **Create Lambda Function**:
   - Runtime: Node.js 18.x
   - Handler: `dist/index.handler` (requires Lambda wrapper)
   - Environment variables: Set from `.env`

3. **Note**: MCP stdio transport may need adaptation for Lambda. Consider HTTP transport for Lambda.

## Environment Variables

Required environment variables:

- `ILMINATE_API_URL` - URL to ilminate-apex API
- `ILMINATE_API_KEY` - API key for ilminate-apex (if required)
- `API_KEY` - API key for MCP server authentication (optional)
- `LOG_LEVEL` - Logging level (debug, info, warn, error)

Optional (for Phase 1 external integrations):

- `MALWARE_PATROL_MCP_COMMAND` - Command to run Malware Patrol MCP server
- `VIRUSTOTAL_API_KEY` - VirusTotal API key
- `ABUSEIPDB_API_KEY` - AbuseIPDB API key

## Security Considerations

1. **API Keys**: Store securely, never commit to version control
2. **Rate Limiting**: Implement rate limiting per client
3. **Input Validation**: All tool inputs are validated
4. **Audit Logging**: All tool calls are logged
5. **Network Security**: Use HTTPS for API calls

## Monitoring

Monitor the MCP server for:

- Tool call success/failure rates
- API response times
- Error rates
- Authentication failures

Consider integrating with:
- CloudWatch (AWS)
- Datadog
- New Relic
- Custom logging solution

