"""
FastAPI Web Server for Ilminate Agent Dashboard
Serves security performance metrics and dashboard UI
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Template
import os
from pathlib import Path
from typing import Dict

from dashboard.metrics import SecurityMetrics

app = FastAPI(
    title="Ilminate Agent Dashboard",
    description="Security Performance Dashboard for Ilminate Agent",
    version="1.0.0"
)

# Initialize metrics calculator
# Can be overridden with APEX_STATS_FILE environment variable
stats_file = os.environ.get('APEX_STATS_FILE')
metrics = SecurityMetrics(stats_file=stats_file)

# Templates directory
templates_dir = Path(__file__).parent / "templates"


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard page"""
    metrics_data = metrics.get_all_metrics()
    timeline_data = metrics.get_timeline_data(30)
    
    # Load and render template
    template_path = templates_dir / "dashboard.html"
    with open(template_path, 'r') as f:
        template = Template(f.read())
    
    html_content = template.render(
        metrics=metrics_data,
        timeline=timeline_data
    )
    
    return HTMLResponse(content=html_content)


@app.get("/api/metrics", response_class=JSONResponse)
async def get_metrics():
    """API endpoint for security metrics"""
    return {
        "success": True,
        "data": metrics.get_all_metrics()
    }


@app.get("/api/timeline", response_class=JSONResponse)
async def get_timeline(days: int = 30):
    """API endpoint for timeline data"""
    return {
        "success": True,
        "data": metrics.get_timeline_data(days)
    }


@app.get("/health", response_class=JSONResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ilminate-agent-dashboard"
    }


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the dashboard server"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()

