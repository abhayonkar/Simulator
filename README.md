# Gas Pipeline Digital Twin Simulator - Django + GasLib-40

## Overview

This is a realistic gas pipeline digital twin simulator built with Django, designed for industrial training and simulation. The system simulates a gas pipeline network based on **GasLib-40** standards (40 nodes, 45 pipes), featuring realistic physics modeling, industrial control systems with 8 embedded PLCs, and comprehensive monitoring capabilities. The simulator provides a safe environment for testing operational scenarios and control system responses.

## Key Features

### 🏭 **8 Embedded PLCs with Specialized Functions**
- **Pressure Control PLC** - PID-based pressure regulation and monitoring
- **Flow Regulation PLC** - Flow rate management and control
- **Compressor Management PLC** - Compressor sequencing and control
- **Valve Control PLC** - Actuator positioning and valve management
- **Safety Monitoring PLC** - System-wide safety oversight
- **Leak Detection PLC** - Gas leak detection and response
- **Temperature Control PLC** - Thermal management and control
- **Emergency Shutdown PLC** - Critical safety system management

### 📊 **Simplified Sensor Network**
- **Pressure Sensors** - Real-time pipeline pressure monitoring
- **Temperature Sensors** - Gas temperature tracking
- **Flow Meters** - Mass flow rate measurements

### 🌐 **Django Web Interface**
- Interactive dashboard with live data visualization
- System status monitoring and alarm management
- PLC status overview with detailed diagnostics
- Network topology visualization from GasLib-40 data
- Simulation management and control panels
- Comprehensive logging and data retrieval

## System Architecture

### Core Framework
The system is built around a **Django-only architecture** where each major subsystem (physics simulation, PLCs, sensors) operates through Django models and services. This design ensures simplicity, maintainability, and realistic behavior matching real industrial systems.

### GasLib-40 Network Foundation
- **40-Node Network** - Standardized gas pipeline network with 40 nodes and 45 pipes
- **Real-Time Simulation** - Physics calculations with configurable timesteps
- **Transient Dynamics** - Gas flow, pressure variations, and temperature changes
- **Compressor Modeling** - Realistic compression station behavior

### Industrial Control System Design
The control architecture implements eight specialized PLCs distributed across network nodes:
- Each PLC follows industrial control patterns
- Configurable scan cycles and memory structures
- Comprehensive alarm systems with severity levels
- Safety interlocks and emergency shutdown procedures

### Simulation Engine
- **Python-Only Implementation** - No external dependencies like MATLAB or OpenPLC
- **Django Integration** - Built using Django models and services
- **Comprehensive Logging** - Complete capture of sensor readings, valve operations, and PLC activities
- **Configurable Duration** - Run simulations for specified time periods
- **Real-Time Monitoring** - Live updates during simulation execution

## Quick Start

### Prerequisites
- Python 3.11+
- Django and dependencies (see requirements.txt)

### Installation & Running

1. **Clone and Navigate**
   ```bash
   git clone <repository-url>
   cd gas-pipeline-simulator
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Database**
   ```bash
   python manage.py migrate
   ```

4. **Load GasLib-40 Network Data**
   ```bash
   python manage.py shell
   # In Django shell:
   from simulator.services.gaslib_parser import GasLibParser
   parser = GasLibParser('GasLib-40-v1-20211130/GasLib-40-v1-20211130.net')
   network = parser.parse_and_create_network()
   ```

5. **Run the Simulator**
   ```bash
   python manage.py runserver 0.0.0.0:5000
   ```

6. **Access the Dashboard**
   - Open your browser to `http://localhost:5000`
   - Load GasLib-40 network via the interface
   - Start simulations with custom duration and timestep
   - Monitor real-time data and PLC operations

### System Status
- **🟢 Active:** 8 PLCs embedded in GasLib-40 structure
- **🟢 Active:** 3 sensor types (pressure, temperature, flow)
- **🟢 Active:** Physics simulation with configurable timesteps
- **🟢 Active:** Django web interface with real-time monitoring
- **🟢 Active:** Comprehensive logging system

## Network Topology

The simulator uses the GasLib-40 network structure with 40 nodes and 45 arcs:

