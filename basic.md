# High-Fidelity, Cyber-Resilient Gas Pipeline Digital Twin—A Step-by-Step Playbook for Building, Testing & Defending an Industrial-Grade Simulator

### Executive Summary

This report outlines a comprehensive, actionable strategy for developing a realistic and secure industrial-level gas pipeline simulator. The proposed architecture is a multi-layered, containerized digital twin that mirrors the Purdue Reference Model, ensuring both high-fidelity physical process replication and a robust environment for cybersecurity testing. [executive_summary[0]][1] The core of the simulator leverages the **GasLib-134** network, a standardized and complex pipeline topology, with its transient gas dynamics modeled in **MATLAB/Simulink** using the Simscape Gas library for industry-grade physical realism. [executive_summary[5]][2] [executive_summary[3]][3] The control layer is implemented with **OpenPLC**, an open-source platform that enables the development of IEC 61131-3 compliant logic without deep proprietary knowledge, making it highly accessible. [executive_summary[2]][4]

The entire system is orchestrated by the **ICSsim framework**, which uses **Docker** to containerize each component—the physics model, PLC, and a Flask-based Human-Machine Interface (HMI)—creating an isolated, reproducible, and realistic network environment. [executive_summary[0]][1] This containerized approach is the cornerstone of the design, providing the modularity needed for robust operational testing and the segmented network architecture required for advanced cybersecurity simulations. [recommended_architecture_overview[0]][1] A defense-in-depth security posture is integrated from the ground up, featuring network segmentation, secure communication protocols like **OPC UA**, and the deployment of Intrusion Detection Systems (IDS) such as **Suricata** and **Zeek**. This enables the simulation, detection, and analysis of realistic cyberattacks, transforming the simulator into a powerful cyber-range for training and defense validation. [cybersecurity_architecture_plan[0]][5]

## 1. Project Vision & Value Proposition — Why a digital twin beats bench-scale rigs for cost, safety and cyber-training

The vision is to create a high-fidelity digital twin of an industrial gas pipeline network that is both operationally realistic and cyber-resilient. [executive_summary[0]][1] This simulator moves beyond traditional bench-scale models by offering a scalable, cost-effective, and safe environment for a wide range of applications. It enables engineers to test control strategies, operators to train on complex scenarios, and cybersecurity teams to practice defending against sophisticated threats without risking physical assets.

By leveraging a multi-layered, containerized architecture, the simulator achieves a level of modularity and reproducibility that is difficult to attain with physical hardware. [recommended_architecture_overview[0]][1] Each component—from the underlying gas physics to the PLC control logic and the operator HMI—runs in its own isolated environment, mirroring the structure of real-world Industrial Control Systems (ICS). [executive_summary[0]][1] This approach not only facilitates independent development and testing but also provides the perfect foundation for creating a powerful cyber-range. The simulator is designed to be a living testbed where the impact of cyberattacks on physical processes can be safely observed, measured, and mitigated, providing invaluable insights for building more secure and resilient critical infrastructure.

## 2. Architecture Blueprint — Containerized Purdue-model stack delivers modularity and realism

The recommended system architecture is a multi-layered, containerized design orchestrated by the ICSsim framework to ensure modularity, realism, and security. [recommended_architecture_overview[0]][1] The architecture is segmented into distinct layers, each running in isolated Docker containers with controlled network communication, mirroring the Purdue Reference Model for ICS. [executive_summary[0]][1]

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   SCADA/ICS     │    │   IDS Security  │
│     (Flask)     │◄──►│   Simulator     │◄──►│     System      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Data Storage  │    │  Physics Engine │
│   (TimescaleDB) │    │   (Python/MATLAB)│
└─────────────────┘    └─────────────────┘
                               ▲
                               │
                               ▼
                      ┌─────────────────┐
                      │  Pipeline Model │
                      │   (GasLib-134)  │
                      └─────────────────┘
                               ▲
                               │
                               ▼
                      ┌─────────────────┐
                      │   PLC Emulation │
                      │    (OpenPLC)    │
                      └─────────────────┘


