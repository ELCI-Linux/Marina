# Marina Auto-Uber Module

Intelligent rideshare automation with location-based triggers for Marina AI system.

## Features

- **Order-on-Arrival**: Automatically order Uber when you arrive at a location
- **Order-on-Approach**: Pre-order Uber when approaching a location
- **Order-to-Appointment**: Schedule rides based on calendar appointments
- **Location Monitoring**: GPS, WiFi, and IP-based location tracking
- **Calendar Integration**: Sync with Google Calendar, Outlook, local calendars
- **Safety Controls**: Confirmation prompts, daily limits, budget constraints
- **Ceto Integration**: Full daemon management through Marina's Ceto system

## Components

### Core Modules

- `auto_uber_daemon.py` - Main daemon with trigger logic
- `uber_client.py` - Uber API client with sandbox support
- `location_monitor.py` - Location tracking and geofencing
- `scheduler.py` - Appointment-based scheduling
- `autouber_cli.py` - Command-line interface

### Configuration

- `config.json` - Main configuration file
- `Ceto/daemons/autouber.json` - Ceto daemon configuration

## Installation

1. Install dependencies:
```bash
pip install -r /home/adminx/Marina/autouber/requirements.txt
```

2. Configure Uber API credentials in `config.json`:
```json
{
  "uber": {
    "client_id": "your_uber_client_id",
    "client_secret": "your_uber_client_secret",
    "sandbox_mode": false
  }
}
```

3. Register with Ceto:
```bash
python3 /home/adminx/Marina/Ceto/cetoctl.py register autouber
```

## Usage

### CLI Commands

```bash
# Start the daemon
python3 /home/adminx/Marina/autouber/autouber_cli.py start

# Order Uber when arriving at theater
python3 /home/adminx/Marina/autouber/autouber_cli.py on-arrival 37.7749,-122.4194 37.7849,-122.4094

# Order Uber when approaching bar (100m radius)
python3 /home/adminx/Marina/autouber/autouber_cli.py on-approach 37.7749,-122.4194 37.7849,-122.4094 --radius 100

# Order Uber for 8pm appointment
python3 /home/adminx/Marina/autouber/autouber_cli.py to-appointment 37.7749,-122.4194 37.7849,-122.4094 "2024-01-20T20:00:00"

# Show status
python3 /home/adminx/Marina/autouber/autouber_cli.py status

# List active requests
python3 /home/adminx/Marina/autouber/autouber_cli.py list --history
```

### Ceto Management

```bash
# Start via Ceto
python3 /home/adminx/Marina/Ceto/cetoctl.py start autouber

# Stop via Ceto
python3 /home/adminx/Marina/Ceto/cetoctl.py stop autouber

# Check status
python3 /home/adminx/Marina/Ceto/cetoctl.py status autouber

# View logs
python3 /home/adminx/Marina/Ceto/cetoctl.py logs autouber
```

### Python API

```python
from autouber import AutoUberDaemon
from datetime import datetime, timedelta

# Create daemon instance
daemon = AutoUberDaemon()
daemon.start()

# Set up triggers
arrival_id = daemon.order_on_arrival(
    location=(37.7749, -122.4194),
    destination=(37.7849, -122.4094),
    radius_m=200
)

approach_id = daemon.order_on_approach(
    location=(37.7749, -122.4194),
    destination=(37.7849, -122.4094),
    radius_m=100
)

appointment_id = daemon.order_to_appointment(
    origin=(37.7749, -122.4194),
    destination=(37.7849, -122.4094),
    appointment_time=datetime.now() + timedelta(hours=2),
    buffer_minutes=10
)

# Check active requests
active = daemon.get_active_requests()
print(f"Active requests: {len(active)}")

# Stop daemon
daemon.stop()
```

## Configuration Options

### Uber API Settings
- `client_id` - Uber Developer App client ID
- `client_secret` - Uber Developer App client secret  
- `sandbox_mode` - Use sandbox for testing (default: true)
- `default_ride_type` - Default ride type (UberX, UberBlack, etc.)

### Location Settings
- `update_interval_seconds` - GPS update frequency (default: 30)
- `accuracy_threshold_meters` - Required location accuracy (default: 50)
- `geofence_check_interval` - Geofence check frequency (default: 10)

### Scheduler Settings
- `calendar_integration` - Enable calendar sync (default: true)
- `default_buffer_minutes` - Default appointment buffer (default: 5)
- `early_arrival_minutes` - Early arrival preference (default: 2)

