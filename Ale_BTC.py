import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
try:
    client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
except Exception as e:
    print(f"Error de conexión inicial: {e}")

# === PARÁMETROS ===
espera_segundos = 14
palanca = 10
ganancia_neta_ale = 0.50 
comision = 0.20
archivo_memoria = "memoria_quantum.txt"

# === ESTADO ===
capital_base = 30.00
ganancia_hoy = 0.0
perdida_hoy = 0.0
contador_ops = 0
en_operacion = False

def registrar(tipo, msg, valor=0):
    global contador_ops, ganancia_hoy, perdida_hoy
    ts = datetime.now().strftime('%H:%M:%S')
    try:
        with open(archivo_memoria, "a") as f:
            f.write(f"[{ts}] {tipo} | {msg}\n")
    except: pass
    if tipo == "CIERRE":
        contador_ops += 1
        if valor > 0: ganancia_hoy += valor
        else: perdida_hoy += abs(valor)

print("🚀 IA QUANTUM: MODO ANTI-PAUSA ACTIVADO")

while True:
    try:
        # 1. CAPTURA DE PRECIOS
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        p_sol = float(ticker['price'])
        
        # 2. LECTURA DE VELAS (Aseguramos que no falle)
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=3)
        if not klines or len(klines) < 3:
            time.sleep(5)
            continue

        v_actual_open = float(klines[-1][1])
        v_anterior_close = float(klines[-2][4])
        
        neto_total = ganancia_hoy - perdida_hoy

        # --- TABLERO EN PANTALLA ---
        print(f"\n🔱 VELAS | SOL: ${p_sol:.2f} | NETO: ${neto_total:.2f}")
        print(f"🕯️ ACTUAL: {'VERDE 🟢' if p_sol > v_actual_open else 'ROJA 🔴'}")
        print(f"🔢 OPS: {contador_ops}/20")
        print("-" * 40)

        if not en_operacion:
            # LÓGICA DE PULSO: Si la vela actual rompe el cierre de la anterior
            # Y el color coincide, entramos por el patrón de 3 velas.
            if p_sol > v_actual_open and p_sol > v_anterior_close:
                en_operacion = True
                p_entrada = p_sol
                tipo_op = "LONG 🟢"
                registrar("ENTRADA", f"LONG en ${p_sol} (Rompe al alza)")
            
            elif p_sol < v_actual_open and p_sol < v_anterior_close:
                en_operacion = True
                p_entrada = p_sol
                tipo_op = "SHORT 🔴"
                registrar("ENTRADA", f"SHORT en ${p_sol} (Rompe a la baja)")
        
        else:
            # GESTIÓN DE SALIDA AMETRALLADORA
            diff = ((p_sol - p_entrada) / p_entrada) if "LONG" in tipo_op else ((p_entrada - p_sol) / p_entrada)
            roi_neto = (diff * 100 * palanca) - comision
            
            # Cierre rápido 0.5% Neto o Protección -0.7%
            if roi_neto >= ganancia_neta_ale or roi_neto <= -0.7:
                res = (capital_base * (roi_neto / 100))
                registrar("CIERRE", f"{tipo_op} ROI: {roi_neto:.2f}%", res)
                en_operacion = False
                print(f"🎯 COBRADO: {roi_neto:.2f}%")

        time.sleep(espera_segundos)

    except Exception as e:
        print(f"⚠️ Error evitado: {e}")
        time.sleep(10) # Espera un poco más si hay error para no saturar
