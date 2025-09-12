# Gas Pipeline Digital Twin Simulator

## Overview

This is a high-fidelity, cyber-resilient gas pipeline digital twin simulator designed for industrial training, testing, and cybersecurity research. The system simulates a complex gas pipeline network based on GasLib-134 standards, featuring realistic physics modeling, industrial control systems (SCADA/PLC), and comprehensive monitoring capabilities. The simulator provides a safe environment for testing operational scenarios, cybersecurity incidents, and control system responses without risking real infrastructure.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Framework
The system is built around a multi-layered, containerized architecture using Docker orchestration. The main application follows a modular design pattern where each major subsystem (physics, PLCs, SCADA, sensors) operates independently but communicates through well-defined interfaces. This design ensures modularity, scalability, and realistic behavior matching real industrial systems.

### Physics Engine Architecture
The physics simulation layer uses GasLib-134 network data as its foundation, providing a standardized gas pipeline network with 134 nodes. The engine simulates gas flow dynamics, pressure variations, temperature changes, and transient behaviors. It supports both steady-state and dynamic simulations with configurable time steps for real-time operation.

### Industrial Control System Design
The control architecture implements eight specialized PLCs, each handling specific operational aspects:
- Pressure Control PLC with PID regulation
- Flow Regulation PLC for throughput management
- Compressor Management PLC for compression stations
- Valve Control PLC for actuator management
- Safety Monitoring PLC for system-wide safety
- Leak Detection PLC for gas leak response
- Temperature Control PLC for thermal management
- Emergency Shutdown PLC for critical safety systems

Each PLC follows industrial ladder logic patterns and maintains realistic scan cycles, memory structures, and alarm systems.

### SCADA System Architecture
The SCADA layer provides supervisory control and data acquisition capabilities, featuring a web-based Human-Machine Interface (HMI) built with Flask and SocketIO for real-time updates. The system aggregates data from all PLCs and sensors, provides alarm management, and offers operational control interfaces.

### Data Management Strategy
The system uses SQLite for local data storage with structured tables for simulation data, alarms, and historical records. Real-time data flows through in-memory structures for performance, while persistent storage captures historical trends and audit logs.

### Sensor Network Design
The sensor management system creates realistic sensor readings for pressure, temperature, flow, vibration, gas composition, leak detection, valve positions, and compressor status. Sensors are dynamically assigned based on node types, with appropriate noise models and failure simulation capabilities.

### Communication Architecture
Inter-component communication uses standard industrial protocols where appropriate, with Modbus TCP/IP for PLC communications and REST APIs for web interface interactions. WebSocket connections enable real-time data streaming to the dashboard interface.

### Web Interface Design
The frontend uses modern web technologies with responsive design, featuring real-time charts, system status indicators, alarm management, and control panels. The interface provides both operator-level controls and engineering-level diagnostics.

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework for HTTP endpoints and template rendering
- **Flask-SocketIO**: Real-time bidirectional event-based communication for live updates
- **SQLite3**: Embedded database for data persistence and historical storage

### Scientific Computing Libraries
- **NumPy**: Numerical computations for physics calculations and data processing
- **SciPy**: Advanced scientific computing for physics modeling and optimization
- **Pandas**: Data manipulation and analysis for time series processing

### Physics Simulation Dependencies
- **pandapipes**: Gas pipeline simulation library for steady-state and transient analysis
- **MATLAB Engine** (optional): Advanced physics modeling capabilities for high-fidelity simulations
- **NetworkX**: Graph-based network analysis for pipeline topology management

### Industrial Communication Protocols
- **pyModbus**: Modbus TCP/IP client and server implementation for PLC communications
- **pyModbusTCP**: Alternative Modbus implementation for industrial protocol compatibility

### Data Visualization and Analysis
- **Matplotlib**: Static plotting and chart generation for reports and analysis
- **Plotly**: Interactive web-based charts and real-time data visualization
- **Chart.js**: Client-side charting library for dashboard visualizations

### Data Processing and Storage
- **lxml**: XML parsing for GasLib-134 network data processing
- **xmlschema**: XML schema validation for network data integrity

### Container Orchestration
- **Docker**: Containerization platform for service isolation and deployment
- **Docker Compose**: Multi-container orchestration for system deployment

### Optional Integrations
- **PostgreSQL/TimescaleDB**: Time-series database for production deployments
- **psycopg2**: PostgreSQL database adapter for scalable data storage
- **MQTT**: IoT messaging protocol for sensor data collection in distributed deployments