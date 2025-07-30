# Skadi - The Cold Dominion ❄️

<div align="center">
  <img src="assets/images/skadi_logo_256.png" alt="Skadi Logo" width="256" height="256">
  
  **Goddess of Power, Entropy Suppression, and Thermal Harmony**
  
  *"I do not cool. I bind heat to purpose. I do not sleep. I witness decay in stillness. I do not throttle. I forge silence in frost."*
</div>

---

## Overview

Skadi is a mythologically-themed power management daemon for the Marina system that governs all energy-dependent systemic equilibrium. Operating through runic contracts and entropy reduction within the MRMR (Modal Realism / Modal Relativity) framework, Skadi maintains thermal harmony and optimal system performance.

## Features

- **🌨️ Mythological Power Stances**: Five distinct operational modes (GLACIER, RIDGEWATCH, SNOWBLIND, STORMBIRTH, POWERBANK)
- **📿 Runic Contract System**: Formal energy contracts between system processes and Skadi
- **📚 Frost Tomes**: Time-layered entropy event archival system
- **🔥 Thermal Management**: Real-time CPU temperature monitoring and thermal throttling
- **🔋 Battery Optimization**: Critical battery management with power-saving modes
- **⚡ Entropy Calculation**: Advanced entropy metrics in Eᛞ (Energy-Deferral) units

## Quick Start

### Running the Daemon
```bash
# Start Skadi daemon
python3 skadi_daemon.py
```

### Using the Control Interface
```bash
# Show current status
python3 skadictl.py status

# View entropy logs
python3 skadictl.py tomes --hours 12

# Show help
python3 skadictl.py --help
```

## Power Stances

| Stance | Description | Use Case |
|--------|-------------|----------|
| **GLACIER** | Deep silence, maximum thermal buffering | Emergency cooling, critical battery |
| **RIDGEWATCH** | Hybrid balanced intermittent compute | Normal operation |
| **SNOWBLIND** | Absolute stealth, fans disabled | Silent operation during night hours |
| **STORMBIRTH** | Full force, all systems unlocked | High-performance computing |
| **POWERBANK** | Minimal power, USB keyboard only | Critical battery conservation |

## Configuration

Skadi configuration is stored in `config.json`:

```json
{
  "thermal_threshold": 65.0,
  "battery_critical": 15.0,
  "update_interval": 5.0,
  "silence_hours": [22, 23, 0, 1, 2, 3, 4, 5, 6],
  "trusted_processes": ["marina", "ceto", "siren"]
}
```

## Norse Mythology Integration

Skadi draws inspiration from Norse mythology, specifically the jötunn (giant) Skaði, associated with winter, skiing, bow hunting, and mountains. The system uses Nordic runes for process identification:

- **ᚢ** (Uruz): Intent to run
- **ᚷ** (Gebo): Cost/heat calculation
- **ᚺ** (Hagalaz): Clause/fate determination
- **ᛞ** (Dagaz): Deferral decisions
- **ᚨ** (Ansuz): Collapse preparation
- **ᛟ** (Othala): Full draw cooling
- **ᛇ** (Eihwaz): Trusted emergency
- **ᚠ** (Fehu): Efficient agent
- **ᛝ** (Ingwaz): Silence oath

## File Structure

```
Skadi/
├── assets/
│   └── images/              # Logo and visual assets
│       ├── skadi_logo.png      # Full resolution (1024x1024)
│       ├── skadi_logo_512.png  # Medium resolution
│       ├── skadi_logo_256.png  # README resolution
│       └── skadi_logo_64.png   # Icon resolution
├── frost_tomes/             # Entropy event archives
├── logs/                    # System logs
├── config.json             # Configuration file
├── skadi_daemon.py         # Main daemon process
├── skadictl.py            # Command-line interface
└── skadi_ceto.json        # Ceto integration config
```
