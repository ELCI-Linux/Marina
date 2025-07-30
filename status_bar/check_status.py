#!/usr/bin/env python3
"""
Marina Status Bar Monitoring and Diagnostic Script

This script provides comprehensive monitoring and diagnostics for the Marina 
Dynamic Island status bar system.
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_status(item, status, details=""):
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {item:<30} {details}")

def check_processes():
    """Check if all required processes are running"""
    print_header("PROCESS STATUS")
    
    # Check Marina core
    try:
        result = subprocess.run(["/home/adminx/Marina/status_bar/start_marina_bar.sh", "status"], 
                              capture_output=True, text=True)
        marina_core_running = result.returncode == 0
        marina_pid = result.stdout.strip().split("PID: ")[-1].rstrip(")") if marina_core_running else "N/A"
        print_status("Marina Core", marina_core_running, f"PID: {marina_pid}")
    except Exception as e:
        print_status("Marina Core", False, f"Error: {e}")
    
    # Check py3status
    try:
        result = subprocess.run(["pgrep", "-f", "py3status"], capture_output=True, text=True)
        py3status_running = result.returncode == 0
        py3status_pids = result.stdout.strip().split('\n') if py3status_running else []
        print_status("py3status", py3status_running, f"PIDs: {', '.join(py3status_pids)}")
    except Exception as e:
        print_status("py3status", False, f"Error: {e}")
    
    # Check i3status
    try:
        result = subprocess.run(["pgrep", "-f", "i3status"], capture_output=True, text=True)
        i3status_running = result.returncode == 0
        print_status("i3status", i3status_running, "Backend process")
    except Exception as e:
        print_status("i3status", False, f"Error: {e}")

def check_files():
    """Check if all required files exist"""
    print_header("FILE SYSTEM STATUS")
    
    required_files = [
        "/home/adminx/Marina/status_bar/marina_bar_core.py",
        "/home/adminx/Marina/status_bar/modules/marina_daemons.py", 
        "/home/adminx/Marina/status_bar/modules/marina_ticker.py",
        "/home/adminx/.config/py3status/config",
        "/home/adminx/.config/py3status/modules/marina_daemons.py",
        "/home/adminx/.config/py3status/modules/marina_ticker.py",
    ]
    
    for file_path in required_files:
        exists = Path(file_path).exists()
        is_symlink = Path(file_path).is_symlink()
        status_detail = ""
        if is_symlink:
            target = Path(file_path).readlink()
            status_detail = f"→ {target}"
        elif exists:
            size = Path(file_path).stat().st_size
            status_detail = f"{size} bytes"
        
        print_status(Path(file_path).name, exists, status_detail)

def check_logs():
    """Check log files for recent activity"""
    print_header("LOG FILE STATUS")
    
    log_files = [
        "/tmp/marina_bar_core.log",
        "/tmp/marina_daemons.log", 
        "/tmp/marina_ticker.log"
    ]
    
    for log_path in log_files:
        log_file = Path(log_path)
        if log_file.exists():
            # Get file size and modification time
            stat = log_file.stat()
            size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime)
            age_seconds = (datetime.now() - mtime).total_seconds()
            
            # Check if recently modified (within last 30 seconds)
            recently_active = age_seconds < 30
            
            details = f"{size} bytes, modified {age_seconds:.0f}s ago"
            print_status(log_file.name, recently_active, details)
            
            # Show last few lines if there are errors
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-3:] if len(lines) >= 3 else lines
                    
                    for line in recent_lines:
                        if "ERROR" in line or "CRITICAL" in line:
                            print(f"    🚨 {line.strip()}")
            except Exception:
                pass
        else:
            print_status(log_file.name, False, "File not found")

def test_import():
    """Test importing the Marina core module"""
    print_header("MODULE IMPORT TEST")
    
    # Add the Marina status bar directory to the path
    marina_dir = "/home/adminx/Marina/status_bar"
    if marina_dir not in sys.path:
        sys.path.insert(0, marina_dir)
    
    try:
        from marina_bar_core import get_marina_bar_core
        print_status("marina_bar_core import", True, "Successfully imported")
        
        # Try to get the core instance
        try:
            core = get_marina_bar_core()
            print_status("Marina core instance", True, "Successfully created")
            
            # Try to get status data
            try:
                data = core.get_py3status_data()
                total_daemons = data.get("total_daemons", 0)
                active_daemons = data.get("active_daemons", 0)
                print_status("Status data retrieval", True, f"{active_daemons}/{total_daemons} daemons")
                
                # Show priority daemon states
                priority_daemons = data.get("priority_daemons", {})
                if priority_daemons:
                    print("\n  Priority Daemon States:")
                    for name, info in priority_daemons.items():
                        emoji = info.get("emoji", "❓")
                        state = info.get("state", "❓")
                        daemon_name = info.get("name", name)
                        print(f"    {emoji} {daemon_name}: {state}")
                        
            except Exception as e:
                print_status("Status data retrieval", False, f"Error: {e}")
        except Exception as e:
            print_status("Marina core instance", False, f"Error: {e}")
    except Exception as e:
        print_status("marina_bar_core import", False, f"Error: {e}")

def test_modules():
    """Test the py3status modules"""
    print_header("PY3STATUS MODULE TEST")
    
    # Test marina_daemons module
    try:
        result = subprocess.run([
            "timeout", "3",
            "python3", "/home/adminx/Marina/status_bar/modules/marina_daemons.py"
        ], capture_output=True, text=True, cwd="/home/adminx/Marina/status_bar")
        
        daemons_working = "Status:" in result.stdout and len(result.stdout) > 50
        print_status("marina_daemons module", daemons_working, 
                    "Produces status output" if daemons_working else "No output")
        
        if result.stderr:
            print(f"    🚨 Stderr: {result.stderr[:100]}...")
            
    except Exception as e:
        print_status("marina_daemons module", False, f"Error: {e}")
    
    # Test marina_ticker module
    try:
        result = subprocess.run([
            "timeout", "3", 
            "python3", "/home/adminx/Marina/status_bar/modules/marina_ticker.py"
        ], capture_output=True, text=True, cwd="/home/adminx/Marina/status_bar")
        
        ticker_working = "Ticker:" in result.stdout and len(result.stdout) > 30
        print_status("marina_ticker module", ticker_working,
                    "Produces ticker output" if ticker_working else "No output")
        
        if result.stderr:
            print(f"    🚨 Stderr: {result.stderr[:100]}...")
            
    except Exception as e:
        print_status("marina_ticker module", False, f"Error: {e}")

def show_summary():
    """Show overall system summary"""
    print_header("MARINA STATUS BAR SUMMARY")
    
    # Overall status
    try:
        # Check if Marina core is responding
        sys.path.insert(0, "/home/adminx/Marina/status_bar")
        from marina_bar_core import get_marina_bar_core
        core = get_marina_bar_core()
        data = core.get_py3status_data()
        
        total_daemons = data.get("total_daemons", 0)
        active_daemons = data.get("active_daemons", 0)
        ticker_message = data.get("ticker_message", "")
        expanded = data.get("expanded", False)
        
        print(f"🌊 Marina Dynamic Island Status Bar")
        print(f"   Monitoring {total_daemons} daemons ({active_daemons} active)")
        print(f"   Current state: {'Expanded' if expanded else 'Compact'}")
        if ticker_message:
            print(f"   Latest message: {ticker_message[:60]}...")
        
        # System status
        system_status = data.get("system_status", {})
        cpu = system_status.get("cpu", 0)
        memory = system_status.get("memory", 0)
        print(f"   System: CPU {cpu:.1f}%, Memory {memory:.1f}%")
        
        print(f"   Status: ✅ OPERATIONAL")
        
    except Exception as e:
        print(f"   Status: ❌ ERROR - {e}")

def main():
    print(f"Marina Status Bar Diagnostic Report")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_processes()
    check_files()
    check_logs()
    test_import()
    test_modules()
    show_summary()
    
    print(f"\n{'='*60}")
    print("For detailed logs, check:")
    print("  - Marina Core: /tmp/marina_bar_core.log")
    print("  - Daemons Module: /tmp/marina_daemons.log") 
    print("  - Ticker Module: /tmp/marina_ticker.log")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
