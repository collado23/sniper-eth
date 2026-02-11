import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === MEMORIA DE CAJA 1 (Tus datos acumulados) ===
archivo_memoria = "memoria_quantum.txt"
cap_inicial = 30.00
ganado_plata = 47.12   
perdido_plata = 67.27  
ops_ganadas = 185  
ops_perdidas = 213 
ops_totales = ops_ganadas + ops_perdidas
en_op = False

# === PARÁMETROS DE PRECISIÓN (0.1 CENTAVO NETO) ===
palanca = 10
comision_total = 0.20 # 0.1% entrada + 0.1% salida
# Meta: cubrimos comisión + ganancia mínima de centavo
meta_activacion_trailing = 0.35 # % de ROI para que ya estemos en verde neto
trail_distancia = 0.10          # Qué tanto lo sigue de cerca (ajustado para celular)

def guardar_historial(tipo, msg, valor=0):
    global ops_totales, ganado_plata, perdido_plata, ops_ganadas, ops_perdidas
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    linea = f"{ts} | {tipo:10} | {msg} | NETO: ${valor:.4f} | OPS: {ops_totales}\n"
    try:
        with open(archivo_memoria, "a", encoding="utf-8") as f:
            f.write(linea)
            f.flush()
    except: pass
    if tipo == "CIERRE":
        ops_totales += 1
        if valor > 0:
            ganado_plata += valor
            ops_ganadas += 1
        else:
            perdido_plata += abs(valor)
            ops_perdidas += 1

print(f"🚀 AMETRALLADORA 1000 OPS - TRAILING DINÁMICO ACTIVADO")

while ops_totales < 1000:
    try:
        # 1. ANÁLISIS RÁPIDO (SIN ADX - SOLO ELÁSTICO Y VELAS)
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=10)
        
        cierres = [float(k[4]) for k in klines]
        ema = sum(cierres) / len(cierres)
        elasticidad = abs(((ema - sol) / sol) * 100)
        v_actual_open = float(klines[-1][1])
        v_color = "VERDE 🟢" if sol > v_actual_open else "ROJA 🔴"
        
        neto_plata = ganado_plata - perdido_plata

        # --- 📊 TABLERO PARA FOTO CELULAR ---
        print("\n" + "═"*50)
        print(f"🔱 ALE IA QUANTUM | {datetime.now().strftime('%H:%M:%S')}")
        print(f"🔢 AVANCE: {ops_totales} / 1000 OPS")
        print(f"✅ G: {ops_ganadas} (+${ganado_plata:.2f}) | ❌ P: {ops_perdidas} (-${perdido_plata:.2f})")
        print(f"💰 NETO CAJA 1: ${neto_plata:.2f}")
        print("-" * 50)
        print(f"📏 ELASTICIDAD: {elasticidad:.3f}% | 📈 SOL: ${sol:.2f}")
        
        if en_op:
            diff = ((sol - p_ent) / p_ent) if "LONG" in t_op else ((p_ent - sol) / p_ent)
            roi_bruto = (diff * 100 * palanca)
            roi_neto = roi_bruto - comision_total
            
            if roi_neto > max_roi: max_roi = roi_neto
            
            print(f"🏃 {t_op} | ROI NETO: {roi_neto:.2f}%")
            print(f"🎯 TRAILING: MAX {max_roi:.2f}% | PISO {max_roi - trail_distancia:.2f}%")
        print("═"*50)

        # 2. GATILLO INVERTIDO (Ametralladora)
        if not en_op:
            if elasticidad >= 0.03: # Filtro bajo para que entre constante
                p_ent = sol
                en_op = True
                max_roi = -99.0
                if sol > v_actual_open:
                    t_op = "SHORT 🔴"
                    guardar_historial("VENTA", f"SHORT INV ${sol}")
                else:
                    t_op = "LONG 🟢"
                    guardar_historial("COMPRA", f"LONG INV ${sol}")
        
        else:
            # 3. CIERRE POR TRAILING DINÁMICO (Asegura el centavo)
            # Si ya estamos por encima de la meta (comisión cubierta + 1 centavo)
            if max_roi >= meta_activacion_trailing:
                # Si el precio retrocede desde el máximo alcanzado, cobramos
                if roi_neto <= (max_roi - trail_distancia):
                    res = (9.85 * (roi_neto / 100)) # Basado en lo que queda
                    guardar_historial("CIERRE", f"{t_op} TRAILING EXIT", res)
                    en_op = False
                    print(f"💰 COBRADO POR TRAILING: {roi_neto:.2f}%")
            
            # Stop Loss de seguridad (por si se va muy en contra)
            elif roi_neto <= -0.70:
                res = (9.85 * (roi_neto / 100))
                guardar_historial("CIERRE", f"{t_op} STOP LOSS", res)
                en_op = False

        time.sleep(12)
    except Exception as e:
        time.sleep(10)