**Node Types:**
- **Sources** - Gas supply points with pressure control
- **Junctions** - Pipeline connection points with monitoring
- **Compressors** - Compression stations with management PLCs
- **Sinks** - Gas consumption points with flow regulation

**PLC Distribution:** The 8 PLCs are strategically embedded throughout the GasLib-40 network structure based on node types and operational requirements.

## Django Application Structure

```
simulator/
├── models.py                # Django models for network, PLCs, sensors
├── views.py                # API endpoints and web interface
├── services/               # Simulation engine and parsers
│   ├── gaslib_parser.py    # GasLib-40 XML parser
│   └── simulation_engine.py # Physics and PLC simulation
├── templates/              # Web interface templates
│   └── simulator/
│       └── index.html      # Main dashboard
└── migrations/             # Database migrations
```

## API Endpoints

### Core Simulation
- `GET /` - Main dashboard interface
- `GET /api/` - API information and endpoints
- `GET /api/status/` - System status and statistics
- `POST /api/start/` - Start simulation (legacy)
- `POST /api/simulation/start/` - Start simulation with parameters

### Network Management
- `POST /api/network/load/` - Load GasLib-40 network data
- `GET /api/network/<id>/` - Get network topology and state

### Monitoring
- `GET /api/sensors/readings/` - Current sensor readings
- `GET /api/plcs/status/` - PLC status overview
- `GET /api/alarms/` - Active alarms list
- `POST /api/alarms/<id>/acknowledge/` - Acknowledge alarm

### Data Retrieval
- `GET /api/simulation/<id>/data/` - Simulation data points
- `POST /api/simulation/stop/` - Stop current simulation

## Simulation Features

### Configurable Parameters
- **Duration:** Simulation runtime (1-3600 seconds)
- **Time Step:** Calculation interval (0.1-60 seconds)
- **Network Selection:** Choose loaded GasLib-40 networks

### Comprehensive Logging
The simulator captures detailed logs for:
- **Sensor Data:** All pressure, temperature, and flow measurements
- **PLC Operations:** Input/output states, logic execution, memory usage
- **Valve Operations:** Position changes, control commands
- **Alarm Events:** PLC alarms with timestamps and severity
- **System Events:** Start/stop, network changes, errors

### Real-Time Monitoring
- Live sensor value updates
- PLC execution status and scan times
- Active alarm counts and acknowledgments
- System performance metrics
- Network topology visualization

## Data Management

### Django Models
- **GasNetwork:** Network topology from GasLib-40
- **Node/Pipe:** Pipeline components with current states
- **Sensor:** Pressure, temperature, flow monitoring
- **PLC:** 8 embedded controllers with logic and memory
- **SimulationRun:** Simulation execution records
- **SimulationData:** Time-series data points

### Database Storage
- **SQLite** for development and testing
- **Structured logging** with timestamps and relationships
- **Historical data** retention for analysis
- **Real-time data** access through Django ORM

## Dependencies

### Core Framework
- **Django** - Web framework and ORM
- **Python 3.11+** - Runtime environment

### Scientific Computing
- **NumPy** - Numerical computations for physics calculations
- **lxml** - XML parsing for GasLib-40 data
- **xmlschema** - XML schema validation

### Additional Libraries
- Standard Python libraries for simulation engine
- Django built-in features for web interface and database

## Testing & Validation

### Simulation Testing
- GasLib-40 network loading and parsing
- PLC logic execution across all 8 controllers
- Sensor data generation and logging
- Alarm generation and management
- Simulation duration and timestep validation

### Integration Testing
- Django API endpoint functionality
- Database model relationships
- Real-time data flow through the system
- Web interface responsiveness

## Contributing

This simulator is designed for educational and research purposes. The Django architecture allows for easy extension and customization of:

- Additional PLC types and control strategies
- New sensor configurations and failure modes
- Enhanced physics models within the simulation engine
- Custom visualization and analysis tools
- Extended network topologies beyond GasLib-40

## License

This project is developed for educational and research purposes in industrial control systems simulation.

## Support & Documentation

For technical support or questions about the simulator:
- Review the Django code documentation
- Check the simulation logs for diagnostic information
- Monitor the real-time dashboard for system status
- Use the web interface API for programmatic access

---

**Built with Django and Python for realistic, maintainable gas pipeline simulation using GasLib-40 network standards.**