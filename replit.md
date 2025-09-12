# Gas Pipeline Digital Twin Simulator - Django Implementation

## Overview

This project is a realistic gas pipeline digital twin simulator built entirely with Django and Python. It simulates a gas pipeline network based on **GasLib-40** standards (40 nodes, 45 pipes), featuring 8 embedded PLC controllers, simplified sensor monitoring, and comprehensive logging capabilities. The simulator provides a safe environment for testing operational scenarios and understanding industrial control systems. It is designed for educational purposes, focusing on practical, maintainable, and understandable implementations of industrial control systems using a pure Python and Django stack.

## User Preferences

**Communication Style:** Simple, everyday language for technical explanations
**Development Approach:** Django-centric, minimal external dependencies
**Architecture Philosophy:** Maintainable over complex, educational over production-grade

## System Architecture

### Core Framework
The system uses a **Django-only architecture** to eliminate complex dependencies:
- **Web Framework:** Django with its built-in template system and ORM.
- **Database:** PostgreSQL for relational data + InfluxDB for time-series data.
- **Simulation Engine:** Pure Python implementation within Django services.
- **Network Data:** GasLib-40 XML parsing directly into Django models.
- **PLCs:** 8 Python classes embedded directly within the Django application.
- **API Layer:** Django REST views provide real-time monitoring and control.

### Key Components

#### 1. Django Models (`simulator/models.py`)
These models define the structure for the pipeline components and simulation data:
- **GasNetwork, Node, Pipe:** For defining the pipeline topology and real-time states.
- **Sensor:** For managing pressure, temperature, and flow monitoring points.
- **PLC:** Represents the 8 embedded controllers with specialized functions.
- **SimulationRun, SimulationData:** For recording execution parameters and time-series data.

#### 2. Simulation Services (`simulator/services/`)
- **GasLibParser:** Handles XML parsing for GasLib-40 network files.
- **SimulationEngine:** Executes physics calculations and PLC logic, designed for real-time operation using threading.
- **Logging System:** Captures comprehensive simulation data.

#### 3. Web Interface (`simulator/templates/`)
- **Dashboard:** Provides a real-time monitoring and control interface.
- **Network Visualization:** Displays the GasLib-40 topology.
- **Simulation Controls:** Allows starting/stopping simulations with configurable parameters.
- **Data Display:** Shows sensor readings, PLC status, and alarm management.

### 8 Embedded PLC Controllers
The system includes 8 distinct Python-native PLC controllers integrated into the Django application, each serving a specific function:
- **Pressure Control:** PID-based pressure regulation.
- **Flow Regulation:** Management of flow rates.
- **Compressor Management:** Sequencing and control of compressors.
- **Valve Control:** Actuator positioning using control algorithms.
- **Safety Monitoring:** System safety oversight with logic and interlocks.
- **Leak Detection:** Algorithms for detecting gas leaks.
- **Temperature Control:** Thermal management and regulation.
- **Emergency Shutdown:** Critical safety systems for emergency response.

### Sensor Network (Simplified)
The simulator includes essential sensors:
- **Pressure Sensors:** Bar readings at pipeline nodes.
- **Temperature Sensors:** Celsius readings for gas temperature.
- **Flow Meters:** Cubic meters per hour flow measurements.

## External Dependencies

### Core Framework Dependencies
- **Django 5.2+:** The foundational web framework and ORM.
- **Python 3.11+:** The primary runtime environment.

### Scientific Computing Libraries
- **NumPy:** Used for numerical computations required for physics calculations.
- **lxml:** Utilized for efficient XML parsing of GasLib-40 network data.
- **xmlschema:** For XML schema validation of network files.

### Databases
- **PostgreSQL:** Recommended for relational data storage, especially in production environments.
- **InfluxDB:** Used for time-series data storage of simulation results.