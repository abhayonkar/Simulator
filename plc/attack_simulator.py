"""
Water Treatment Plant Simulator: Cyber Attack Simulation

This module injects malicious data into the Modbus datastore
based on the scenarios defined in the configuration file.
"""
import datetime

class AttackSimulator:
    """
    Executes cyber attack scenarios by directly manipulating the Modbus datastore.
    """
    def __init__(self, context, register_map, scenarios):
        self.context = context
        self.r_map = register_map
        self.scenarios = self._parse_scenarios(scenarios)
        self.active_attack = "None"

    def _parse_scenarios(self, scenarios):
        """Converts time strings from config into timedelta objects for comparison."""
        if not scenarios:
            return []
        for s in scenarios:
            try:
                # Convert HH:MM:SS string to a timedelta object
                h, m, sec = map(int, s['start_time'].split(':'))
                s['start_delta'] = datetime.timedelta(hours=h, minutes=m, seconds=sec)
                h, m, sec = map(int, s['end_time'].split(':'))
                s['end_delta'] = datetime.timedelta(hours=h, minutes=m, seconds=sec)
            except (ValueError, KeyError) as e:
                print(f"[ERROR] Invalid time format in attack scenario '{s.get('name', 'Unnamed')}': {e}")
                # Mark scenario as invalid
                s['start_delta'] = None
        return [s for s in scenarios if s.get('start_delta') is not None]

    def _get_register_address(self, name):
        """Gets the Modbus address for a given register name."""
        return self.r_map[name]['address'] - 1

    def update(self, current_sim_time_delta):
        """
        Checks if any attacks should be active at the current simulation time
        and executes them.
        """
        self.active_attack = "None"

        for scenario in self.scenarios:
            if scenario['start_delta'] <= current_sim_time_delta <= scenario['end_delta']:
                self.active_attack = scenario['name']
                self._execute_attack(scenario)
                # For this model, we assume only one attack can be active at a time.
                # The first one found in the list takes precedence.
                break

    def _execute_attack(self, scenario):
        """Performs the malicious action on the Modbus datastore."""
        attack_type = scenario['attack_type']
        target_reg_name = scenario['target_register']
        address = self._get_register_address(target_reg_name)
        params = scenario['parameters']

        if attack_type == "set_sensor_value" or attack_type == "set_actuator_value":
            value_to_set = int(params['value'])
            self.context.setValues(3, address, [value_to_set])

        elif attack_type == "offset_sensor":
            original_value = self.context.getValues(3, address, count=1)[0]
            offset = int(params['offset'])
            new_value = max(0, original_value + offset) # Ensure value doesn't go below zero
            self.context.setValues(3, address, [new_value])