### 2.1 Physical Process Layer: GasLib-134 + Simscape Gas hits transient accuracy at <10 ms step size

The foundation of the simulator is a high-fidelity physical process model of the **GasLib-134** pipeline network, a standardized, publicly available, and complex gas network instance with **134 nodes** designed for research and benchmarking. [key_technology_recommendations.1.justification[0]][2] [key_technology_recommendations.1.justification[1]][6] This model is built in **MATLAB/Simulink** using the **Simscape Gas library**, which provides specialized blocks for pipes, compressors, and valves, and supports real gas models for accurate transient dynamic simulation. [key_technology_recommendations.0.justification[0]][7] [key_technology_recommendations.0.justification[3]][8]

The modeling approach involves programmatically building the Simulink model from the parsed GasLib-134 XML data. [physical_process_modeling.modeling_approach[1]][6] Each component is mapped to a corresponding Simscape Gas block:
* Pipes map to `Pipe (G)` blocks.
* Sources and sinks map to `Reservoir (G)` or `Controlled Mass Flow Rate Source (G)` blocks.
* The compressor station maps to a `Compressor (G)` block.
* The control valve maps to a `Variable Local Restriction (G)` block.

For the highest fidelity, the `Real Gas` model is selected in the `Gas Properties (G)` block, and the `Pipe (G)` block is configured to enable dynamic compressibility. [physical_process_modeling.modeling_approach[4]][9] Due to the mathematically "stiff" nature of the model, a variable-step implicit solver like `ode15s` or `daessc` is used, with tolerances tuned to `1e-3` for a balance of speed and accuracy. [physical_process_modeling.solver_configuration[0]][10] To enable headless operation, the Simulink model is compiled using Simulink Coder and deployed within its own Docker container. [recommended_architecture_overview[1]][11]

### 2.2 PLC Control Layer: OpenPLC lowers IEC-61131 barrier; auto-generated ST from Stateflow

The control logic is executed by an **OpenPLC** instance running in a dedicated Docker container. [recommended_architecture_overview[1]][11] OpenPLC is an open-source, IEC 61131-3 compliant software PLC, making it ideal for users without deep proprietary PLC knowledge. [key_technology_recommendations.3.justification[0]][12] It supports standard industrial languages like Ladder Diagram (LD) and Structured Text (ST). [plc_control_implementation.implementation_details[1]][13]

The control strategy manages the pipeline's actuators to ensure safe operation. This includes:
* **Compressor Management:** A dual-compressor sequencing strategy to alternate units and balance wear. [plc_control_implementation.control_strategy_overview[0]][14]
* **Pressure Regulation:** Using PID controllers to modulate control valves. [plc_control_implementation.control_strategy_overview[1]][15]
* **Safety Interlocks & ESD:** Monitoring critical parameters like pressure to execute safe shutdowns. [plc_control_implementation.control_strategy_overview[5]][16]

For beginners, it is recommended to first design and validate this logic visually in **MATLAB's Stateflow**, which can then serve as a blueprint for implementation in the OpenPLC Editor. [guidance_for_plc_beginners.logic_design_tool[0]][17] OpenPLC is configured as a Modbus TCP slave on port **502**, with its internal memory locations mapped to standard Modbus addresses (e.g., `%QX0.0` to Coils, `%IW0` to Input Registers) for communication. [plc_control_implementation.protocol_io_mapping[0]][13]

### 2.3 HMI/SCADA Layer: Flask-SocketIO + OPC UA enables real-time web dashboards with role-based control

A web-based Human-Machine Interface (HMI) and SCADA master is developed using the **Flask** Python framework. [recommended_architecture_overview[1]][11] The UI/UX philosophy is grounded in the **ISA-101.01 standard**, featuring a four-level display hierarchy for intuitive navigation and situational awareness. [hmi_scada_interface_design.ui_ux_philosophy[0]][18]

