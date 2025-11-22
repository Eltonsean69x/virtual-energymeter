\# Virtual Energy Meter



A small \*\*virtual 3-phase energy meter\*\* for SCADA / PLC / PME engineers.



It has two parts:



\- ✅ A \*\*Modbus TCP server\*\* that emulates a 3-phase energy meter (voltages, currents, kW, PF, frequency).

\- ✅ A \*\*desktop GUI dashboard\*\* (Python + Tkinter) that shows live values updating every second.



Use it to:



\- Test SCADA / HMI / PLC / PME integrations without real hardware

\- Demo Modbus connectivity

\- Train junior engineers on register maps and live data



---



\## Features



\- Modbus TCP server on configurable host/port (default: `0.0.0.0:5020`)

\- Simulated 3-phase:

&nbsp; - Phase-phase voltages

&nbsp; - Phase currents

&nbsp; - Phase active power

&nbsp; - Total active power

&nbsp; - Power factor

&nbsp; - Frequency

\- Simple \*\*register map\*\* (holding registers 40001–40012)

\- \*\*GUI dashboard\*\* with:

&nbsp; - Per-phase table (V, A, kW)

&nbsp; - Totals panel (kW, PF, Hz)

&nbsp; - Start / pause simulation

&nbsp; - Profiles:

&nbsp;   - Light / Office

&nbsp;   - Industrial / Heavy

&nbsp;   - Random test

&nbsp; - Noise toggle (enable / disable random variation)

&nbsp; - Status bar with last update time



---



\## Installation



Requirements:



\- Python 3.10+ (tested with 3.13)

\- `pymodbus` < 3.10



Clone the repo and install the dependency:



```bash

git clone https://github.com/Eltonsean69x/virtual-energymeter.git

cd virtual-energymeter

python -m pip install "pymodbus<3.10"



