"""
Water Treatment Plant Simulator: PLC Logic and Process Simulation

This module simulates the physical water treatment process and the
control logic that a real PLC would execute.
"""
import random

class PLCLogic:
    """
    Simulates the water treatment process and control logic.
    It reads from and writes to the Modbus datastore to interact with the "plant".
    """
    def __init__(self, context, register_map, params):
        self.context = context
        self.r_map = register_map
        self.params = params
        self.stuck_sensors = {} # To track faulty sensors

    def _read_register(self, name):
        """Helper to read a single value from a holding register."""
        address = self.r_map[name]['address'] - 1 # Adjust for 0-based index
        value = self.context.getValues(3, address, count=1)[0]
        return value

    def _write_register(self, name, value):
        """Helper to write a single value to a holding register."""
        address = self.r_map[name]['address'] - 1 # Adjust for 0-based index
        self.context.setValues(3, address, [int(value)])

    def update(self, current_time):
        """Executes one step of the simulation logic."""

        # --- 1. SIMULATE EXTERNAL CONDITIONS (RAW WATER) ---
        # Base turbidity with some random noise
        base_turbidity = self.params['raw_water_turbidity_normal'] + random.uniform(-5, 5)
        # Occasional random spikes (e.g., from rainfall)
        if random.random() < 0.01:
            base_turbidity += random.uniform(50, 150)
        self._write_register("raw_water_turbidity", base_turbidity)

        # --- 2. FAULTY SENSOR SIMULATION ---
        # Check if any sensor should get "stuck"
        for name in self.r_map:
            if 'turbidity' in name and random.random() < self.params['faulty_reading_chance']:
                if name not in self.stuck_sensors:
                    current_value = self._read_register(name)
                    stuck_duration = random.randint(10, 50) # Stuck for 10-50 steps
                    self.stuck_sensors[name] = {"value": current_value, "steps_left": stuck_duration}

        # Update any active stuck sensors
        for name in list(self.stuck_sensors.keys()):
            self.stuck_sensors[name]["steps_left"] -= 1
            if self.stuck_sensors[name]["steps_left"] <= 0:
                del self.stuck_sensors[name] # Sensor is no longer stuck
            else:
                # Force the sensor to report its stuck value
                self._write_register(name, self.stuck_sensors[name]["value"])


        # --- 3. READ SENSOR VALUES FROM MODBUS ---
        raw_turbidity = self._read_register("raw_water_turbidity")

        # --- 4. EXECUTE CONTROL LOGIC ---
        # Adjust coagulant pump speed based on incoming water turbidity
        if raw_turbidity > self.params['raw_water_turbidity_high_threshold']:
            self._write_register("coagulant_pump_speed", self.params['coagulant_pump_speed_high'])
        else:
            self._write_register("coagulant_pump_speed", self.params['coagulant_pump_speed_normal'])

        # --- 5. SIMULATE THE PHYSICAL PROCESS ---
        coag_pump_speed = self._read_register("coagulant_pump_speed")

        # Coagulation/Flocculation effectiveness depends on pump speed
        # A speed of 0 means 0 effectiveness.
        coag_effectiveness_ratio = coag_pump_speed / self.params['coagulant_pump_speed_high']
        coag_effectiveness = coag_effectiveness_ratio * random.uniform(0.85, 0.95)

        # Calculate turbidity after sedimentation
        turbidity_after_sed = raw_turbidity * (1 - coag_effectiveness)
        self._write_register("sedimentation_turbidity", turbidity_after_sed)

        # Filtration further reduces turbidity
        final_turbidity = turbidity_after_sed * random.uniform(0.05, 0.15)
        self._write_register("filter_outlet_ turbidity", final_turbidity)