The backend architecture uses **Flask-SocketIO** to enable low-latency, bi-directional communication with web clients, allowing the server to push real-time data updates without polling. [hmi_scada_interface_design.system_architecture[1]][19] To keep the web server responsive, data acquisition from the PLC is offloaded to a non-blocking background thread. [hmi_scada_interface_design.system_architecture[1]][19]

For secure and structured data exchange, the HMI uses the **`asyncua`** Python library to communicate via **OPC UA**. [hmi_scada_interface_design.protocol_integration[0]][20] OPC UA is superior to Modbus for this link due to its robust security, hierarchical address space, and efficient subscription model, which allows the server to report data changes by exception rather than constant polling. [hmi_scada_interface_design.protocol_integration[0]][20]

### 2.4 Orchestration & Networks: ICSsim + Docker Compose enforce OT/IT segmentation and reproducibility

The entire system is managed by the **ICSsim framework**, which uses **Docker Compose** to define and launch all services. [recommended_architecture_overview[0]][1] ICSsim is explicitly designed for building virtual ICS security testbeds with support for physical process coupling, making it superior to alternatives like SCADAsim for this project. [industrial_control_system_framework.justification[0]][21] [industrial_control_system_framework.justification[2]][11]

A critical security strategy is implemented using Docker's custom networking to create segmented virtual networks:
* An **`ot_network`** for sensitive control traffic between the MATLAB model and OpenPLC.
* An **`it_network`** for the Flask HMI and its database.

This segmentation enforces security boundaries, with a gateway service controlling and monitoring traffic between the zones. [docker_deployment_strategy.network_segmentation[0]][22] This containerized approach, managed by ICSsim, ensures the testbed is isolated, reproducible, and provides a realistic network environment for both operational and security testing. [industrial_control_system_framework.justification[2]][11]

### 2.5 Technology Decision Matrix — Why each core tool beat ≥3 alternatives

The technology stack was carefully selected to balance fidelity, accessibility, and security. Each recommended tool was chosen over alternatives based on its specific strengths for this project's unique requirements.

| Component Area | Recommended Technology | Justification & Key Advantages | Alternatives Considered |
| :--- | :--- | :--- | :--- |
| **Physical Process Model** | MATLAB/Simulink with Simscape Gas Library | High-fidelity transient simulation with specialized blocks for gas components; industry standard for complex physical modeling. [key_technology_recommendations.0.justification[0]][7] | Custom Python physics engines, other commercial simulation software. [key_technology_recommendations.0.alternatives_considered[0]][23] |
| **Gas Network Data** | GasLib-134 | Standardized, complex (134-node) public benchmark for research; well-structured and parsable XML format. [key_technology_recommendations.1.justification[0]][2] [key_technology_recommendations.1.justification[1]][6] | Creating a custom network model from scratch. [key_technology_recommendations.1.alternatives_considered[0]][6] |
| **ICS/SCADA Framework** | ICSsim | Designed for virtual ICS security testbeds with physical process coupling (HIL/SIL); native Docker support ensures reproducibility. [key_technology_recommendations.2.justification[0]][1] | SCADAsim (lacks direct interface for real physical processes). [key_technology_recommendations.2.alternatives_considered[0]][24] |
| **PLC Functionality** | OpenPLC | Open-source, IEC 61131-3 compliant, and easily containerized; ideal for users without proprietary PLC knowledge. [key_technology_recommendations.3.justification[0]][12] | Commercial PLC simulators, custom Python logic (lacks realism). [key_technology_recommendations.3.alternatives_considered[0]][12] |
| **HMI/SCADA Interface** | Flask with Flask-SocketIO | Lightweight, flexible Python framework with a vast ecosystem; SocketIO enables real-time, low-latency browser updates. [key_technology_recommendations.4.justification[1]][19] | Django (more heavyweight), commercial SCADA HMI software. |
| **Secure Communication** | OPC UA (via `asyncua`) | Modern, secure-by-design protocol with built-in encryption and authentication; rich data model supports complex tag structures. [key_technology_recommendations.6.justification[0]][25] | Modbus/TCP (insecure), MQTT (requires Sparkplug for standard payload). [key_technology_recommendations.6.alternatives_considered[0]][26] |
| **Cybersecurity Monitoring** | Suricata and Zeek | Powerful combination of rule-based IDS (Suricata) and deep network analysis (Zeek); ICSNPP parsers add visibility into Modbus/OPC UA. [key_technology_recommendations.7.justification[0]][27] [key_technology_recommendations.7.justification[1]][28] | Snort, Wireshark (manual analysis). |
| **Data Historian** | TimescaleDB | Superior performance with high-cardinality ICS data; full SQL support via PostgreSQL enables complex, relational queries. [key_technology_recommendations.8.justification[5]][29] | InfluxDB (performance degrades with high cardinality, less flexible query language). [key_technology_recommendations.8.alternatives_considered[0]][29] |

