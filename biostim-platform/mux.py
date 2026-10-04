"""
mux.py
Controlador para dos multiplexores CD74HC4067 (MUX A y MUX B).
MUX A (IN+): S0→GP6, S1→GP7, S2→GP8
MUX B (IN-): S0→GP9, S1→GP10, S2→GP11
EN de ambos conectado a GND (siempre habilitado).
"""

from machine import Pin


class MUX:
    def __init__(self, s0_pin, s1_pin, s2_pin):
        self.s0 = Pin(s0_pin, Pin.OUT)
        self.s1 = Pin(s1_pin, Pin.OUT)
        self.s2 = Pin(s2_pin, Pin.OUT)
        self.select(0)  # Canal 0 por defecto

    def select(self, channel):
        """
        Selecciona el canal (0-7) del multiplexor.
        Canal 0 → Electrodo 1 (5 mm)
        Canal 1 → Electrodo 2 (centro)
        Canal 2 → Electrodo 3 (45 mm)
        """
        if channel < 0 or channel > 7:
            raise ValueError("Canal debe estar entre 0 y 7")
        self.s0(channel & 0x01)
        self.s1((channel >> 1) & 0x01)
        self.s2((channel >> 2) & 0x01)


class DualMUX:
    """
    Gestiona los dos multiplexores para la medida diferencial.
    MUX A → INA333 VIN+ (IN+)
    MUX B → INA333 VIN- (IN-)
    """
    def __init__(self):
        self.mux_a = MUX(s0_pin=6,  s1_pin=7,  s2_pin=8)
        self.mux_b = MUX(s0_pin=9,  s1_pin=10, s2_pin=11)

    def select_pair(self, ch_plus, ch_minus):
        """
        Selecciona el par de electrodos para la medida diferencial.
        ch_plus:  electrodo conectado a VIN+ (0, 1 o 2)
        ch_minus: electrodo conectado a VIN- (0, 1 o 2)
        """
        self.mux_a.select(ch_plus)
        self.mux_b.select(ch_minus)

    def scan_all_pairs(self, adc, delay_ms=50):
        """
        Recorre todas las combinaciones diferenciales posibles y
        devuelve un diccionario con las diferencias de potencial en mV.
        """
        pairs = [(0, 1), (0, 2), (1, 2)]
        results = {}
        for a, b in pairs:
            self.select_pair(a, b)
            import time
            time.sleep_ms(delay_ms)  # Tiempo de estabilización del MUX
            mv = adc.read_differential_mv()
            results[f"E{a+1}-E{b+1}"] = mv
        return results
