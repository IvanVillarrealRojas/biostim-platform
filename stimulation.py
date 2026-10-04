"""
stimulation.py
Monitorización de corriente/voltaje mediante INA226 (I2C).
Con fuente regulable externa conectada directamente a los electrodos
a través del INA226, sin DRV8833.

Configuración hardware:
    Fuente (+) → INA226 V+/C+
    INA226 V-/C- → Electrodo positivo
    Electrodo negativo → GND de la fuente = GND común del sistema

INA226 (I2C):
    SDA → GP4
    SCL → GP5
    Dirección I2C: 0x40
"""

import struct

# ── INA226 registros ──────────────────────────────────────────────────────────
INA226_ADDR       = 0x40
REG_CONFIG        = 0x00
REG_SHUNT_VOLTAGE = 0x01
REG_BUS_VOLTAGE   = 0x02
REG_POWER         = 0x03
REG_CURRENT       = 0x04
REG_CALIBRATION   = 0x05

# avg=16, VBUS CT=1.1ms, VSH CT=1.1ms, modo continuo
INA226_CONFIG = 0x4527

# Resistencia shunt del módulo (R002 = 0.002 Ω)
R_SHUNT     = 0.002
CURRENT_LSB = 0.001  # 1 mA por bit
CAL_VALUE   = int(0.00512 / (CURRENT_LSB * R_SHUNT))


class INA226:
    def __init__(self, i2c, addr=INA226_ADDR):
        self.i2c  = i2c
        self.addr = addr
        self._write_reg(REG_CONFIG,      INA226_CONFIG)
        self._write_reg(REG_CALIBRATION, CAL_VALUE)

    def _write_reg(self, reg, value):
        self.i2c.writeto_mem(self.addr, reg, struct.pack('>H', value))

    def _read_reg(self, reg):
        return struct.unpack('>H', self.i2c.readfrom_mem(self.addr, reg, 2))[0]

    def _read_signed(self, reg):
        val = self._read_reg(reg)
        return val - 65536 if val > 32767 else val

    def read_bus_voltage(self):
        """Voltaje en el electrodo positivo respecto a GND (V)."""
        return self._read_reg(REG_BUS_VOLTAGE) * 1.25e-3

    def read_current(self):
        """Corriente inyectada en la muestra (A)."""
        return self._read_signed(REG_CURRENT) * CURRENT_LSB

    def read_power(self):
        """Potencia entregada (W)."""
        return self._read_reg(REG_POWER) * 25 * CURRENT_LSB