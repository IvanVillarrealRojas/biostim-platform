# ph_sensor.py
#
# Lectura y conversión de tensión a pH para un módulo de pH
# conectado a GP26 (ADC0) de la Raspberry Pi Pico.
#
# Suposiciones:
#   - El ADC NUNCA recibe más de 3.3 V (ya sea directo o con divisor).
#   - Se hace un mapeo lineal:
#         0.0 V  -> pH 14
#         1.65 V -> pH 7
#         3.3 V  -> pH 0
#
#   - Esta relación es aproximada. Para tener medida real,
#     más adelante puedes sustituir la fórmula por una calibrada
#     con buffers pH 4 y pH 7.

from machine import ADC, Pin

# ADC en GP26
adc_ph = ADC(Pin(26))

VREF = 3.3              # máximo que verá el ADC
ADC_MAX = 65535         # read_u16() devuelve 0..65535

PH_MIN = 0.0            # pH mínimo del rango
PH_MAX = 14.0           # pH máximo del rango

def get_ph():
    """
    Lee el ADC en GP26, calcula el voltaje (0..3.3 V)
    y lo mapea linealmente a un pH entre 0 y 14.

    Devuelve:
        (ph, volt)
    """
    raw = adc_ph.read_u16()
    volt = (raw / ADC_MAX) * VREF

    # Mapeo lineal:
    #   volt = 0   -> pH = PH_MAX
    #   volt = VREF -> pH = PH_MIN
    #
    #   pH = PH_MAX - (volt / VREF) * (PH_MAX - PH_MIN)
    ph = PH_MAX - (volt / VREF) * (PH_MAX - PH_MIN)

    # Opcional: limitar por si hay pequeñas desviaciones numéricas
    if ph < PH_MIN:
        ph = PH_MIN
    if ph > PH_MAX:
        ph = PH_MAX

    return ph, volt


# Pequeño test si ejecutas este archivo directamente
if __name__ == "__main__":
    import time
    while True:
        ph, volt = get_ph()
        print("Voltaje:", round(volt, 3), "V   pH:", round(ph, 2))
        time.sleep(1)
