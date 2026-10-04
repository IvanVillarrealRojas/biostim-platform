"""
main.py  —  Plataforma bioelectrónica de bajo coste
Fuente regulable externa conectada directamente a electrodos via INA226.
Sin DRV8833. La estimulación se controla manualmente desde la fuente.
"""

from wifi import connect_wifi
from temp_sensor import TempSensor
from ph_sensor import get_ph
from ads1220 import ADS1220
from mux import DualMUX
from stimulation import INA226

import network, socket
from machine import I2C, Pin

# ── Credenciales WiFi ─────────────────────────────────────────────────────────
SSID     = "YOUR_SSID"
PASSWORD = "YOUR_PASSWORD"

# ── Distancias entre electrodos (mm) ─────────────────────────────────────────
DISTANCES = {"E1-E2": 20.0, "E1-E3": 40.0, "E2-E3": 20.0}

# ── Inicialización ────────────────────────────────────────────────────────────
connect_wifi(SSID, PASSWORD)
ip = network.WLAN(network.STA_IF).ifconfig()[0]
print("IP:", ip)

sensor_interno  = TempSensor(pin_num=21, rom_index=0)
sensor_ambiente = TempSensor(pin_num=21, rom_index=1)
adc   = ADS1220()
muxs  = DualMUX()
i2c   = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
monitor = INA226(i2c)


# ── Lectura de todos los sensores ─────────────────────────────────────────────
def read_all():
    ti        = sensor_interno.read_temp_c()
    te        = sensor_ambiente.read_temp_c()
    ph, volt  = get_ph()
    pairs     = muxs.scan_all_pairs(adc)
    sv        = monitor.read_bus_voltage()
    sc        = monitor.read_current()
    sp        = monitor.read_power()
    return ti, te, ph, volt, pairs, sv, sc, sp


def build_json(ti, te, ph, volt, pairs, sv, sc, sp):
    def fv(v): return "{:.4f}".format(v) if v is not None else "null"
    return (
        '{{"temp_int":{ti},"temp_ext":{te},"ph":{ph},"ph_volt":{pv},'
        '"diff_E1E2":{d12},"diff_E1E3":{d13},"diff_E2E3":{d23},'
        '"stim_voltage":{sv},"stim_current":{sc},"stim_power":{sp}}}'
    ).format(
        ti=fv(ti), te=fv(te), ph=fv(ph), pv=fv(volt),
        d12=fv(pairs.get("E1-E2")), d13=fv(pairs.get("E1-E3")), d23=fv(pairs.get("E2-E3")),
        sv=fv(sv), sc=fv(sc), sp=fv(sp)
    )


# ── Utilidades HTTP ───────────────────────────────────────────────────────────
def send_file(cl, path, mime):
    try:
        cl.send("HTTP/1.1 200 OK\r\nContent-Type: {}\r\n\r\n".format(mime))
        with open(path, "rb") as f:
            while True:
                chunk = f.read(512)
                if not chunk: break
                cl.sendall(chunk)
    except OSError:
        pass


def parse_param(req, key):
    try:
        idx = req.index(key + "=") + len(key) + 1
        end = req.find("&", idx)
        return req[idx:] if end == -1 else req[idx:end]
    except ValueError:
        return None


# ── Servidor web ──────────────────────────────────────────────────────────────
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
print("Dashboard: http://{}".format(ip))


# ── Bucle principal ───────────────────────────────────────────────────────────
while True:
    try:
        cl, addr = s.accept()
        req = cl.recv(1024).decode("utf-8", "ignore")

        if "GET /data" in req:
            ti, te, ph, volt, pairs, sv, sc, sp = read_all()
            body = build_json(ti, te, ph, volt, pairs, sv, sc, sp)
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
            cl.sendall(body)

        else:
            send_file(cl, "dashboard.html", "text/html")

        cl.close()

    except OSError:
        try: cl.close()
        except: pass
