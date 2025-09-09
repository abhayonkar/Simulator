"""
Water Treatment Plant Simulator: Main Entry Point

This is the main script to launch the simulator.
It handles configuration loading, dependency version checking,
and starting the Modbus server and simulation loop.
"""
import logging
import yaml
import argparse
import os
import asyncio

# Check for pymodbus version before doing anything else
try:
    import pymodbus
    from packaging import version
    MIN_PYMODBUS_VERSION = "3.2.0"

    if version.parse(pymodbus.__version__) < version.parse(MIN_PYMODBUS_VERSION):
        print(f"\n--- ERROR: Incompatible pymodbus version! ---")
        print(f"Your installed version is {pymodbus.__version__}.")
        print(f"This simulator requires version {MIN_PYMODBUS_VERSION} or newer.")
        print(f"Please upgrade it by running: pip install --upgrade pymodbus\n")
        exit(1)

except ImportError:
    print("\n--- ERROR: pymodbus is not installed! ---")
    print("Please install the required libraries by running:")
    print("pip install pymodbus>=3.2 pyyaml packaging\n")
    exit(1)

# Now, import the simulator class
from plc.modbus_server import WaterPlantSimulator

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger()

def main():
    """Main function to run the simulator."""
    print("--- Launching Water Treatment Plant Simulator ---")
    parser = argparse.ArgumentParser(description="Water Treatment Plant SCADA Simulator")
    parser.add_argument(
        "--config",
        default="configs/water_plant_config.yaml",
        help="Path to the master YAML configuration file."
    )
    args = parser.parse_args()
    print(f"Using configuration: {args.config}\n")

    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        log.error(f"FATAL: Configuration file not found at '{args.config}'")
        log.error("Please ensure the config file exists and you are running from the project root.")
        return

    simulator = WaterPlantSimulator(config)
    try:
        asyncio.run(simulator.run_async())
    except KeyboardInterrupt:
        log.info("Simulator interrupted by user.")
    finally:
        # Ensure data is saved even if the program is interrupted
        output_path = simulator.config['simulation']['output_csv_path']
        if simulator.simulation_data and not os.path.exists(output_path):
            log.info("Saving data on exit...")
            simulator.save_data_to_csv()

if __name__ == "__main__":
    main()

