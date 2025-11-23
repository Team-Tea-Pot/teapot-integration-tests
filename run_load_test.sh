#!/bin/bash
# Locust load test runner

echo "=================================================="
echo "TeaPot User Service Load Testing"
echo "=================================================="

# Default values
HOST="${1:-http://localhost:8080}"
USERS="${2:-10}"
SPAWN_RATE="${3:-2}"
DURATION="${4:-60s}"
MODE="${5:-web}"

echo "Configuration:"
echo "  Host: $HOST"
echo "  Users: $USERS"
echo "  Spawn Rate: $SPAWN_RATE"
echo "  Duration: $DURATION"
echo "  Mode: $MODE"
echo "=================================================="

# Install locust if not already installed
if ! command -v locust &> /dev/null; then
    echo "Installing Locust..."
    pip install locust
fi

if [ "$MODE" = "web" ]; then
    echo "Starting Locust web UI..."
    echo "Open http://localhost:8089 in your browser"
    locust -f tests/performance/locustfile.py --host="$HOST"
else
    echo "Running headless load test..."
    locust -f tests/performance/locustfile.py \
        --host="$HOST" \
        --users "$USERS" \
        --spawn-rate "$SPAWN_RATE" \
        --run-time "$DURATION" \
        --headless \
        --html=locust_report.html
    
    echo ""
    echo "Report saved to: locust_report.html"
fi
