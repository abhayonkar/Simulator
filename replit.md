# Gas Pipeline Digital Twin Simulator - Django Implementation

## Overview

This is a realistic gas pipeline digital twin simulator built entirely with Django and Python. The system simulates a gas pipeline network based on **GasLib-40** standards (40 nodes, 45 pipes), featuring 8 embedded PLC controllers, simplified sensor monitoring, and comprehensive logging capabilities. The simulator provides a safe environment for testing operational scenarios and understanding industrial control systems.

## Recent Changes

**Major Refactoring (September 2025):**
- ✅ **Unified Architecture:** Combined Flask and Django variants into single Django application
- ✅ **GasLib-40 Integration:** Switched from GasLib-134 to GasLib-40 for appropriate complexity
- ✅ **Simplified Dependencies:** Removed Flask, SocketIO, cybersecurity features, OpenPLC, MATLAB
- ✅ **8 Embedded PLCs:** Implemented Python-native PLC controllers within Django models
- ✅ **Essential Sensors Only:** Streamlined to pressure, temperature, and flow rate sensors
- ✅ **Comprehensive Logging:** Added detailed simulation data capture and time-series storage
- ✅ **Django Workflow:** Configured for Replit environment with proper host settings

## User Preferences

**Communication Style:** Simple, everyday language for technical explanations
**Development Approach:** Django-centric, minimal external dependencies
**Architecture Philosophy:** Maintainable over complex, educational over production-grade

## System Architecture

### Core Framework
The system uses a **Django-only architecture** eliminating complex dependencies:

- **Web Framework:** Django with built-in template system and ORM
- **Database:** SQLite for development (easily upgradeable to PostgreSQL)
- **Simulation Engine:** Pure Python implementation in Django services
- **Network Data:** GasLib-40 XML parsing and Django model creation
- **PLCs:** 8 Python classes embedded within the Django application
- **API Layer:** Django REST views for real-time monitoring and control

### Key Components

#### 1. Django Models (`simulator/models.py`)
- **GasNetwork:** Loaded GasLib-40 networks with metadata
- **Node/Pipe:** Pipeline topology with real-time states
- **Sensor:** Pressure, temperature, and flow monitoring points
- **PLC:** 8 embedded controllers with specialized functions
- **SimulationRun:** Execution records with parameters and status
- **SimulationData:** Time-series data points for analysis

#### 2. Simulation Services (`simulator/services/`)
- **GasLibParser:** XML parsing for GasLib-40 network files
- **SimulationEngine:** Physics calculations and PLC execution
- **Threading Support:** Real-time simulation execution
- **Logging System:** Comprehensive data capture

#### 3. Web Interface (`simulator/templates/`)
- **Dashboard:** Real-time monitoring and control interface
- **Network Visualization:** GasLib-40 topology display
- **Simulation Controls:** Start/stop with configurable parameters
- **Data Display:** Sensor readings, PLC status, alarm management

### 8 Embedded PLC Controllers

| PLC Type | Function | Implementation |
|----------|----------|----------------|
| **Pressure Control** | PID pressure regulation | Python class with control logic |
| **Flow Regulation** | Flow rate management | Embedded in Django models |
| **Compressor Management** | Compressor sequencing | State machine implementation |
| **Valve Control** | Actuator positioning | Position control algorithms |
| **Safety Monitoring** | System safety oversight | Safety logic and interlocks |
| **Leak Detection** | Gas leak response | Detection algorithms |
| **Temperature Control** | Thermal management | Temperature regulation |
| **Emergency Shutdown** | Critical safety systems | Emergency response logic |

### Sensor Network (Simplified)
- **Pressure Sensors:** Bar readings at pipeline nodes
- **Temperature Sensors:** Celsius readings for gas temperature  
- **Flow Meters:** Cubic meters per hour flow measurements

*Removed:* Vibration sensors, gas composition analyzers, specialized leak detectors

## File Structure

```
.
├── gas_sim/                    # Django project settings
│   ├── settings.py            # Django configuration (ALLOWED_HOSTS = ['*'])
│   ├── urls.py                # URL routing with API endpoints
│   └── wsgi.py                # WSGI application
├── simulator/                  # Main Django app
│   ├── models.py              # Database models for pipeline components
│   ├── views.py               # API endpoints and web interface
│   ├── services/              # Simulation engine and parsers
│   │   ├── gaslib_parser.py   # GasLib-40 XML parsing
│   │   └── simulation_engine.py # Physics and PLC simulation
│   ├── templates/             # Web interface templates
│   │   └── simulator/
│   │       └── index.html     # Main dashboard
│   └── migrations/            # Database migrations
├── GasLib-40-v1-20211130/     # Network data
│   └── GasLib-40-v1-20211130.net # XML network definition
├── requirements.txt           # Python dependencies
├── manage.py                  # Django management script
└── db.sqlite3                 # SQLite database (created on first run)
```

