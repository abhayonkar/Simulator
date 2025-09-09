"""
Water Treatment Plant Simulator: Main Modbus Server Class

This script defines the WaterPlantSimulator class which initializes and runs
the Modbus TCP server, orchestrates the simulation loops (PLC logic, attacks),
and handles the detailed data logging.
This version has been upgraded to use the advanced ModbusSimulatorContext for
more realistic, action-based register simulation.
"""
import logging
import yaml
import datetime
import time
import csv
import os
import asyncio

from pymodbus.server import ModbusTcpServer
from pymodbus.datastore import ModbusSimulatorContext

from plc.plc_logic import PLCLogic
from plc.attack_simulator import AttackSimulator

log = logging.getLogger()

class WaterPlantSimulator:
    def __init__(self, config):
        self.config = config
        self.register_map = config['register_map']
        self.is_running = True
        self.server = None
        self.simulation_data = []

        # The PLCLogic class will now hold the internal state of the physical process
        self.plc = PLCLogic(None, self.register_map, config['process_parameters']) # Context not needed here anymore
        self.attacker = AttackSimulator(None, self.register_map, config.get('attack_scenarios', []))

        # --- Build the Simulator Context ---
        # Create the action dictionary for our simulator context
        simulator_actions = {}
        for name, details in self.register_map.items():
            address = details['address'] - 1 # 0-based index
            # Define a read action for every register that fetches the live value from our PLC logic
            simulator_actions[address] = {
                "read_action": self._read_register_action,
                "write_action": self._write_register_action,
            }
        
        # Initialize the advanced simulator context with our actions
        # FIXED: Provide the config parameter as the first required positional argument
        self.context = ModbusSimulatorContext(config=config, custom_actions=simulator_actions)
        
        # Pass the live context to the plc and attacker objects now that it's created
        self.plc.context = self.context
        self.attacker.context = self.context


    def _read_register_action(self, address, _):
        """Callback triggered when any register is read by a Modbus client."""
        # Find the register name from its address
        for name, details in self.register_map.items():
            if details['address'] - 1 == address:
                # Return the current value from the plc_logic's internal state
                return self.plc.state.get(name, 0)
        return 0 # Return 0 if address is unknown

    def _write_register_action(self, address, value):
        """Callback triggered when any register is written to by a Modbus client."""
        # Find the register name from its address
        for name, details in self.register_map.items():
            if details['address'] - 1 == address and details.get('type') == 'actuator':
                # Update the state in the plc_logic for actuators
                self.plc.state[name] = value[0] # value is a list
                log.info(f"MODBUS WRITE: Register '{name}' (Addr {address+1}) set to {value[0]}")
                break

    def _log_state(self, log_entry, state_suffix):
        """Helper function to log the current value of all registers with a suffix."""
        for name in self.register_map:
            # Get the value directly from the PLC's internal state for logging
            value = self.plc.state.get(name, 0)
            log_entry[f"{name}{state_suffix}"] = value

    async def _simulation_loop_async(self, start_time):
        """The main simulation loop, running as an asyncio task."""
        total_sim_duration_delta = datetime.timedelta(hours=self.config['simulation']['duration_hours'])
        time_step_seconds = self.config['simulation']['time_step_seconds']

        while self.is_running:
            current_sim_time_delta = datetime.datetime.now() - start_time

            if current_sim_time_delta > total_sim_duration_delta:
                self.is_running = False
                break

            # --- Data Logging with Pre/Post States ---
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "sim_time": str(current_sim_time_delta)
            }
            
            # The order is now crucial:
            # 1. Log the state before this time step's updates
            self._log_state(log_entry, "_before_update")
            
            # 2. Run the physical process simulation and control logic for one time step
            self.plc.update(current_sim_time_delta)
            self._log_state(log_entry, "_after_logic")
            
            # 3. Apply any active attacks
            self.attacker.update(current_sim_time_delta)
            self._log_state(log_entry, "_after_attack")

            # 4. Log the attack status and save the record
            log_entry["active_attack"] = self.attacker.active_attack
            self.simulation_data.append(log_entry)

            await asyncio.sleep(time_step_seconds)

        log.info("Simulation finished. Saving data and shutting down...")
        self.save_data_to_csv()
        if self.server:
            self.server.shutdown()

    async def run_async(self):
        """Starts the simulation loops and the Modbus server using asyncio."""
        server_config = self.config['plc']
        log.info(f"Starting Modbus TCP server on {server_config['ip_address']}:{server_config['port']}...")

        # Create the server instance
        self.server = ModbusTcpServer(
            self.context,
            address=(server_config['ip_address'], server_config['port'])
        )

        simulation_start_time = datetime.datetime.now()

        # Run the simulation loop and the server concurrently
        sim_task = asyncio.create_task(self._simulation_loop_async(simulation_start_time))
        server_task = asyncio.create_task(self.server.serve_forever())

        # Wait for the simulation to complete
        await sim_task
        # Once simulation is done, it will have called server.shutdown(), so the server_task will also complete.
        await server_task

    def save_data_to_csv(self):
        """Writes the collected simulation data to a CSV file."""
        csv_path = self.config['simulation']['output_csv_path']
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        if not self.simulation_data:
            log.warning("No data to save.")
            return

        header = self.simulation_data[0].keys()
        with open(csv_path, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=header)
            dict_writer.writeheader()
            dict_writer.writerows(self.simulation_data)

        log.info(f"Data successfully saved to {csv_path}")