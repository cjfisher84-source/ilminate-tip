# Contributing to ilminate MCP Server

## Development Setup

1. **Clone and Install**
   ```bash
   npm install
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Build**
   ```bash
   npm run build
   ```

4. **Development Mode**
   ```bash
   npm run dev
   ```

## Project Structure

```
ilminate-mcp/
├── src/
│   ├── index.ts                 # Main MCP server entry point
│   ├── auth.ts                  # Authentication middleware
│   ├── tools/                   # MCP tool implementations
│   │   ├── analyze-email-threat.ts
│   │   ├── map-to-mitre-attack.ts
│   │   ├── check-domain-reputation.ts
│   │   ├── get-campaign-analysis.ts
│   │   └── scan-image-for-threats.ts
│   ├── utils/                   # Utility modules
│   │   ├── logger.ts
│   │   └── ilminate-api.ts
│   └── client/                  # MCP client for Phase 1
│       └── mcp-client.ts
├── examples/                    # Example usage
├── dist/                        # Compiled output
└── package.json
```

## Adding New Tools

To add a new MCP tool:

1. **Create tool file** in `src/tools/`:
   ```typescript
   // src/tools/my-new-tool.ts
   export async function myNewTool(input: MyInput): Promise<MyOutput> {
     // Implementation
   }
   ```

2. **Register tool** in `src/index.ts`:
   - Add to `ListToolsRequestSchema` handler
   - Add case in `CallToolRequestSchema` handler

3. **Update documentation** in `README.md`

## Testing

```bash
# Run tests (when implemented)
npm test

# Type checking
npm run type-check

# Linting
npm run lint
```

## Integration with ilminate-apex

This MCP server connects to ilminate-apex API endpoints. Ensure:

1. ilminate-apex is running and accessible
2. `ILMINATE_API_URL` is correctly configured
3. `ILMINATE_API_KEY` is set if required

## Deployment

See `DEPLOYMENT.md` for deployment instructions.

