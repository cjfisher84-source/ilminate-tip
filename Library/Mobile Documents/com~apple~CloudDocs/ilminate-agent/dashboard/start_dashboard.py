#!/usr/bin/env python3
"""
Start the Ilminate Agent Dashboard Server
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.server import run_server
import argparse


def main():
    parser = argparse.ArgumentParser(description='Start Ilminate Agent Dashboard')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to (default: 8080)')
    parser.add_argument('--stats-file', help='Path to statistics JSON file')
    
    args = parser.parse_args()
    
    # Set custom stats file if provided
    if args.stats_file:
        os.environ['APEX_STATS_FILE'] = args.stats_file
    
    print(f"Starting Ilminate Agent Dashboard on http://{args.host}:{args.port}")
    print(f"Stats file: {args.stats_file or 'apex_health_status.json'}")
    
    run_server(host=args.host, port=args.port)


if __name__ == '__main__':
    main()

