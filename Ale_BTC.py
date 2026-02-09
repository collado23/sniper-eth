import os, time, pandas as pd, numpy as np
from binance.client import Client

# --- CONFIGURACIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol_sol = "SOLUSDT"
symbol_btc = "BTCUSDT"
cantidad_prueba = 0.1  
archivo_memoria = "memoria_gladiador.txt"

# --- ESTADÍSTICAS DE SESIÓN ---
ganancia_total_porcentaje = 0.0
contador_operaciones = 0

# --- INTELIGENCIA DE 4 AÑOS (Yahoo Finanzas) ---
LIMITE_HISTORICO_SOL = 2.45  
LIMITE_HISTORICO_BTC = 1.35  

def guardar_log(precio, dist, pnl, motivo, btc_dist):
    global ganancia_total_porcentaje, contador_operaciones
    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Si es un cierre, actualizamos estadísticas
    if "CIERRE" in motivo:
        ganancia_total_porcentaje += pnl
        contador_operaciones += 1
    
    promedio = ganancia_total_porcentaje / contador_operaciones if contador_operaciones > 0 else 0
    
    log = (f"[{fecha}] SOL: {precio:.2f} | PNL: {pnl:.2f}% | "
           f"TOTAL ACUMULADO: {ganancia_total_porcentaje:.2f}% | PROMEDIO: {promedio:.2f}% | {motivo}\n")
    
    with open(archivo_memoria, "a") as f:
        f.write(log)

def ejecutar_v8_3():
    print(f"🔱 GLADIADOR V8.3: MONITOR DE GANANCIAS ACUMULADAS")
    
    while True:
        try:
            # 1. Datos actuales
            k_s = client.futures_klines(symbol=symbol_sol, interval='1m', limit=100)
            k_b = client.futures_klines(symbol=symbol_btc, interval='1m', limit=100)
            df_s = pd.DataFrame(k_s).astype(float)
            df_b = pd.DataFrame(k_b).astype(float)
            
            p_s = df_s[4].iloc[-1]
            ema_s = df_s[4].ewm(span=200, adjust=False).mean().iloc[-1]
            dist_s = ((p_s - ema_s) / ema_s) * 100
            dist_b = ((df_b[4].iloc[-1] - df_b[4].ewm(span=200, adjust=False).mean().iloc[-1]) / df_b[4].ewm(span=200, adjust=False).mean().iloc[-1]) * 100

            # 2. Revisar posición
            pos = client.futures_position_information(symbol=symbol_sol)
            datos_pos = next((p for p in pos if p['symbol'] == symbol_sol), None)
            amt = float(datos_pos['positionAmt']) if datos_pos else 0
            
            pnl_actual = 0.0
            status = "BUSCANDO ENTRADA"

            if amt != 0:
                ent = float(datos_pos['entryPrice'])
                pnl_actual = ((p_s - ent) / ent * 100) if amt > 0 else ((ent - p_s) / ent * 100)
                status = "🟢 OPERANDO"
                
                # CIERRE AUTOMÁTICO
                if abs(dist_s) < 0.15 or pnl_actual < -1.2:
                    client.futures_create_order(symbol=symbol_sol, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                    guardar_log(p_s, dist_s, pnl_actual, "🎯 CIERRE", dist_b)
            else:
                # ENTRADA
                if abs(dist_s) >= LIMITE_HISTORICO_SOL and abs(dist_b) >= (LIMITE_HISTORICO_BTC * 0.8):
                    side = 'SELL' if dist_s > 0 else 'BUY'
                    client.futures_create_order(symbol=symbol_sol, side=side, type='MARKET', quantity=cantidad_prueba)
                    guardar_log(p_s, dist_s, 0, f"🚀 ENTRADA {side}", dist_b)

            # --- LA PANTALLITA DE ESTADÍSTICAS ---
            promedio_sesion = ganancia_total_porcentaje / contador_operaciones if contador_operaciones > 0 else 0
            
            print(f"==================================================")
            print(f"💰 SESIÓN: {ganancia_total_porcentaje:+.2f}% | PROMEDIO/TRADE: {promedio_sesion:+.2f}%")
            print(f"📊 {status} | ROI ACTUAL: {pnl_actual:+.2f}%")
            print(f"📈 SOL: {p_s:.2f} ({dist_s:+.2f}%) | BTC Dist: {dist_b:+.2f}%")
            print(f"🔢 Operaciones Cerradas: {contador_operaciones}")
            print(f"==================================================")
            
            time.sleep(20)

        except Exception as e:
            print(f"⚠️ Error: {e}"); time.sleep(30)

if __name__ == "__main__":
    ejecutar_v8_3()