## 3. Cybersecurity Hardening — Built-in defense-in-depth validated by ATT&CK-ICS playbooks

The simulator's cybersecurity architecture is designed with a defense-in-depth strategy, integrating security at every layer and enabling realistic attack simulation and validation. [cybersecurity_architecture_plan[0]][5]

### 3.1 Threat Model & Zoned Network Design: Plant, Control, DMZ boundaries with default-deny rules

The threat model is based on the **MITRE ATT&CK for ICS framework**, providing a comprehensive knowledge base of adversary tactics specific to industrial environments. [cybersecurity_architecture_plan.threat_model[0]][30] This allows for the simulation of realistic attack chains covering tactics from Initial Access to Impair Process Control and Impact. [attack_simulation_playbooks.1.attack_name[1]][30]

The network architecture implements a zoned model inspired by the NIST ICS cybersecurity testbed, enforced via Docker networking. [cybersecurity_architecture_plan.network_architecture[0]][1] It establishes clear trust boundaries by segmenting the network into three zones:
1. **Plant Zone:** The most critical zone, containing the MATLAB simulation and OpenPLC. It uses insecure protocols like Modbus TCP, and direct access from less trusted zones is forbidden. [cybersecurity_architecture_plan.network_architecture[1]][11]
2. **Control Zone:** An intermediary zone with the HMI, OPC UA server, and local historian.
3. **Demilitarized Zone (DMZ):** A buffer between the OT network and any external networks.

Firewalls (e.g., Linux `iptables`) are placed at each boundary with a default-deny policy and explicit allowlists based on the principle of least privilege. [cybersecurity_architecture_plan.network_architecture[3]][31]

### 3.2 Secure Comms & Secrets: OPC UA TLS, Docker Secrets, Modbus isolation

A multi-faceted strategy secures data in transit and at rest.
* **OPC UA with TLS:** For communications between the Control Zone and the OPC UA server, OPC UA is used with its highest security policies, enforcing TLS for encryption and X.509 certificate-based authentication. [cybersecurity_architecture_plan.secure_communications_and_secrets[0]][25] [cybersecurity_architecture_plan.secure_communications_and_secrets[1]][32]
* **Modbus Isolation:** The inherently insecure Modbus TCP protocol is strictly isolated within the Plant Zone. [cybersecurity_architecture_plan.secure_communications_and_secrets[0]][25]
* **Secrets Management:** Sensitive credentials are never hardcoded. **Docker Secrets** is the recommended native solution for managing passwords and keys, as it encrypts secrets and mounts them securely. [attack_simulation_playbooks[205]][33] For more advanced needs, **HashiCorp Vault** can provide centralized, dynamic secrets management. [attack_simulation_playbooks[192]][34]

### 3.3 IDS & Attack Playbooks: Suricata + Zeek detection rates for 4 scripted attacks