### Safety Settings
- `require_confirmation` - Require user confirmation (default: true)
- `max_daily_requests` - Daily request limit (default: 10)
- `home_location` - Default home coordinates

## Trigger Types

### Order-on-Arrival
Triggers when you arrive at a specific location and settle there (30 second delay).

**Use cases:**
- Order ride home after arriving at theater/restaurant
- Auto-request pickup after work meetings
- Schedule departure from events

### Order-on-Approach  
Pre-orders rides when you're approaching a location, timing arrival with your exit.

**Use cases:**
- Uber arrives as you leave the bar
- Ride ready when exiting conference
- Minimize wait time at departure

### Order-to-Appointment
Calculates optimal order time based on pickup ETA, travel time, and appointment schedule.

**Use cases:**
- Never be late to meetings
- Automatic ride scheduling from calendar
- Buffer time for traffic/delays

## Location Sources

The system uses multiple location sources in priority order:

1. **GPS** - Hardware GPS (requires system integration)
2. **WiFi Positioning** - Based on nearby WiFi networks
3. **IP Geolocation** - Approximate location from IP address
4. **Mock Location** - For testing purposes

## Calendar Integration

Supports multiple calendar sources:

- **Google Calendar** - Via Google Calendar API
- **Outlook Calendar** - Via Microsoft Graph API  
- **Local Calendars** - ICS files from Evolution, Thunderbird
- **Marina Tasks** - Internal Marina task system

Events are automatically analyzed for transportation needs based on:
- Event location (non-home addresses)
- Keywords (meeting, appointment, restaurant, etc.)
- Event type and description

## Safety Features

- **Confirmation Prompts** - Optional user confirmation before ordering
- **Daily Limits** - Configurable maximum requests per day
- **Budget Constraints** - Per-request spending limits
- **Location Validation** - Reasonable distance checks
- **Emergency Cancel** - Quick cancellation options

## Integration with Marina

### Perception Module
- Location data from GPS and sensors
- Movement pattern recognition
- Context awareness

### Brain Module  
- Calendar and task integration
- Decision making logic
- User preference learning

### Notification System
- Ride status updates
- Confirmation requests
- Error alerts

## API Endpoints

When running, the daemon exposes REST API endpoints:

- `GET /status` - Daemon status and metrics
- `GET /requests` - List active requests
- `POST /requests` - Create new request
- `DELETE /requests/{id}` - Cancel request

## Logging

Logs are written to:
- `/home/adminx/Marina/logs/autouber.log` - Main daemon log
- `/home/adminx/Marina/logs/notifications.json` - Notification events

Log rotation is configured for 10MB files with 5 file retention.

## Security

The module implements several security measures:

- **Sandboxed API Access** - Limited file system access
- **Credential Management** - Secure API key storage
- **Network Restrictions** - Only required endpoints accessible
- **User Confirmation** - Prevents unauthorized rides
- **Rate Limiting** - Daily request limits

## Troubleshooting

### Common Issues

**Daemon won't start:**
- Check Uber API credentials in config.json
- Verify Python dependencies installed
- Check log file for specific errors

**Location not updating:**
- Ensure location sources are accessible
- Check GPS hardware availability
- Verify network connectivity for IP/WiFi location

**Rides not triggering:**
- Confirm geofence radius settings
- Check location accuracy threshold
- Verify Uber API credentials and sandbox mode

**Calendar integration not working:**
- Check calendar file paths and permissions
- Verify calendar API credentials (Google/Outlook)
- Ensure Marina task files are accessible

### Debug Commands

```bash
# Check daemon health
python3 -c "from autouber import AutoUberDaemon; daemon = AutoUberDaemon(); print('OK')"

# Test location services
python3 /home/adminx/Marina/autouber/location_monitor.py

# Test Uber API
python3 /home/adminx/Marina/autouber/uber_client.py

# Test scheduler
python3 /home/adminx/Marina/autouber/scheduler.py
```

## Development

### Adding New Trigger Types

1. Add new TriggerMode enum value
2. Implement handler in `_process_active_requests()`
3. Add convenience method to AutoUberDaemon
4. Update CLI and API interfaces

### Extending Location Sources

1. Add method to LocationMonitor class
2. Register in `_init_location_sources()`
3. Implement error handling and fallback
4. Add configuration options

### Custom Calendar Integration

1. Add sync method to UberScheduler
2. Register in `_init_calendar_sources()`
3. Implement event parsing logic
4. Add authentication if required

## License

Part of the Marina AI System. See main project license.

## Support

For issues and feature requests, check the Marina project documentation or logs in `/home/adminx/Marina/logs/`.
