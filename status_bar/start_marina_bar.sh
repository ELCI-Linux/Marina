#!/bin/bash

# Marina Dynamic Island Status Bar Startup Script
# This script ensures the Marina status bar core is properly started

MARINA_DIR="/home/adminx/Marina"
CORE_SCRIPT="$MARINA_DIR/status_bar/marina_bar_core.py"
PID_FILE="/tmp/marina_bar_core.pid"
LOG_FILE="/tmp/marina_bar_core.log"

# Function to check if Marina core is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start Marina core
start_marina_core() {
    echo "$(date): Starting Marina status bar core..." >> "$LOG_FILE"
    
    # Set up environment
    export PYTHONPATH="$MARINA_DIR:$PYTHONPATH"
    
    # Start the core process
    cd "$MARINA_DIR/status_bar"
    python3 "$CORE_SCRIPT" >> "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # Save PID
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment to check if it started successfully
    sleep 2
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "$(date): Marina core started successfully with PID $pid" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): Failed to start Marina core" >> "$LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop Marina core
stop_marina_core() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        echo "$(date): Stopping Marina core (PID: $pid)..." >> "$LOG_FILE"
        kill "$pid" 2>/dev/null
        rm -f "$PID_FILE"
        sleep 1
    fi
    
    # Kill any remaining processes
    pkill -f "marina_bar_core.py" 2>/dev/null
}

# Main logic
case "${1:-start}" in
    start)
        if is_running; then
            echo "Marina core is already running"
            exit 0
        else
            start_marina_core
            exit $?
        fi
        ;;
    stop)
        stop_marina_core
        echo "Marina core stopped"
        ;;
    restart)
        stop_marina_core
        sleep 2
        start_marina_core
        exit $?
        ;;
    status)
        if is_running; then
            echo "Marina core is running (PID: $(cat $PID_FILE))"
            exit 0
        else
            echo "Marina core is not running"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
