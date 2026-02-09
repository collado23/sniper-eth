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

# --- PARÁMETROS FÍSICOS (De la data de 4 años) ---
LIMITE_SOL = 2.45  # Distancia crítica para Solana
LIMITE_BTC = 1.35  # Distancia crítica para Bitcoin

def guardar_en_memoria(precio, dist, pnl, motivo, adx):
    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
    log = (f"[{fecha}] SOL: {precio:.2f} | Dist: {dist:.2f}% | "
           f"ADX: {adx:.1f} | ROI: {pnl:.2f}% | MOTIVO: {motivo}\n")
    with open(archivo_memoria, "a") as f:
        f.write(log)
    print(f"📝 {motivo} | ROI: {pnl:.2f}%")

def calcular_adx(df, period=14):
    df = df.copy()
    df['h-l'] = df['high'] - df['low']
    df['h-pc'] = abs(df['high'] - df['close'].shift(1))
    df['l-pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
    df['up'] = df['high'] - df['high'].shift(1)
    df['dn'] = df['low'].shift(1) - df['low']
    df['+dm'] = np.where((df['up'] > df['dn']) & (df['up'] > 0), df['up'], 0)
    df['-dm'] = np.where((df['dn'] > df['up']) & (df['dn'] > 0), df['dn'], 0)
    tr_smooth = df['tr'].rolling(window=period).sum()
    dm_plus_smooth = df['+dm'].rolling(window=period).sum()
    dm_minus_smooth = df['-dm'].rolling(window=period).sum()
    df['+di'] = 100 * (dm_plus_smooth / tr_smooth)
    df['-di'] = 100 * (dm_minus_smooth / tr_smooth)
    df['dx'] = 100 * abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])
    return df['dx'].rolling(window=period).mean().iloc[-1]

def ejecutar_gladiador_total():
    print(f"🔱 GLADIADOR V7.5: INICIANDO OPERACIONES DE PRUEBA")
    precio_maximo = 0

    while True:
        try:
            # 1. Obtención de Datos de SOL y BTC
            k_sol = client.futures_klines(symbol=symbol_sol, interval='1m', limit=100)
            k_btc = client.futures_klines(symbol=symbol_btc, interval='1m', limit=100)
            
            df_s = pd.DataFrame(k_sol, columns=['t','open','high','low','close','v','ct','q','n','tb','tq','i'])
            df_b = pd.DataFrame(k_btc, columns=['t','open','high','low','close','v','ct','q','n','tb','tq','i'])
            df_s[['open','high','low','close']] = df_s[['open','high','low','close']].astype(float)
            df_b['close'] = df_b['close'].astype(float)

            # 2. Variables de Física y Análisis
            p_sol = df_s['close'].iloc[-1]
            p_btc = df_b['close'].iloc[-1]
            ema_s = df_s['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            ema_b = df_b['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            
            dist_s = ((p_sol - ema_s) / ema_s) * 100
            dist_b = ((p_btc - ema_b) / ema_b) * 100
            adx_val = calcular_adx(df_s)

            # Análisis de Vela Japonesa (Giro)
            v = df_s.iloc[-1]
            es_roja = v['close'] < v['open']
            es_verde = v['close'] > v['open']
            mecha_sup = v['high'] - max(v['open'], v['close'])
            mecha_inf = min(v['open'], v['close']) - v['low']
            cuerpo = abs(v['close'] - v['open'])

            # 3. Estado de Posición
            pos = client.futures_position_information(symbol=symbol_sol)
            datos_pos = next((p for p in pos if p['symbol'] == symbol_sol), None)
            amt = float(datos_pos['positionAmt']) if datos_pos else 0
            pnl = 0

            # --- LÓGICA DE ENTRADA (Reflejo + Física + Vela) ---
            if amt == 0:
                precio_maximo = 0
                # SHORT: SOL estirado + BTC confirma + Vela de giro roja
                if dist_s > LIMITE_SOL and dist_b > (LIMITE_BTC * 0.7) and es_roja and mecha_sup > cuerpo:
                    client.futures_create_order(symbol=symbol_sol, side='SELL', type='MARKET', quantity=cantidad_prueba)
                    guardar_en_memoria(p_sol, dist_s, 0, "📉 ENTRADA SHORT (Giro Cuántico)", adx_val)
                
                # LONG: SOL estirado abajo + BTC confirma + Vela de giro verde
                elif dist_s < -LIMITE_SOL and dist_b < -(LIMITE_BTC * 0.7) and es_verde and mecha_inf > cuerpo:
                    client.futures_create_order(symbol=symbol_sol, side='BUY', type='MARKET', quantity=cantidad_prueba)
                    guardar_en_memoria(p_sol, dist_s, 0, "🚀 ENTRADA LONG (Giro Cuántico)", adx_val)

            # --- LÓGICA DE CIERRE (ROI + Trailing) ---
            else:
                entrada = float(datos_pos['entryPrice'])
                pnl = ((p_sol - entrada) / entrada * 100) if amt > 0 else ((entrada - p_sol) / entrada * 100)
                
                # Seguimiento del mejor precio para el Trailing
                if precio_maximo == 0 or (amt > 0 and p_sol > precio_maximo) or (amt < 0 and p_sol < precio_maximo):
                    precio_maximo = p_sol
                
                # Retroceso desde el pico
                retroceso = abs((precio_maximo - p_sol) / precio_maximo * 100)

                # CIERRE: Si vuelve a la EMA 200 o si el ROI cae 0.3% desde su máximo
                if abs(dist_s) < 0.15 or (pnl > 0.4 and retroceso > 0.3):
                    client.futures_create_order(symbol=symbol_sol, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                    guardar_en_memoria(p_sol, dist_s, pnl, "🎯 CIERRE: Objetivo cumplido", adx_val)

            print(f"📊 SOL: {p_sol:.2f} ({dist_s:.2f}%) | BTC: {dist_b:.2f}% | ROI: {pnl:.2f}%")
            time.sleep(20) # Respiro de seguridad para la API

        except Exception as e:
            print(f"⚠️ Alerta: {e}"); time.sleep(30)

if __name__ == "__main__":
    ejecutar_gladiador_total()