A combination of **Suricata** and **Zeek** provides comprehensive network monitoring. [key_technology_recommendations.7.justification[0]][27] An IDS sensor is placed to monitor all traffic between zones. Suricata provides signature-based threat detection, while Zeek provides high-fidelity logs for forensics. [attack_simulation_playbooks[199]][35] Specialized Zeek packages from the CISA ICSNPP project add deep visibility into Modbus and OPC UA traffic. [attack_simulation_playbooks[197]][28] [attack_simulation_playbooks[207]][27]

The following attack playbooks will be used to validate the security posture:

| Attack Name | Objective & Technique | Expected Detection |
| :--- | :--- | :--- |
| **Unauthorized Command Message (Logic Injection)** | **Objective:** Maliciously modify PLC state to disrupt the physical process. [attack_simulation_playbooks.0.objective[0]][24] <br> **Technique:** Use `scapy` to craft and send a malicious Modbus `Write Single Register` command to the PLC. [attack_simulation_playbooks.0.technique[0]][11] | A Suricata alert flags the unauthorized Modbus write command from a non-allowlisted IP. Zeek's `modbus.log` records the anomalous transaction for forensic analysis. [attack_simulation_playbooks.0.expected_detection[0]][11] |
| **Man-in-the-Middle (MitM)** | **Objective:** Intercept and alter HMI-to-PLC communication to inject false commands or readings. [attack_simulation_playbooks.1.objective[0]][16] <br> **Technique:** Use `ettercap` to perform an ARP spoofing attack on the OT network, redirecting traffic through an attacker machine. [attack_simulation_playbooks.1.technique[0]][16] | The HMI's OPC UA connection fails due to an untrusted certificate, causing a TLS handshake failure. Zeek logs show unexpected TCP resets and connection failures. [attack_simulation_playbooks.1.expected_detection[0]][21] |
| **Denial of Service (DoS)** | **Objective:** Overwhelm a PLC or HMI with traffic, causing a loss of view or control. [attack_simulation_playbooks.2.objective[0]][21] <br> **Technique:** Use `hping3` to execute a TCP SYN flood against the target device, exhausting its connection resources. [attack_simulation_playbooks.2.technique[0]][21] | The zone firewall logs a massive number of connection attempts. Zeek's `conn.log` shows a spike in traffic and half-open connections. Suricata detects the flood pattern and alerts. [attack_simulation_playbooks.2.expected_detection[0]][21] |
| **Packet Replay** | **Objective:** Capture and replay a legitimate command (e.g., 'start motor') at a malicious time. [attack_simulation_playbooks.3.objective[0]][21] <br> **Technique:** Use `tcpdump` to capture a valid Modbus transaction, then use `tcpreplay` to inject it back onto the network later. [attack_simulation_playbooks.3.technique[0]][21] | Detection is difficult but possible if the protocol uses sequence numbers or nonces. Advanced detection can use custom Zeek scripting to track Modbus transaction IDs and flag out-of-sequence repetitions. [attack_simulation_playbooks.3.expected_detection[0]][21] |

## 4. Observability & Testing — Golden baselines, fault injection, and KPI dashboards catch issues fast

A robust testing and observability harness is crucial for validating the simulator's fidelity and resilience. This involves a carefully selected data historian, a comprehensive observability stack, and automated testing frameworks for both regression and fault injection.

### 4.1 Telemetry Pipeline & KPIs: OpenTelemetry → Prometheus/TimescaleDB → Grafana

**TimescaleDB** is the recommended data historian over InfluxDB due to its superior performance with high-cardinality data and its full SQL support via PostgreSQL, which is critical for complex analysis. [observability_and_testing_harness.data_historian_choice[3]][29] A comprehensive, vendor-neutral observability stack will be deployed:
* **OpenTelemetry:** The standard for generating and collecting all telemetry data (metrics, logs, traces). [observability_and_testing_harness.observability_stack[1]][36]
* **Prometheus:** For collecting and storing time-series metrics, using exporters like `modbus_exporter`. [attack_simulation_playbooks[218]][37]
* **Grafana Loki & Fluent Bit:** Loki for cost-effective log aggregation, with logs forwarded by the lightweight Fluent Bit agent. [attack_simulation_playbooks[160]][38]
* **Grafana Tempo:** For storing and analyzing distributed traces to debug request flows.

