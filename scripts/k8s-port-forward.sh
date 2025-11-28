#!/bin/bash
# Port forwarding script for Kubernetes services
# This keeps port-forwards running in the background

set -e

NAMESPACE="task-manager"
PID_DIR="/tmp/k8s-port-forward-pids"

mkdir -p "$PID_DIR"

# Function to start port forward
start_port_forward() {
    local service=$1
    local port=$2
    local pid_file="$PID_DIR/${service}.pid"
    
    # Check if already running
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Port forward for $service already running (PID: $pid)"
            return
        fi
    fi
    
    # Start port forward in background
    kubectl port-forward -n "$NAMESPACE" "svc/$service" "$port:$port" > /dev/null 2>&1 &
    local new_pid=$!
    echo "$new_pid" > "$pid_file"
    echo "Started port forward for $service on port $port (PID: $new_pid)"
}

# Function to stop port forward
stop_port_forward() {
    local service=$1
    local pid_file="$PID_DIR/${service}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid" 2>/dev/null || true
            echo "Stopped port forward for $service (PID: $pid)"
        fi
        rm -f "$pid_file"
    fi
}

# Function to stop all port forwards
stop_all() {
    echo "Stopping all port forwards..."
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local service=$(basename "$pid_file" .pid)
            stop_port_forward "$service"
        fi
    done
}

# Function to show status
show_status() {
    echo "Port forward status:"
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local service=$(basename "$pid_file" .pid)
            local pid=$(cat "$pid_file")
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "  $service: running (PID: $pid)"
            else
                echo "  $service: stopped (stale PID file)"
                rm -f "$pid_file"
            fi
        fi
    done
}

# Main command handling
case "${1:-start}" in
    start)
        echo "Starting port forwards for task-manager services..."
        start_port_forward "postgres" "5432"
        start_port_forward "rest-api" "8000"
        start_port_forward "ui" "3000"
        echo ""
        echo "Services available at:"
        echo "  PostgreSQL: localhost:5432"
        echo "  API: http://localhost:8000"
        echo "  UI: http://localhost:3000"
        ;;
    stop)
        stop_all
        ;;
    status)
        show_status
        ;;
    restart)
        stop_all
        sleep 2
        $0 start
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
