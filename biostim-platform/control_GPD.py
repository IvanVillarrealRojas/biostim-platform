import serial, requests, time, csv

# ── Configuración ─────────────────────────────────────────────
PICO_URL     = "http://192.168.43.208/data"   # IP de tu Pico ------------- CHANGE
COM_PORT     = "COM8"                          # ------------- CHANGE
BAUD         = 9600

V_TARGET     = 9.0     # V objetivo en el electrodo (lectura INA226) ------------- CHANGE
V_SOURCE_MAX = 15.0    # techo de seguridad para la fuente ------------- CHANGE
V_SOURCE_MIN = 0.0
I_SAFETY     = 0.050   # 50 mA límite de corriente — parada de emergencia   ------------- CHANGE
KP           = 0.5     # ganancia proporcional, empezar bajo  ------------- CHANGE

PERIOD_S     = 1.0     # frecuencia del bucle

# ── Inicialización ────────────────────────────────────────────
psu = serial.Serial(COM_PORT, BAUD, timeout=1)

def send(cmd):
    psu.write((cmd + "\n").encode())
    time.sleep(0.02)   # respetar los 10 ms mínimos

v_source = V_TARGET
send(f"ISET1:{I_SAFETY:.3f}")
send(f"VSET1:{v_source:.3f}")
send("OUT1")

# ── Log CSV ───────────────────────────────────────────────────
log = open("test_bucle.csv", "w", newline="")
writer = csv.writer(log)
writer.writerow(["t_s", "v_elec", "i_elec_mA", "v_source_cmd", "evento"])
t0 = time.time()

# ── Bucle de control ──────────────────────────────────────────
try:
    while True:
        try:
            r = requests.get(PICO_URL, timeout=5).json()
            v_elec = float(r["stim_voltage"])
            i_elec = float(r["stim_current"])
        except Exception as e:
            print("Error leyendo Pico:", e)
            time.sleep(PERIOD_S)
            continue

        # ── Chequeo de seguridad ANTES de tocar la fuente ──────
        if i_elec > I_SAFETY:
            send("OUT0")
            print(f"⚠ Parada de emergencia por sobrecorriente: "
                  f"i_elec={i_elec*1000:.1f} mA > {I_SAFETY*1000:.1f} mA")
            writer.writerow([f"{time.time()-t0:.1f}", f"{v_elec:.3f}",
                              f"{i_elec*1000:.2f}", f"{v_source:.3f}",
                              "PARADA_EMERGENCIA"])
            log.flush()
            break

        error    = V_TARGET - v_elec
        v_source = max(V_SOURCE_MIN, min(V_SOURCE_MAX, v_source + KP * error))
        send(f"VSET1:{v_source:.3f}")

        print(f"V_elec={v_elec:.3f} V  I_elec={i_elec*1000:.1f} mA  "
              f"→ VSET={v_source:.3f} V")

        writer.writerow([f"{time.time()-t0:.1f}", f"{v_elec:.3f}",
                          f"{i_elec*1000:.2f}", f"{v_source:.3f}", ""])
        log.flush()

        time.sleep(PERIOD_S)

except KeyboardInterrupt:
    send("OUT0")
    print("Parada segura por el usuario.")

finally:
    log.close()
    psu.close()