A comprehensive set of Key Performance Indicators (KPIs), based on the **NIST IR 8188** framework, will be measured, covering process fidelity (e.g., reactor pressure), network performance (e.g., packet loss), and protocol performance (e.g., Modbus polling rates). [performance_benchmarking_and_hardware.performance_kpis[0]][39]

### 4.2 Regression & CI/CD: pytest + GitHub Actions compare runs to canonical traces

The strategy for automated regression testing is centered on the concept of "golden baselines." [attack_simulation_playbooks[226]][40] A golden baseline is a version-controlled recording of all relevant telemetry from a known-good test scenario. For each subsequent automated test run, new results are compared against this baseline. Defined tolerances (e.g., a sensor value must be within **±2%** of the baseline) account for minor variations. [observability_and_testing_harness.automated_testing_framework[1]][41] Any deviation exceeding these tolerances automatically triggers a test failure, alerting developers to a potential regression. These tests will be integrated into a CI/CD pipeline.

### 4.3 Fault Injection & Performance Benchmarks: Rapid valve-closure, compressor trip, DoS stress

Automated **Fault Injection Simulation (FIS)** is essential for testing system resilience. [observability_and_testing_harness.fault_injection_plan[3]][41] This involves systematically injecting faults to verify the system's response, including:
* **Sensor Faults:** Simulating drift, stuck-at values, or noise.
* **Communication Faults:** Simulating high latency, packet loss, or MitM attacks.
* **Control Logic Faults:** Introducing errors directly into the PLC's control logic.

A set of defined benchmark scenarios will be used to test the simulator's limits and response to disturbances. [performance_benchmarking_and_hardware.benchmark_scenarios[1]][39] Since no pre-configured scenarios exist for GasLib-134, the following will be developed:

| Benchmark Scenario | Objective | Key Metrics to Watch |
| :--- | :--- | :--- |
| **Rapid Valve Closure** | Generate a pressure surge to test the physics model's transient response. | Peak pressure, solver stability, settling time. |
| **Compressor Trip** | Simulate an abrupt shutdown of the compressor station to test system response. | Pressure decay rate, time to trigger low-pressure alarms. |
| **Large Network Disturbance** | Simulate simultaneous demand changes at multiple sinks to test scalability. | Simulation speed vs. real-time, CPU/memory utilization. |
| **Cybersecurity Stress Test** | Execute a DoS attack to measure performance degradation. | Packet loss rate, HMI response time, control loop latency. [performance_benchmarking_and_hardware.performance_kpis[0]][39] |

## 5. Deployment & Ops — From multi-stage Docker builds to PTP time-sync on 6-core hosts

The deployment strategy focuses on creating reproducible, resilient, and performant environments using containerization and best practices for real-time systems.

### 5.1 Image Build & Health Strategy: MCR-based image, restart policies, live-ness probes

A specific build strategy is used for each component to create optimized Docker images.
* **MATLAB/Simulink:** The `compiler.runtime.createDockerImage` function packages the compiled model with the minimal MATLAB Runtime (MCR) into a self-contained image. [docker_deployment_strategy.image_build_plan[0]][12]
* **OpenPLC:** The official Dockerfile from the project's repository is used to build a standard image. [docker_deployment_strategy.image_build_plan[0]][12]
* **Flask HMI:** A standard Dockerfile uses a Python base image and installs dependencies from a `requirements.txt` file. Multi-stage builds are used to create smaller, more secure final images.

