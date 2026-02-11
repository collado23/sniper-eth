import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === MEMORIA HISTÓRICA DE AYER Y HOY ===
archivo_memoria = "memoria_quantum.txt"
cap_inicial = 30.00
ganado = 47.12   
perdido = 67.27  
ops_totales = 398 # Empezamos desde donde te quedaste en la foto
en_op = False

def guardar_historial(tipo, msg, valor=0):
    global ops_totales, ganado, perdido
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    linea = f"{ts} | {tipo:10} | {msg} | NETO: ${valor:.4f}\n"
    
    try:
        with open(archivo_memoria, "a", encoding="utf-8") as f:
            f.write(linea)
            f.flush()
            os.fsync(f.fileno())
    except: pass

    if tipo == "CIERRE":
        ops_totales += 1
        if valor > 0: ganado += valor
        else: perdido += abs(valor)

print(f"🚀 INICIANDO CARRERA HACIA LAS 1000 OPERACIONES (MODO INVERTIDO)")

while ops_totales < 1000:
    try:
        # Escaneo ultra-rápido de SOL
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=5)
        
        # Filtros mínimos para que dispare constante
        v_actual_open = float(klines[-1][1])
        v_color = "VERDE 🟢" if sol > v_actual_open else "ROJA 🔴"
        neto = ganado - perdido

        # --- TABLERO PARA FOTO (Celular) ---
        print("\n" + "═"*45)
        print(f"🔱 IA QUANTUM | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 NETO: ${neto:.2f} | CAP: ${cap_inicial + neto:.2f}")
        print(f"🔢 AVANCE: {ops_totales} / 1000 OPS")
        print(f"🕯️ VELA: {v_color} | 📈 SOL: ${sol:.2f}")
        print(f"⚠️ MODO: INVERTIDO (Contra-Tendencia)")
        print("═"*45)

        if not en_op:
            # GATILLO INVERTIDO: Entra casi siempre para llegar a las 1000
            p_ent = sol
            en_op = True
            if sol > v_actual_open:
                t_op = "SHORT 🔴" # Vela verde -> Venta
                guardar_historial("VENTA", f"SHORT INVERTIDO ${sol}")
            else:
                t_op = "LONG 🟢"  # Vela roja -> Compra
                guardar_historial("COMPRA", f"LONG INVERTIDO ${sol}")
        
        else:
            # Salida rápida para rotar operaciones (0.3% neto para dar velocidad)
            diff = ((sol - p_ent) / p_ent) if "LONG" in t_op else ((p_ent - sol) / p_ent)
            roi = (diff * 100 * 10) - 0.20 # Palanca x10 y comisión
            
            # Cierre rápido para acumular volumen de operaciones
            if roi >= 0.30 or roi <= -0.40:
                res = (9.85 * (roi / 100))
                guardar_historial("CIERRE", f"{t_op} Fin ROI: {roi:.2f}%", res)
                en_op = False
                print(f"🎯 Op {ops_totales} cerrada. Resultado: {roi:.2f}%")

        time.sleep(10) # 10 segundos para máxima velocidad
    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(5)

print("🏁 OBJETIVO DE 1000 OPERACIONES ALCANZADO")
