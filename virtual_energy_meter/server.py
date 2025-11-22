import random
import threading
import time
from dataclasses import dataclass

from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
import pymodbus
pymodbus_version = pymodbus.__version__


@dataclass
class MeterState:
    voltage_l1: float = 230.0
    voltage_l2: float = 230.0
    voltage_l3: float = 230.0
    current_l1: float = 10.0
    current_l2: float = 8.0
    current_l3: float = 12.0
    pf: float = 0.96      # power factor
    freq: float = 50.0    # Hz

    def update(self):
        """Update the simulated values slightly each cycle."""
        def jitter(val, span):
            return val + random.uniform(-span, span)

        # Simple noisy drift
        self.voltage_l1 = jitter(self.voltage_l1, 1.0)
        self.voltage_l2 = jitter(self.voltage_l2, 1.0)
        self.voltage_l3 = jitter(self.voltage_l3, 1.0)

        self.current_l1 = max(0.0, jitter(self.current_l1, 0.2))
        self.current_l2 = max(0.0, jitter(self.current_l2, 0.2))
        self.current_l3 = max(0.0, jitter(self.current_l3, 0.2))

        self.pf = max(0.7, min(1.0, jitter(self.pf, 0.01)))
        self.freq = jitter(self.freq, 0.02)

    def powers_kw(self):
        """Very rough 3-phase active power calc: P = V * I * pf / 1000."""
        p1 = self.voltage_l1 * self.current_l1 * self.pf / 1000.0
        p2 = self.voltage_l2 * self.current_l2 * self.pf / 1000.0
        p3 = self.voltage_l3 * self.current_l3 * self.pf / 1000.0
        return p1, p2, p3, (p1 + p2 + p3)


def create_datastore():
    """
    Create a Modbus datastore with our register map.

    Holding registers (4x) layout (1-based Modbus addresses):
    40001: V_L1 (V * 10)
    40002: V_L2
    40003: V_L3
    40004: I_L1 (A * 100)
    40005: I_L2
    40006: I_L3
    40007: P_L1 (kW * 100)
    40008: P_L2
    40009: P_L3
    40010: P_total (kW * 100)
    40011: PF (×1000)
    40012: Frequency (Hz ×100)
    """
    # Start block at address 1 so register 1 corresponds to 40001
    block = ModbusSequentialDataBlock(1, [0] * 100)  # 100 holding registers
    store = ModbusSlaveContext(
        di=None, co=None, hr=block, ir=None
    )
    return ModbusServerContext(slaves=store, single=True)



def update_loop(context: ModbusServerContext, state: MeterState, interval: float = 1.0):
    """Background thread that updates the meter values in the datastore."""
    slave_id = 0x00  # ignored when single=True
    while True:
        time.sleep(interval)
        state.update()

        p1, p2, p3, ptot = state.powers_kw()

        slave = context[slave_id]
        set_hr = slave.setValues

        # Scale & write values
        vals = {}

        # Voltages (×10)
        vals[0] = int(state.voltage_l1 * 10)
        vals[1] = int(state.voltage_l2 * 10)
        vals[2] = int(state.voltage_l3 * 10)

        # Currents (×100)
        vals[3] = int(state.current_l1 * 100)
        vals[4] = int(state.current_l2 * 100)
        vals[5] = int(state.current_l3 * 100)

        # Powers (×100)
        vals[6] = int(p1 * 100)
        vals[7] = int(p2 * 100)
        vals[8] = int(p3 * 100)
        vals[9] = int(ptot * 100)

        # PF (×1000)
        vals[10] = int(state.pf * 1000)

        # Frequency (×100)
        vals[11] = int(state.freq * 100)

        # Apply to datastore
        for address, value in vals.items():
            # 3 = function code for holding registers
            set_hr(3, address + 1, [value])



def run_server(host: str = "0.0.0.0", port: int = 5020):
    context = create_datastore()
    state = MeterState()

    # Start background updater
    t = threading.Thread(target=update_loop, args=(context, state), daemon=True)
    t.start()

    identity = ModbusDeviceIdentification()
    identity.VendorName = "VirtualEnergyMeter"
    identity.ProductCode = "VEM"
    identity.VendorUrl = "https://github.com/Eltonsean69x/virtual-energymeter"
    identity.ProductName = "Virtual Energy Meter"
    identity.ModelName = "VEM-Simple-3P"
    identity.MajorMinorRevision = pymodbus_version

    print(f"Starting Virtual Energy Meter on {host}:{port}")
    print("Holding register map (1-based addresses):")
    print("  40001–40003: V_L1, V_L2, V_L3 (V ×10)")
    print("  40004–40006: I_L1, I_L2, I_L3 (A ×100)")
    print("  40007–40009: P_L1, P_L2, P_L3 (kW ×100)")
    print("  40010      : P_total (kW ×100)")
    print("  40011      : PF (×1000)")
    print("  40012      : Frequency (Hz ×100)")

    StartTcpServer(
        context,
        identity=identity,
        address=(host, port),
    )


if __name__ == "__main__":
    run_server()
