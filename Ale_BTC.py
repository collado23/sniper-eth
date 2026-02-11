import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === MEMORIA REAL (Actualizada a tu última foto) ===
archivo_memoria = "memoria_quantum.txt"
cap_inicial = 30.00
ganado_plata = 47.37   
perdido_plata = 67.66  
ops_ganadas = 189      
ops_perdidas = 217     
ops_totales = ops_ganadas + ops_perdidas
en_op = False

def guardar_historial(tipo, msg, valor=0):
    global ops_totales, ganado_plata, perdido_plata, ops_ganadas, ops_perdidas
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    linea = f"{ts} | {tipo:10} | {msg} | VAL: ${valor:.4f} | OPS: {ops_totales}\n"
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

print(f"🚀 MODO SNIPER: 2 VELAS + ELASTICIDAD ACTIVADO")

while ops_totales < 1000:
    try:
        # 1. ANÁLISIS DE LAS ÚLTIMAS 2 VELAS
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=5)
        
        # Color de las últimas 2 velas cerradas
        def get_color(k): return "VERDE 🟢" if float(k[4]) > float(k[1]) else "ROJA 🔴"
        v1 = get_color(klines[-2]) # La que acaba de cerrar
        v2 = get_color(klines[-3]) # La anterior
        
        # Elasticidad (Media de 20 períodos)
        klines_ema = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=20)
        cierres = [float(k[4]) for k in klines_ema]
        ema = sum(cierres) / 20
        elasticidad = abs(((ema - sol) / sol) * 100)
        
        neto = ganado_plata - perdido_plata

        # --- 📊 TABLERO PARA FOTO CELULAR ---
        print("\n" + "═"*50)
        print(f"🔱 ALE IA QUANTUM | {datetime.now().strftime('%H:%M:%S')}")
        print(f"🔢 OPS: {ops_totales} / 1000 | 💰 NETO: ${neto:.2f}")
        print(f"✅ G: {ops_ganadas} (+${ganado_plata:.2f})")
        print(f"❌ P: {ops_perdidas} (-${perdido_plata:.2f})")
        print("-" * 50)
        print(f"🕯️ RACHA 2V: [{v2}] -> [{v1}]") 
        print(f"📏 ELASTICIDAD: {elasticidad:.3f}% | 📈 SOL: ${sol:.2f}")
        
        if en_op:
            diff = ((sol - p_ent) / p_ent) if "LONG" in t_op else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.20
            if roi_neto > max_roi: max_roi = roi_neto
            print(f"🏃 {t_op} | ROI NETO: {roi_neto:.2f}% | PISO: {max_roi - 0.10:.2f}%")
        print("═"*50)

        # 2. GATILLO: SI LAS 2 SON IGUALES + ELASTICIDAD
        if not en_op:
            if v1 == v2 and elasticidad >= 0.045:
                p_ent = sol
                en_op = True
                max_roi = -99.0
                # Lógica Invertida (Espejo)
                if "VERDE" in v1:
                    t_op = "SHORT 🔴"
                    guardar_historial("VENTA", f"SHORT 2V en ${sol}")
                else:
                    t_op = "LONG 🟢"
                    guardar_historial("COMPRA", f"LONG 2V en ${sol}")
        
        else:
            # 3. CIERRE POR TRAILING (Asegura el centavo neto)
            if max_roi >= 0.35:
                if roi_neto <= (max_roi - 0.10):
                    res = (9.85 * (roi_neto / 100)) # Operando sobre capital real
                    guardar_historial("CIERRE", f"{t_op} TRAIL", res)
                    en_op = False
            elif roi_neto <= -0.70:
                res = (9.85 * (roi_neto / 100))
                guardar_historial("CIERRE", f"{t_op} STOP", res)
                en_op = False

        time.sleep(15)
    except Exception as e:
        time.sleep(10)
