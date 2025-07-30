#!/usr/bin/env python3
"""
Auto-Uber Test Script
Demonstrates the functionality of Marina's Auto-Uber system
"""

import time
from datetime import datetime, timedelta

from auto_uber_daemon import AutoUberDaemon

def test_auto_uber():
    """Test Auto-Uber functionality"""
    print("🚖 Testing Marina Auto-Uber System")
    print("=" * 50)
    
    # Create daemon instance
    print("\n1. Creating Auto-Uber daemon...")
    daemon = AutoUberDaemon()
    
    # Start the daemon
    print("2. Starting daemon...")
    daemon.start()
    time.sleep(2)  # Let it initialize
    
    # Test coordinates (San Francisco area)
    theater_location = (37.7749, -122.4194)  # Theater
    home_location = (37.7849, -122.4094)     # Home
    office_location = (37.7949, -122.4294)   # Office
    
    print("\n3. Setting up triggers...")
    
    # Test order-on-arrival
    print("   • Setting up order-on-arrival at theater → home")
    arrival_id = daemon.order_on_arrival(
        location=theater_location,
        destination=home_location,
        radius_m=150,
        auto_confirm=True
    )
    print(f"     Trigger ID: {arrival_id}")
    
    # Test order-on-approach
    print("   • Setting up order-on-approach at office → theater")
    approach_id = daemon.order_on_approach(
        location=office_location,
        destination=theater_location,
        radius_m=200,
        auto_confirm=True
    )
    print(f"     Trigger ID: {approach_id}")
    
    # Test order-to-appointment
    appointment_time = datetime.now() + timedelta(minutes=5)
    print(f"   • Setting up order-to-appointment at {appointment_time.strftime('%H:%M')}")
    appointment_id = daemon.order_to_appointment(
        origin=home_location,
        destination=office_location,
        appointment_time=appointment_time,
        buffer_minutes=3,
        auto_confirm=True
    )
    print(f"     Trigger ID: {appointment_id}")
    
    # Show active requests
    print("\n4. Active requests:")
    active = daemon.get_active_requests()
    for i, request in enumerate(active, 1):
        print(f"   {i}. {request.id}")
        print(f"      Mode: {request.trigger_mode.value}")
        print(f"      Origin: {request.origin}")
        print(f"      Destination: {request.destination}")
        if request.appointment_time:
            print(f"      Appointment: {request.appointment_time}")
        print()
    
    print(f"Total active requests: {len(active)}")
    
    # Test location monitoring
    print("\n5. Testing location monitoring...")
    print("   Current location:", daemon.location_monitor.get_current_location())
    print("   Location fresh:", daemon.location_monitor.is_location_fresh())
    
    # Test Uber client
    print("\n6. Testing Uber API (sandbox mode)...")
    products = daemon.uber_client.get_available_products(theater_location)
    print(f"   Available products: {len(products)}")
    
    estimates = daemon.uber_client.get_price_estimates(theater_location, home_location)
    if estimates:
        for estimate in estimates:
            print(f"   {estimate['display_name']}: {estimate['estimate']}")
    
    # Test scheduler
    print("\n7. Testing scheduler...")
    scheduled = daemon.scheduler.get_scheduled_rides()
    print(f"   Scheduled rides: {len(scheduled)}")
    
    # Cleanup
    print("\n8. Cleaning up...")
    daemon.remove_request(arrival_id)
    daemon.remove_request(approach_id) 
    daemon.remove_request(appointment_id)
    
    remaining = daemon.get_active_requests()
    print(f"   Remaining active requests: {len(remaining)}")
    
    # Stop daemon
    print("9. Stopping daemon...")
    daemon.stop()
    
    print("\n✅ Auto-Uber test completed successfully!")
    print("\nNatural Language Examples:")
    print("• 'Order me an Uber when I get to the theater'")
    print("• 'Have one pull up as I'm leaving this bar'") 
    print("• 'Make sure I'm at the station by 4pm. You decide when to call it.'")

if __name__ == "__main__":
    test_auto_uber()