To ensure resilience, each critical service in the `docker-compose.yml` file will have a `healthcheck` directive and a `restart: unless-stopped` policy to automatically recover from crashes. [docker_deployment_strategy.resilience_and_monitoring[0]][12]

### 5.2 Time Synchronization & Latency Mitigation: PTP vs. Chrony trade-offs, Simulink master clock

For distributed simulations requiring high precision, an external master clock is necessary. The recommended protocol is the **Precision Time Protocol (PTP / IEEE 1588)**, which can achieve sub-microsecond accuracy across a local network and is supported by Simulink Real-Time. [co_simulation_and_synchronization.master_clock_and_time_sync[0]][42] This ensures that timestamps from all components can be accurately correlated. To compensate for communication delays inherent in co-simulation, Simulink can apply **numerical compensation algorithms** to automatically correct for signal delays and reduce accumulated error. [co_simulation_and_synchronization.latency_and_error_handling[0]][43]

### 5.3 Hardware & RTOS Sizing: 32–64 GB RAM, PREEMPT_RT kernels for sub-millisecond loops

Hardware should be sized to meet performance targets.
* **CPU:** A multicore processor is essential to support Simulink's multitasking mode and run the multiple Docker containers.
* **RAM:** A generous amount (e.g., starting with **32-64GB**) is recommended.
* **NICs:** For high-precision time synchronization, Network Interface Cards that support hardware timestamping are required for PTP. [co_simulation_and_synchronization.master_clock_and_time_sync[0]][42]

For hard real-time performance with deterministic timing guarantees, a **Real-Time Operating System (RTOS)** or a real-time kernel patch like the **PREEMPT_RT patchset** for Linux should be considered. [performance_benchmarking_and_hardware.hardware_and_rtos_guidance[1]][39] This is critical for Hardware-in-the-Loop (HIL) simulations.

## 6. Implementation Roadmap — 6-month phased plan from POC to cyber-range ready

This consolidated workflow provides a step-by-step guide for implementing the simulator. [consolidated_workflow[1]][44]

### 6.1 Phase 1: Physical Process Model Creation (MATLAB/Simulink)
1. **Parse GasLib-134 Data:** In MATLAB, use `readstruct` to parse the network topology and component parameters from the XML files. [consolidated_workflow[0]][2]
2. **Build Simulink Model:** Programmatically construct the pipeline model in Simulink using the Simscape Gas library, mapping GasLib components to Simscape blocks. [consolidated_workflow[4]][9]
3. **Configure Physics and Solvers:** Select a `Real Gas` model and a stiff, variable-step solver like `ode15s`. [consolidated_workflow[4]][9]
4. **Containerize the Model:** Use MATLAB Compiler to compile the model and package it with the MATLAB Runtime into a Docker image. [consolidated_workflow[2]][1]

### 6.2 Phase 2: Control Logic & HMI (OpenPLC & Flask)
1. **Design Control Logic:** Design compressor sequencing, pressure regulation (PID), and ESD logic, potentially using Stateflow for initial design.
2. **Implement in OpenPLC:** Translate the logic into Structured Text or Ladder Diagram in the OpenPLC Editor. [consolidated_workflow[3]][45]
3. **Map I/O:** Define the Modbus address mapping for all inputs and outputs.
4. **Build Flask HMI:** Create the Flask web application using Flask-SocketIO for real-time updates and libraries like `pymodbus` or `asyncua` for protocol integration. [consolidated_workflow[5]][46] [consolidated_workflow[6]][19]

### 6.3 Phase 3: System Deployment & Orchestration (Docker & ICSsim)
1. **Create `docker-compose.yml`:** Define all services (MATLAB, OpenPLC, Flask HMI) in a Docker Compose file.
2. **Configure Networks:** Define the `ot_network` and `it_network` to enforce network segmentation.
3. **Use ICSsim:** Leverage the ICSsim framework to manage the Docker Compose environment, providing a reproducible testbed. [consolidated_workflow[1]][44]

