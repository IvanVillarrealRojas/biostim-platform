"""
ads1220.py
Driver para el ADS1220 (ADC 24 bits, SPI) en MicroPython.
Raspberry Pi Pico 2W:
    SCLK → GP18
    MOSI → GP19
    MISO → GP16
    CS   → GP17
    DRDY → GP12
"""

from machine import SPI, Pin
import time

# Comandos ADS1220
CMD_RESET   = 0x06
CMD_START   = 0x08
CMD_RDATA   = 0x10
CMD_WREG    = 0x40
CMD_RREG    = 0x20

# Registro 0: MUX AIN0 vs AVSS, ganancia 1, PGA habilitado
REG0 = 0x06   # MUX = 0000 (AIN0/AIN1), Ganancia = 1, PGA enabled

# Registro 1: Data rate 20 SPS, modo normal, modo continuo
REG1 = 0x04   # DR=000 (20SPS), Mode=00 (normal), CM=1 (continuo), TS=0, BCS=0

# Registro 2: referencia interna, 50/60Hz rechazo, IDAC apagado
REG2 = 0x70   # VREF=01 (AVDD/AVSS), 50/60Hz=11, IDAC=000

# Registro 3: IDAC1 e IDAC2 desconectados
REG3 = 0x00

VREF = 3.3       # Tensión de referencia (AVDD - AGND)
FULLSCALE = 2**23  # ADS1220 es de 24 bits con signo → 2^23


class ADS1220:
    def __init__(self, spi_id=0, cs_pin=17, drdy_pin=12):
        self.spi = SPI(
            spi_id,
            baudrate=1_000_000,
            polarity=0,
            phase=1,
            sck=Pin(18),
            mosi=Pin(19),
            miso=Pin(16)
        )
        self.cs   = Pin(cs_pin,   Pin.OUT, value=1)
        self.drdy = Pin(drdy_pin, Pin.IN)
        self._reset()
        self._configure()

    def _reset(self):
        self.cs(0)
        self.spi.write(bytes([CMD_RESET]))
        self.cs(1)
        time.sleep_ms(1)

    def _configure(self):
        """Escribe los 4 registros de configuración de una sola vez."""
        self.cs(0)
        self.spi.write(bytes([CMD_WREG | 0x03, REG0, REG1, REG2, REG3]))
        self.cs(1)
        # Arrancar conversión continua
        self.cs(0)
        self.spi.write(bytes([CMD_START]))
        self.cs(1)

    def _wait_drdy(self, timeout_ms=200):
        """Espera a que DRDY baje (dato listo)."""
        t0 = time.ticks_ms()
        while self.drdy.value() == 1:
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_ms:
                return False
        return True

    def read_raw(self):
        """Lee el valor crudo de 24 bits con signo."""
        if not self._wait_drdy():
            return None
        self.cs(0)
        self.spi.write(bytes([CMD_RDATA]))
        buf = self.spi.read(3)
        self.cs(1)

        # Reconstruir entero de 24 bits
        raw = (buf[0] << 16) | (buf[1] << 8) | buf[2]

        # Convertir a entero con signo
        if raw >= FULLSCALE:
            raw -= 2 * FULLSCALE
        return raw


    def read_voltage(self):
        """Devuelve la tensión en voltios en AIN0 referenciada a AGND."""
        raw = self.read_raw()
        if raw is None:
            return None
        return (raw / FULLSCALE) * VREF

    def read_differential_mv(self):
        """Devuelve la diferencia de potencial en milivoltios."""
        v = self.read_voltage()
        if v is None:
            return None
        # Restar VREF/2 para obtener el valor centrado respecto a 1.65 V
        return (v - VREF / 2) * 1000
