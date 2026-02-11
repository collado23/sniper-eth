import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === PARÁMETROS ===
espera_segundos = 14
palanca = 10
ganancia_neta_ale = 0.50 
comision = 0.20
archivo_memoria = "memoria_quantum.txt"

# === ESTADO DEL BÚNKER (ESTO NO SE BORRA) ===
capital_base = 30.00
ganancia_acumulada = 0.0  # <--- AQUÍ SE GUARDA TODO LO GANADO
perdida_acumulada = 0.0   # <--- AQUÍ SE GUARDA TODO LO PERDIDO
contador_ops = 0
en_operacion = False

def registrar_y_sumar(tipo, msg, valor=0):
    global contador_ops, ganancia_acumulada, perdida_acumulada
    ts = datetime.now().strftime('%H:%M:%S')
    
    # Escribir en el TXT
    try:
        with open(archivo_memoria, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {tipo} | {msg} | VALOR: ${valor:.4f}\n")
    except: pass

    # Actualizar contadores reales
    if tipo == "CIERRE":
        contador_ops += 1
        if valor > 0:
            ganancia_acumulada += valor
        else:
            perdida_acumulada += abs(valor)

print("🚀 AMETRALLADORA ACTIVADA - CONTADORES REINICIADOS PARA EL CICLO")

while True:
    try:
        # 1. DATOS EN TIEMPO REAL
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        p_sol = float(ticker['price'])
        
        # Velas para el patrón
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=3)
        v_actual_open = float(klines[-1][1])
        v_anterior_close = float(klines[-2][4])
        
        # CÁLCULO DEL NETO REAL
        neto_total = ganancia_acumulada - perdida_acumulada

        # --- TABLERO INTEGRAL (Lo que pediste ver) ---
        print("\n" + "═"*55)
        print(f"🔱 ALE IA QUANTUM | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💎 PRECIO SOL: ${p_sol:.2f}")
        print(f"💰 CAP. ACTUAL: ${capital_base + neto_total:.2f}")
        print(f"📈 NETO TOTAL: ${neto_total:.2f}") # <--- TU BALANCE REAL
        print(f"✅ GANADO: +${ganancia_acumulada:.2f} | ❌ PERDIDO: -${perdida_acumulada:.2f}")
        print(f"🔢 OPS: {contador_ops}/20 para el ANÁLISIS UNO")
        print("═"*55)

        if not en_operacion:
            # Lógica de entrada por velas
            if p_sol > v_actual_open and p_sol > v_anterior_close:
                en_operacion = True
                p_entrada = p_sol
                tipo_op = "LONG 🟢"
                registrar_y_sumar("ENTRADA", f"LONG en ${p_sol}")
            elif p_sol < v_actual_open and p_sol < v_anterior_close:
                en_operacion = True
                p_entrada = p_sol
                tipo_op = "SHORT 🔴"
                registrar_y_sumar("ENTRADA", f"SHORT en ${p_sol}")
        
        else:
            # Lógica de salida: 0.5% NETO
            diff = ((p_sol - p_entrada) / p_entrada) if "LONG" in tipo_op else ((p_entrada - p_sol) / p_entrada)
            roi_neto = (diff * 100 * palanca) - comision
            
            if roi_neto >= ganancia_neta_ale or roi_neto <= -0.7:
                resultado_dolares = (capital_base * (roi_neto / 100))
                registrar_y_sumar("CIERRE", f"{tipo_op} finalizado", resultado_dolares)
                en_operacion = False

        time.sleep(espera_segundos)

    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(10)
