from machine import I2C, Pin
import struct
import time
 
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
print("Dispositivos I2C:", i2c.scan())
 
# Configuracion para shunt R002 (0.002 Ohm)
R_SHUNT     = 0.002
CURRENT_LSB = 0.001  # 1 mA por bit
CAL_VALUE   = int(0.00512 / (CURRENT_LSB * R_SHUNT))
INA226_CONFIG = 0x4527
 
print("CAL_VALUE:", CAL_VALUE)
 
# Escribir configuracion y calibracion
def write_reg(addr, reg, value):
    i2c.writeto_mem(addr, reg, struct.pack('>H', value))
 
def read_reg(addr, reg):
    return struct.unpack('>H', i2c.readfrom_mem(addr, reg, 2))[0]
 
def read_signed(addr, reg):
    val = read_reg(addr, reg)
    return val - 65536 if val > 32767 else val
 
write_reg(0x40, 0x00, INA226_CONFIG)
write_reg(0x40, 0x05, CAL_VALUE)
 
while True:
    v = read_reg(0x40, 0x02) * 1.25e-3
    c = read_signed(0x40, 0x04) * CURRENT_LSB * 1000
    p = read_reg(0x40, 0x03) * 25 * CURRENT_LSB
    print("Voltaje: {:.3f} V  |  Corriente: {:.2f} mA  |  Potencia: {:.4f} W".format(v, c, p))
    time.sleep(1)