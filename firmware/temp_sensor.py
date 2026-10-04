# temp_sensor.py
#
# Clase para leer sensores DS18B20 mediante el protocolo 1-Wire.
# Permite tener dos sensores (interno y ambiente) en el mismo pin GP21,
# seleccionándolos por su índice en el bus.
#
# Conexión: ambos DS18B20 → GP21, resistencia pull-up de 4.7 kΩ a 3.3 V.

import machine
import onewire
import ds18x20
import time


class TempSensor:
    def __init__(self, pin_num, rom_index=0):
        """
        pin_num:   número de GPIO al que está conectado el bus 1-Wire.
        rom_index: índice del sensor en el bus (0 = primero encontrado,
                   1 = segundo encontrado). Permite distinguir interno
                   de ambiente cuando comparten el mismo pin.
        """
        self.pin       = machine.Pin(pin_num)
        self.ow        = onewire.OneWire(self.pin)
        self.ds        = ds18x20.DS18X20(self.ow)
        self.rom_index = rom_index

        self.roms = self.ds.scan()
        print(f"[TempSensor] GP{pin_num} → {len(self.roms)} dispositivo(s) encontrado(s)")

        if not self.roms:
            raise RuntimeError(
                f"No se encontró ningún DS18B20 en GP{pin_num}. "
                "Revisa el cableado y la resistencia pull-up de 4.7 kΩ."
            )
        if rom_index >= len(self.roms):
            raise RuntimeError(
                f"Se pidió el sensor con índice {rom_index} "
                f"pero solo hay {len(self.roms)} sensor(es) en GP{pin_num}."
            )

    def read_temp_c(self):
        """Devuelve la temperatura en °C del sensor seleccionado por rom_index."""
        self.ds.convert_temp()
        time.sleep_ms(750)          # Tiempo de conversión del DS18B20 (máx. 750 ms)
        return self.ds.read_temp(self.roms[self.rom_index])
