# wifi.py  – helper sencillo para conectar al WiFi en la Pico W
import network
import time

def connect_wifi(ssid, password, timeout=20):
    """
    Conecta la Raspberry Pi Pico W a la red WiFi dada.
    Lanza OSError si no se puede conectar.
    """
    wlan = network.WLAN(network.STA_IF)

    try:
        wlan.active(True)
    except OSError as e:
        # Aquí suele saltar el EPERM si el chip WiFi no está disponible
        print("Error activando WiFi:", e)
        print("¿Tu placa es una *Raspberry Pi Pico W* (con WiFi)?")
        raise

    if wlan.isconnected():
        print("Ya estaba conectada:", wlan.ifconfig())
        return wlan

    print("Conectando a WiFi…")
    wlan.connect(ssid, password)

    t0 = time.ticks_ms()
    while not wlan.isconnected() and time.ticks_diff(time.ticks_ms(), t0) < timeout * 1000:
        print(".", end="")
        time.sleep(1)

    if not wlan.isconnected():
        print("\nNo se pudo conectar al WiFi.")
        raise OSError("No se pudo conectar a la red WiFi")

    print("\nConectado al WiFi. IFConfig:", wlan.ifconfig())
    return wlan
