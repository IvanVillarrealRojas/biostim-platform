# Biostim-platform
 
**Low-cost, open-source bioelectronic platform for electrical stimulation and real-time environmental monitoring of cell-laden hydrogels.**
 
A compact, modular system that applies controlled electrical stimulation to a cell-culture hydrogel while continuously monitoring the variables that matter for cell viability: temperature, pH, and the electric field distributed across the sample. It is built entirely from low-cost, widely available components and a single Raspberry Pi Pico 2 W, and it exposes all of its data through a self-hosted web dashboard reachable from any browser on the same network.
 
The goal of the project is to make in-vitro electrostimulation accessible to laboratories, universities and schools that cannot justify the cost of commercial systems, which are typically closed, expensive, and difficult to adapt to a specific experiment.
 
---
 
## Why this project exists
 
Electrical signalling governs a wide range of biological processes, and electrostimulation of cell cultures is an increasingly common technique for studying how different cell types respond to electric fields. The commercial equipment that enables this is usually priced in the thousands of euros, built on closed architectures, and offers little room for customisation or real-time data access.
 
This platform is a response to that gap. It integrates, in a single and reusable device that costs roughly €110 in materials per unit, functions that are normally split across several independent instruments: programmable stimulation, distributed field measurement inside the hydrogel, continuous environmental monitoring, and a real-time control interface.
 
---
 
## Features
 
- **Analog acquisition chain** — Three platinum sensing electrodes distributed along the channel, read through two CD74HC4067 multiplexers, an INA333 instrumentation amplifier centred on a 1.65 V reference, and a 24-bit ADS1220 ADC over SPI. Any differential pair of electrodes can be selected by software to measure the potential difference and compute the local electric field (E = ΔV/d).
- **Stimulation monitoring** — An INA226 sensor measures the real voltage and current delivered to the electrodes, allowing the system to detect effects such as electrode polarisation, where the effective voltage at the electrode drops over time even while the source holds constant.
- **Environmental monitoring** — Two DS18B20 digital temperature sensors on a shared 1-Wire bus (one internal to the channel, one ambient reference) and a glass-electrode pH probe through a conditioning module.
- **Self-hosted web dashboard** — A single-page interface served directly by the Pico over Wi-Fi. Live status cards, historical charts for temperature, pH and electric field, a configurable optimal-zone threshold system, and optional auto-stop safety limits.
- **Optional closed-loop control** — A host-side Python script (`control_GPD.py`) that reads the real electrode voltage from the dashboard and automatically adjusts a GW Instek GPD-series bench power supply over serial to hold a target voltage, compensating for electrode polarisation, with a current safety cut-off.
- **Fully modular firmware** — Written in MicroPython, one module per subsystem, so each stage can be understood, tested and replaced independently.
---
 
## Hardware architecture
 
The Raspberry Pi Pico 2 W coordinates every stage of the system. The complete pin map is as follows.
 
| GPIO | Protocol | Connection |
|------|----------|------------|
| GP2 | Digital | DRV8833 IN1 |
| GP3 | Digital | DRV8833 IN2 (unipolar configuration) |
| GP4 | I2C SDA | INA226 |
| GP5 | I2C SCL | INA226 |
| GP6, GP7, GP8 | Digital | MUX A select lines S0, S1, S2 |
| GP9, GP10, GP11 | Digital | MUX B select lines S0, S1, S2 |
| GP12 | Digital | ADS1220 DRDY |
| GP16 | SPI MISO | ADS1220 |
| GP17 | SPI CS | ADS1220 |
| GP18 | SPI SCLK | ADS1220 |
| GP19 | SPI MOSI | ADS1220 |
| GP21 | 1-Wire | DS18B20 internal + DS18B20 ambient (shared bus) |
| GP26 | ADC | pH module output (Po) |
 
The acquisition stage is protected against the higher-voltage stimulation stage by a cascade of series resistors, BAT54 clamp diodes, bias resistors to the 1.65 V reference, and input/output RC filtering. The physical platform is a 3D-printed resin chamber with a confined millimetric channel and an interchangeable glass-slide base for microscope compatibility.

The complete electronic schematic, including the full protection cascade, is available in hardware/ as a viewable PDF. An editable EasyEDA source (schematic.epro2) is also provided. The password to open it can be requested by email at ivi.280504@gmail.com.

The 3D-printable models for the chamber and the removable spacers are in 3d-models/, provided as STL files ready for slicing and as OBJ/MTL for viewing and editing. They were printed in Clear V4 resin on a Formlabs SLA printer.
 
### Stimulation and INA226 wiring
 
The stimulation voltage is supplied by an external regulated power supply connected to the electrodes through the INA226. Bench testing was carried out with a GW Instek GPD-2303 programmable supply, which is also the unit the optional `control_GDP.py` script drives over serial. The module used here exposes separate **V−**, **Current (+/−)** and **V+** screw terminals; the connection that correctly reports both the electrode voltage and the injected current is
 
