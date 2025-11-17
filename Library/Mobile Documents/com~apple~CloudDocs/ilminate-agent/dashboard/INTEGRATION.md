# Dashboard Integration Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Dashboard Server

```bash
python -m dashboard.start_dashboard
```

Or with custom options:

```bash
python -m dashboard.start_dashboard --host 0.0.0.0 --port 9000 --stats-file /path/to/stats.json
```

### 3. Access Dashboard

Open your browser to: `http://localhost:8080`

## Integration with Main Agent

### Option 1: Background Thread

Add to your main agent script (`apex_main_system.py`):

```python
from dashboard.server import app
import uvicorn
import threading

def start_dashboard():
    """Start dashboard in background thread"""
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")

# Start dashboard
dashboard_thread = threading.Thread(target=start_dashboard, daemon=True)
dashboard_thread.start()
```

### Option 2: Separate Process

Run dashboard as separate process:

```bash
# Terminal 1: Main agent
python apex_main_system.py

# Terminal 2: Dashboard
python -m dashboard.start_dashboard
```

### Option 3: Systemd Service

Create `/etc/systemd/system/ilminate-dashboard.service`:

```ini
[Unit]
Description=Ilminate Agent Dashboard
After=network.target

[Service]
Type=simple
User=ilminate
WorkingDirectory=/opt/ilminate-agent
ExecStart=/usr/bin/python3 -m dashboard.start_dashboard --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable ilminate-dashboard
sudo systemctl start ilminate-dashboard
```

## Updating Statistics

The dashboard reads from `apex_health_status.json`. Update this file with your agent statistics:

```python
import json
from datetime import datetime

stats = {
    "emails_processed": total_processed,
    "emails_blocked": total_blocked,
    "emails_quarantined": total_quarantined,
    "false_positives": false_positive_count,
    "avg_response_time_seconds": avg_response_seconds,
    "endpoints_monitored": active_endpoints,
    "total_endpoints": total_endpoints,
    "last_incident_timestamp": datetime.now().isoformat(),
    "daily_stats": {
        date.isoformat(): {
            "quarantined": day_quarantined,
            "delivered": day_delivered,
            "blocked": day_blocked
        }
        for date, day_quarantined, day_delivered, day_blocked in daily_data
    }
}

with open('apex_health_status.json', 'w') as f:
    json.dump(stats, f, indent=2)
```

## Integration with ilminate-apex Dashboard

### Option 1: API Proxy

Add to ilminate-apex API routes:

```typescript
// src/app/api/agent-metrics/route.ts
export async function GET(request: NextRequest) {
  const agentUrl = process.env.AGENT_DASHBOARD_URL || 'http://localhost:8080';
  const response = await fetch(`${agentUrl}/api/metrics`);
  const data = await response.json();
  return NextResponse.json(data);
}
```

### Option 2: Direct Integration

Use the metrics in your dashboard component:

```typescript
// In ilminate-apex component
const [agentMetrics, setAgentMetrics] = useState(null);

useEffect(() => {
  fetch('http://agent-host:8080/api/metrics')
    .then(res => res.json())
    .then(data => setAgentMetrics(data.data));
}, []);
```

### Option 3: Embed as Iframe

```tsx
<iframe 
  src="http://agent-host:8080" 
  width="100%" 
  height="600px"
  style={{ border: 'none' }}
/>
```

## Custom Metrics

Override `SecurityMetrics` class methods:

```python
from dashboard.metrics import SecurityMetrics

class CustomMetrics(SecurityMetrics):
    def calculate_cyber_score(self) -> int:
        # Custom calculation
        return custom_score
    
    def get_protection_rate(self) -> float:
        # Custom protection rate calculation
        return custom_rate

# Use custom metrics
from dashboard.server import app
app.state.metrics = CustomMetrics()
```

## Security Considerations

1. **Authentication**: Add authentication middleware:

```python
from fastapi import Depends, HTTPException, Header

async def verify_token(x_api_key: str = Header(...)):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.get("/api/metrics")
async def get_metrics(token: str = Depends(verify_token)):
    return {"success": True, "data": metrics.get_all_metrics()}
```

2. **HTTPS**: Use reverse proxy (nginx/traefik) with SSL

3. **Firewall**: Restrict access to internal network only

4. **Rate Limiting**: Add rate limiting middleware

## Troubleshooting

### Dashboard not loading

- Check if port 8080 is available: `lsof -i :8080`
- Check logs for errors
- Verify `apex_health_status.json` exists and is valid JSON

### Metrics showing defaults

- Ensure statistics file is being updated by agent
- Check file path matches `stats_file` parameter
- Verify JSON structure matches expected format

### Chart not rendering

- Check browser console for JavaScript errors
- Verify Chart.js CDN is accessible
- Check network tab for failed requests

