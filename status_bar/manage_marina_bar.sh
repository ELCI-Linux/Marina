#!/bin/bash

# Marina Status Bar Management Script
# Provides clean start/stop/restart/status operations for py3status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="/home/adminx/.config/py3status/config"
LOG_FILE="/tmp/marina_status_bar.log"
PID_FILE="/tmp/marina_status_bar.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}🌊 Marina Status Bar Manager${NC}"
    echo "================================"
}

get_py3status_pids() {
    pgrep -f "py3status.*${CONFIG_FILE}"
}

start_marina_bar() {
    print_status
    echo "🚀 Starting Marina Status Bar..."
    
    # Check if already running
    local pids=$(get_py3status_pids)
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}⚠️  Marina Status Bar is already running (PID: $pids)${NC}"
        return 1
    fi
    
    # Clean up any stale processes
    pkill -f "py3status.*config" 2>/dev/null || true
    sleep 1
    
    # Start py3status
    echo "📝 Using config: $CONFIG_FILE"
    echo "📋 Logging to: $LOG_FILE"
    
    py3status -c "$CONFIG_FILE" > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ Marina Status Bar started successfully (PID: $pid)${NC}"
        echo "📊 Status bar modules:"
        echo "   • marina_daemons: Daemon status display"
        echo "   • marina_ticker: Natural language messages" 
        echo "   • tztime: Clock display"
        return 0
    else
        echo -e "${RED}❌ Failed to start Marina Status Bar${NC}"
        echo "Check log file: $LOG_FILE"
        return 1
    fi
}

stop_marina_bar() {
    print_status
    echo "⏹️  Stopping Marina Status Bar..."
    
    local pids=$(get_py3status_pids)
    if [ -z "$pids" ]; then
        echo -e "${YELLOW}⚠️  Marina Status Bar is not running${NC}"
        return 1
    fi
    
    # Stop processes gracefully
    echo "🔄 Stopping py3status processes: $pids"
    kill $pids 2>/dev/null
    
    # Wait for graceful shutdown
    sleep 3
    
    # Force kill if still running
    local remaining=$(get_py3status_pids)
    if [ -n "$remaining" ]; then
        echo "💀 Force killing remaining processes: $remaining"
        kill -9 $remaining 2>/dev/null
    fi
    
    # Cleanup
    [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
    
    echo -e "${GREEN}✅ Marina Status Bar stopped${NC}"
    return 0
}

status_marina_bar() {
    print_status
    
    local pids=$(get_py3status_pids)
    if [ -n "$pids" ]; then
        echo -e "${GREEN}✅ Marina Status Bar is running${NC}"
        echo "📊 Process details:"
        ps aux | head -1
        ps aux | grep -E "($pids)" | grep -v grep
        
        echo ""
        echo "📋 Recent log entries:"
        if [ -f "$LOG_FILE" ]; then
            tail -n 5 "$LOG_FILE" | grep -o '"full_text": "[^"]*"' | sed 's/"full_text": "//g' | sed 's/"$//g' | head -3
        fi
        
        echo ""
        echo "🎛️  Available modules:"
        echo "   • marina_daemons: $([ -f /home/adminx/.config/py3status/modules/marina_daemons.py ] && echo "✅ Available" || echo "❌ Missing")"
        echo "   • marina_ticker: $([ -f /home/adminx/.config/py3status/modules/marina_ticker.py ] && echo "✅ Available" || echo "❌ Missing")"
        echo "   • marina_mini_menu: $([ -f /home/adminx/.config/py3status/modules/marina_mini_menu.py ] && echo "✅ Available (disabled)" || echo "❌ Missing")"
        
    else
        echo -e "${RED}❌ Marina Status Bar is not running${NC}"
        
        # Check for issues
        echo ""
        echo "🔍 Diagnostics:"
        echo "   • Config file: $([ -f "$CONFIG_FILE" ] && echo "✅ Found" || echo "❌ Missing")"
        echo "   • Log file: $([ -f "$LOG_FILE" ] && echo "✅ Found" || echo "❌ Missing")"
        
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "📋 Last log entries:"
            tail -n 5 "$LOG_FILE"
        fi
    fi
    
    return 0
}

restart_marina_bar() {
    print_status
    echo "🔄 Restarting Marina Status Bar..."
    
    stop_marina_bar
    sleep 2
    start_marina_bar
}

show_help() {
    print_status
    echo "Usage: $0 {start|stop|restart|status|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the Marina Status Bar"
    echo "  stop     - Stop the Marina Status Bar"  
    echo "  restart  - Restart the Marina Status Bar"
    echo "  status   - Show current status and diagnostics"
    echo "  help     - Show this help message"
    echo ""
    echo "Files:"
    echo "  Config:  $CONFIG_FILE"
    echo "  Log:     $LOG_FILE"
    echo "  PID:     $PID_FILE"
}

# Main command handling
case "$1" in
    start)
        start_marina_bar
        ;;
    stop)
        stop_marina_bar
        ;;
    restart)
        restart_marina_bar
        ;;
    status)
        status_marina_bar
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Invalid command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

exit $?