```
V+        -> positive electrode        (measures the real voltage at the electrode)
V-        -> common GND
Current+  -> power-supply positive
Current-  -> positive electrode
Negative electrode -> common GND
Power-supply GND   -> common GND
```
 
With this wiring the bus-voltage reading reflects the voltage actually present at the electrode relative to ground, and the current is measured through the module's internal shunt (R002 = 0.002 Ω).

The system does not require a bench supply. It can equally be driven from batteries by inserting an H-bridge such as the DRV8833 between the battery and the electrodes, provided the battery voltage stays within the limits of the H-bridge and the rest of the system's protection stages. Driving the H-bridge from the Pico's PWM then allows lower or variable effective voltages to be produced by adjusting frequency and duty cycle. Operation has been verified in this configuration with a standard 9 V battery.
 
---
 
## Repository structure
 
```
biostim-platform/
├── firmware/            MicroPython code that runs on the Raspberry Pi Pico 2 W
│   ├── main.py          Entry point: initialises all modules, serves the dashboard
│   ├── wifi.py          Wi-Fi connection helper
│   ├── temp_sensor.py   DS18B20 driver (shared 1-Wire bus, selection by ROM index)
│   ├── ph_sensor.py     pH reading and voltage-to-pH mapping
│   ├── ads1220.py       ADS1220 24-bit ADC driver (SPI)
│   ├── mux.py           CD74HC4067 dual-multiplexer controller
│   └── stimulation.py   INA226 voltage/current/power monitor (I2C)
├── dashboard/
│   └── dashboard.html   Self-contained web interface (HTML/CSS/JS)
├── pc/
│   └── control_GPD.py   Optional closed-loop voltage control (runs on a PC)
├── hardware/
│   └── schematic.pdf    Complete electronic schematic (viewable)
│   └── schematic.epro2  Editable source (EasyEDA; password on request)
├── 3d-models/
│   ├── platform/        Main microfluidic chamber (STL + OBJ/MTL)
│   └── spacers/         Removable channel spacers (STL + OBJ/MTL)
├── README.md
└── LICENSE
```
 
---
 
## Getting started
 
### 1. Flash MicroPython
 
Install the latest MicroPython firmware for the Raspberry Pi Pico 2 W following the official Raspberry Pi instructions.
 
### 2. Upload the firmware
 
Copy every file from `firmware/` and the `dashboard/dashboard.html` file to the root of the Pico, using Thonny or the MicroPico extension for VS Code. The dashboard must sit next to `main.py` because the Pico serves it as a static file.
 
### 3. Set your Wi-Fi credentials
 
Edit the `SSID` and `PASSWORD` fields at the top of `main.py`.
 
### 4. Run
 
Execute `main.py`. The console prints the IP address assigned to the Pico. Open that address in any browser on the same network to reach the dashboard.
 
### 5. (Optional) Closed-loop control
 
To hold a constant voltage at the electrode and compensate for polarisation, connect a GW Instek GPD-series supply over serial, edit the `PICO_URL`, `COM_PORT` and target parameters at the top of `pc/control_GPD.py`, and run it on your computer. It logs the session to CSV and includes a current safety cut-off.
 
---
 
## Current status
 
The platform is functional and has been validated on the bench: Wi-Fi connectivity, the full sensor suite, the acquisition chain, and the INA226 voltage and current measurements all work, and the dashboard updates in real time. The system is suitable for use in experiments today, and remains under active development toward a fully polished release.
 
### Planned work
 
- Integration of the circuit onto a dedicated PCB to replace the breadboard wiring and enable an enclosure.
- Permanent, repeatable electrode connectors on the platform surface.
- Extension to bipolar stimulation with appropriate filtering.
- Remote dashboard access beyond the local network (cloud/IoT or a USB desktop application).
- Geometric optimisation of the chamber with smaller, specialised sensors for flexible experiment configurations.
- Validation with live cell cultures.
  
---
 
## Credits and attribution
 
This platform — its original concept, hardware architecture, firmware and dashboard — was designed and developed by **Iván Villarreal Rojas** and **Ximena Natalia L Gamiz Salas** (2026).
 
If you use, build upon, fork or continue this project, in whole or in part, please credit the original work:
 
> Based on the biostim-platform originally designed and developed by Iván Villarreal Rojas and Ximena Natalia L Gamiz Salas (2026).
 
Academic or derivative work that extends this platform should cite the original author accordingly.
 
---
 
## License
 
Released under the MIT License. See [LICENSE](LICENSE) for details. You are free to use, modify and distribute this work, including commercially, provided the original copyright and attribution are retained.