## External Dependencies

### Core Framework Dependencies
- **Django 5.2+:** Web framework and ORM for all functionality
- **Python 3.11+:** Runtime environment with standard libraries

### Scientific Computing Libraries
- **NumPy:** Numerical computations for physics calculations
- **lxml:** XML parsing for GasLib-40 network data
- **xmlschema:** XML schema validation for network files

### Removed Dependencies
- ❌ **Flask/Flask-SocketIO:** Replaced with Django
- ❌ **MATLAB/Simulink:** Pure Python implementation
- ❌ **OpenPLC:** Python-native PLC logic
- ❌ **pandapipes:** Simplified physics in Python
- ❌ **psycopg2-binary:** Using SQLite for simplicity
- ❌ **pyModbus/pyModbusTCP:** No industrial protocols needed
- ❌ **eventlet/python-socketio:** Standard HTTP only

## Replit Configuration

### Environment Setup
- **Python Version:** 3.11 (installed via module system)
- **Port Configuration:** Django server runs on 0.0.0.0:5000
- **Host Settings:** `ALLOWED_HOSTS = ['*']` for Replit proxy support
- **Database:** SQLite (no additional setup required)

### Workflow Configuration
- **Name:** Django Server
- **Command:** `python manage.py runserver 0.0.0.0:5000`
- **Port:** 5000 (configured for Replit webview)
- **Auto-restart:** Enabled for development

### First-Time Setup
1. **Dependencies:** Automatically installed via requirements.txt
2. **Database:** Migrations applied automatically
3. **Network Data:** GasLib-40 files included in repository
4. **Web Interface:** Accessible immediately at preview URL

## API Endpoints

### Core Functionality
- `GET /` - Main dashboard interface
- `GET /api/` - API information and available endpoints
- `GET /api/status/` - System status and statistics

### Network Management
- `POST /api/network/load/` - Load GasLib-40 network from XML
- `GET /api/network/<id>/` - Get network topology and current state

### Simulation Control
- `POST /api/simulation/start/` - Start simulation with parameters
- `POST /api/simulation/stop/` - Stop current simulation
- `GET /api/simulation/<id>/data/` - Retrieve simulation time-series data

### Monitoring
- `GET /api/sensors/readings/` - Current sensor values
- `GET /api/plcs/status/` - PLC execution status
- `GET /api/alarms/` - Active system alarms

## Development Workflow

### Local Development
1. **Load Network:** Use web interface to load GasLib-40 data
2. **Start Simulation:** Configure duration (1-3600 seconds) and timestep (0.1-60 seconds)
3. **Monitor Real-time:** View live sensor data and PLC operations
4. **Analyze Results:** Export simulation data for analysis

### Data Management
- **Django Admin:** Access via `/admin/` for data management
- **Database Queries:** Use Django ORM for custom data analysis
- **Export Options:** API endpoints provide JSON data for external tools

## Troubleshooting

### Common Issues
- **Network Loading Errors:** Ensure GasLib-40 XML file is accessible
- **Simulation Performance:** Reduce timestep or duration for large networks
- **Database Issues:** Run `python manage.py migrate` to update schema
- **Port Conflicts:** Django server configured for port 5000 only

### Debugging
- **Django Debug Mode:** Enabled by default in development
- **Logging:** Check console output for simulation engine messages
- **API Testing:** Use `/api/` endpoint to verify system status

## Educational Use

### Learning Objectives
- **Industrial Control Systems:** Understanding PLC operations and logic
- **Pipeline Operations:** Gas flow dynamics and pressure control
- **System Integration:** Django web applications with real-time data
- **Data Management:** Time-series data storage and retrieval

### Simulation Scenarios
- **Steady-State Operations:** Normal pipeline operation monitoring
- **Transient Events:** Valve operations and flow changes
- **Control System Response:** PLC logic execution and alarm handling
- **Data Analysis:** Historical trend analysis and pattern recognition

## Future Enhancements

### Near-term Improvements
- **Enhanced Visualization:** Interactive network diagrams
- **Data Export:** CSV/Excel export for simulation results
- **Performance Optimization:** Caching for large network operations
- **User Management:** Django authentication for multi-user access

### Potential Extensions
- **Additional Networks:** Support for other GasLib datasets
- **Advanced Physics:** More sophisticated flow calculations
- **Machine Learning:** Predictive maintenance algorithms
- **Mobile Interface:** Responsive design for tablet/mobile access

### Architecture Preservation
All enhancements should maintain:
- **Django-only stack:** No external simulation dependencies
- **Python implementation:** Pure Python, no compiled libraries
- **Simple deployment:** Single application architecture
- **Educational focus:** Clear, understandable implementation

---

**This Django implementation provides a practical, maintainable gas pipeline simulator ideal for education and research in industrial control systems.**