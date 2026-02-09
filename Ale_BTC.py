import os, time, pandas as pd, numpy as np
from binance.client import Client

# --- CONFIGURACIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol_sol = "SOLUSDT"
symbol_btc = "BTCUSDT"
cantidad_prueba = 0.1  # Cantidad de prueba sugerida
archivo_memoria = "memoria_gladiador.txt"

# --- LÍMITES HISTÓRICOS (Inyectados de data externa) ---
LIMITE_SOL = 2.45 
LIMITE_BTC = 1.35 

def guardar_en_memoria(sol_p, dist_s, pnl, motivo):
    with open(archivo_memoria, "a") as f:
        log = (f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
               f"SOL: {sol_p:.2f} | Dist: {dist_s:.2f}% | "
               f"ROI: {pnl:.2f}% | MOTIVO: {motivo}\n")
        f.write(log)
    print(f"📝 Registro: {motivo} | ROI: {pnl:.2f}%")

def ejecutar_gladiador_v7_5():
    print(f"🔱 GLADIADOR V7.5 ACTIVADO - MODO OPERATIVO")
    posicion_abierta = False
    precio_entrada = 0
    tipo_operacion = None # 'LONG' o 'SHORT'

    while True:
        try:
            # 1. Obtener datos (Respetando límites de API)
            k_sol = client.futures_klines(symbol=symbol_sol, interval='1m', limit=100)
            k_btc = client.futures_klines(symbol=symbol_btc, interval='1m', limit=100)
            
            p_sol = float(k_sol[-1][4])
            p_btc = float(k_btc[-1][4])
            
            # Cálculos de EMA 200
            df_s = pd.DataFrame(k_sol)[4].astype(float)
            df_b = pd.DataFrame(k_btc)[4].astype(float)
            ema_s = df_s.ewm(span=200, adjust=False).mean().iloc[-1]
            ema_b = df_b.ewm(span=200, adjust=False).mean().iloc[-1]
            
            dist_s = ((p_sol - ema_s) / ema_s) * 100
            dist_b = ((p_btc - ema_b) / ema_b) * 100

            # 2. Revisar posición real en Binance
            pos = client.futures_position_information(symbol=symbol_sol)
            datos_pos = next((p for p in pos if p['symbol'] == symbol_sol), None)
            amt = float(datos_pos['positionAmt']) if datos_pos else 0

            # --- LÓGICA DE ENTRADA (SOL + BTC ACOPLADOS) ---
            if amt == 0:
                # SHORT: SOL estirado arriba Y BTC estirado arriba
                if dist_s > LIMITE_SOL and dist_b > (LIMITE_BTC * 0.8):
                    client.futures_create_order(symbol=symbol_sol, side='SELL', type='MARKET', quantity=cantidad_prueba)
                    guardar_en_memoria(p_sol, dist_s, 0, "📉 ENTRADA SHORT (Elástico Máximo)")
                
                # LONG: SOL estirado abajo Y BTC estirado abajo
                elif dist_s < -LIMITE_SOL and dist_b < -(LIMITE_BTC * 0.8):
                    client.futures_create_order(symbol=symbol_sol, side='BUY', type='MARKET', quantity=cantidad_prueba)
                    guardar_en_memoria(p_sol, dist_s, 0, "🚀 ENTRADA LONG (Elástico Máximo)")

            # --- LÓGICA DE CIERRE (RETORNO A LA MEDIA) ---
            else:
                precio_entrada = float(datos_pos['entryPrice'])
                pnl = ((p_sol - precio_entrada) / precio_entrada * 100) if amt > 0 else ((precio_entrada - p_sol) / precio_entrada * 100)
                
                # Cierre por retorno a la EMA (el elástico vuelve a su sitio)
                # O cierre por seguridad si el ROI es positivo y empieza a retroceder
                deberia_cerrar = False
                if amt > 0 and dist_s > -0.10: deberia_cerrar = True # Volvió a la EMA en Long
                if amt < 0 and dist_s < 0.10: deberia_cerrar = True  # Volvió a la EMA en Short

                if deberia_cerrar:
                    client.futures_create_order(symbol=symbol_sol, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                    guardar_en_memoria(p_sol, dist_s, pnl, "🎯 CIERRE: Regreso a la EMA 200")

            print(f"📊 SOL: {p_sol:.2f} ({dist_s:.2f}%) | BTC: {dist_b:.2f}% | ROI: {pnl if amt != 0 else 0:.2f}%")
            time.sleep(20)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    ejecutar_gladiador_v7_5()
