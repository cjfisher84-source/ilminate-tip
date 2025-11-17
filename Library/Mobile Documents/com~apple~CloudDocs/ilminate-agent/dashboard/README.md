# Ilminate Agent Dashboard

Web-based dashboard for viewing security performance metrics from the Ilminate Agent.

## Features

- **Cyber Security Score**: Real-time security score calculation (0-100)
- **Protection Rate**: Percentage of threats successfully blocked
- **Response Time**: Average time to detect and respond to threats
- **False Positive Rate**: Accuracy of threat detection
- **Coverage**: Percentage of organization monitored
- **Threats Blocked Today**: Daily threat blocking statistics
- **Active Monitoring**: 24/7 monitoring status
- **Last Incident**: Time since last security incident

## Installation

The dashboard uses FastAPI which is already included in `requirements.txt`.

## Running the Dashboard

### Standalone Server

```bash
cd /path/to/ilminate-agent
python -m dashboard.server
```

The dashboard will be available at `http://localhost:8080`

### With Custom Port

```python
from dashboard.server import run_server
run_server(host="0.0.0.0", port=9000)
```

### Integration with Main Agent

Add to your main agent script:

```python
from dashboard.server import app
import uvicorn
import threading

def start_dashboard():
    uvicorn.run(app, host="0.0.0.0", port=8080)

# Start dashboard in background thread
dashboard_thread = threading.Thread(target=start_dashboard, daemon=True)
dashboard_thread.start()
```

## API Endpoints

### GET `/api/metrics`

Returns all security metrics:

```json
{
  "success": true,
  "data": {
    "cyber_score": 82,
    "protection_rate": 94.2,
    "response_time": 2.3,
    "false_positives": 0.8,
    "coverage": 99.1,
    "threats_blocked_today": 2420,
    "active_monitoring": "24/7",
    "last_incident": "2h ago",
    "timestamp": "2025-01-20T10:30:00"
  }
}
```

### GET `/api/timeline?days=30`

Returns timeline data for charts:

```json
{
  "success": true,
  "data": [
    {
      "date": "2025-01-20",
      "quarantined": 45,
      "delivered": 120,
      "blocked": 12
    }
  ]
}
```

### GET `/health`

Health check endpoint.

## Statistics File Format

The dashboard reads statistics from `apex_health_status.json` (or custom path):

```json
{
  "emails_processed": 10000,
  "emails_blocked": 500,
  "emails_quarantined": 8900,
  "false_positives": 80,
  "avg_response_time_seconds": 138,
  "endpoints_monitored": 50,
  "total_endpoints": 50,
  "last_incident_timestamp": "2025-01-20T08:30:00",
  "daily_stats": {
    "2025-01-20": {
      "quarantined": 45,
      "delivered": 120,
      "blocked": 12
    }
  }
}
```

## Customization

### Custom Statistics File

```python
from dashboard.metrics import SecurityMetrics

metrics = SecurityMetrics(stats_file="/path/to/custom/stats.json")
```

### Custom Metrics Calculation

Override methods in `SecurityMetrics` class to customize calculations.

## Integration with ilminate-apex

The dashboard can be integrated with the main ilminate-apex dashboard by:

1. Exposing the API endpoints via reverse proxy
2. Embedding the dashboard as an iframe
3. Using the API endpoints to populate the main dashboard

Example integration:

```javascript
// In ilminate-apex
const response = await fetch('http://agent-host:8080/api/metrics');
const metrics = await response.json();
// Use metrics.data to populate dashboard
```

