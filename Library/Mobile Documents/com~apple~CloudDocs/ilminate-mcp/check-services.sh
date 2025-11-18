#!/bin/bash

echo "Checking ilminate services..."
echo ""

# APEX Bridge
echo -n "APEX Bridge (localhost:8888): "
if curl -s http://localhost:8888/health 2>/dev/null | grep -q "healthy"; then
    echo "✓ Running"
else
    echo "✗ Not running"
fi

# ilminate-apex (if running)
echo -n "ilminate-apex (localhost:3000): "
if curl -s http://localhost:3000/health 2>/dev/null | grep -q "ok\|healthy"; then
    echo "✓ Running"
else
    echo "✗ Not running (optional)"
fi

# ilminate-portal (if running)
echo -n "ilminate-portal (localhost:3001): "
if curl -s http://localhost:3001/health 2>/dev/null | grep -q "ok\|healthy"; then
    echo "✓ Running"
else
    echo "✗ Not running (optional)"
fi

# ilminate-siem (if running)
echo -n "ilminate-siem (localhost:55000): "
if curl -s http://localhost:55000/health 2>/dev/null | grep -q "ok\|healthy"; then
    echo "✓ Running"
else
    echo "✗ Not running (optional)"
fi

echo ""
echo "Done!"