### 6.4 Phase 4: Security Tooling & Playbooks
1. **Deploy Security Tools:** Add services for Suricata and Zeek to the `docker-compose.yml` file to monitor network traffic.
2. **Configure Firewalls:** Use `iptables` to enforce strict allowlist rules between network zones.
3. **Secure Communications:** Configure OPC UA with its built-in security features. Isolate insecure Modbus TCP traffic. [consolidated_workflow[9]][20]
4. **Execute Attack Playbooks:** Run simulated attacks using tools like `scapy` and `hping3` to validate defenses.

## 7. Risk Register & Mitigations — Top 8 technical and security pitfalls with countermeasures

| Risk Category | Potential Pitfall | Mitigation Strategy |
| :--- | :--- | :--- |
| **Performance** | Simulation runs slower than real-time, preventing HIL testing. | Profile the Simulink model to identify bottlenecks; use code generation and multitasking mode; ensure adequate multicore CPU hardware. |
| **Fidelity** | The physics model does not accurately reflect real-world gas dynamics. | Use the `Real Gas` model in Simscape; validate against known benchmarks; carefully tune solver tolerances for accuracy. [physical_process_modeling.modeling_approach[4]][9] |
| **Integration** | Components (MATLAB, OpenPLC, Flask) fail to communicate correctly. | Use standardized protocols (Modbus, OPC UA); establish a clear tag mapping strategy; implement robust error handling and retry logic in all clients. |
| **Complexity** | The multi-container architecture becomes difficult to manage and debug. | Use Docker Compose for declarative orchestration; implement centralized logging with Grafana/Loki; maintain comprehensive documentation for each service. |
| **Security** | Default configurations leave security holes (e.g., open ports, weak credentials). | Implement a zoned network architecture with default-deny firewalls; use Docker Secrets or Vault for all credentials; enforce secure OPC UA policies. [cybersecurity_architecture_plan.secure_communications_and_secrets[2]][34] |
| **PLC Logic** | Errors in the OpenPLC control logic lead to unsafe or unstable operation. | Design and validate logic in Stateflow before implementation; use automated regression testing with golden baselines to catch regressions. |
| **Data Management** | The data historian cannot handle the volume or query load from the simulation. | Choose a high-performance time-series database like TimescaleDB designed for high-cardinality data. [observability_and_testing_harness.data_historian_choice[3]][29] |
| **Time Sync** | Inaccurate time synchronization leads to incorrect event correlation and latency measurements. | Use PTP with hardware-timestamping NICs for high-precision distributed simulations; ensure all components are synchronized to a single master clock. [co_simulation_and_synchronization.master_clock_and_time_sync[0]][42] |

## 8. Success Metrics & Next Steps — Quantifiable KPIs and stretch targets for year-1

Success will be measured against a clear set of KPIs that track performance, fidelity, and resilience.

**Primary Success Metrics:**
* **Simulation Speed:** Achieve stable simulation runs at **1x real-time** speed on target hardware.
* **Control Loop Latency:** Maintain an end-to-end HMI-to-PLC control loop latency of less than **250ms**.
* **Process Fidelity:** Match key transient response curves from benchmark scenarios to within **5%** of expected values.
* **Security Detection:** Successfully detect **100%** of scripted attack playbooks (logic injection, MitM, DoS) with the deployed IDS/IPS.
* **System Uptime:** Achieve **99.9%** availability of all services during a 24-hour continuous test run, managed by Docker's auto-restart policies.

**Next Steps & Stretch Goals:**
* Expand the fault injection library to include a wider range of sensor and actuator failure modes.
* Integrate a more advanced data historian with machine learning capabilities for automated anomaly detection.
* Develop a formal curriculum for using the simulator as a cyber-range for operator and blue-team training.
* Achieve hard real-time performance (<10ms latency) by deploying the system on an RTOS with the PREEMPT_RT patch. [performance_benchmarking_and_hardware.hardware_and_rtos_guidance[1]][39]


