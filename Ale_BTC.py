import os, time, pandas as pd, numpy as np
from binance.client import Client

# --- CONFIGURACIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol = "SOLUSDT"
cantidad_prueba = 0.1  
archivo_memoria = "memoria_gladiador.txt"

# --- VARIABLES DE SEGUIMIENTO ---
precio_maximo_alcanzado = 0
posicion_abierta = False

def guardar_en_memoria(precio, dist, adx, pnl, motivo):
    try:
        with open(archivo_memoria, "a") as f:
            log = (f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                   f"P: {precio:.2f} | Dist_EMA: {dist:.2f}% | ADX: {adx:.1f} | "
                   f"ROI: {pnl:.2f}% | MOTIVO: {motivo}\n")
            f.write(log)
        print(f"📝 {motivo} | ROI: {pnl:.2f}% | Dist: {dist:.2f}%")
    except Exception as e:
        print(f"❌ Error al escribir en TXT: {e}")

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

def ejecutar_gladiador_v6_3():
    global precio_maximo_alcanzado, posicion_abierta
    print(f"🔱 GLADIADOR V6.3: MODO ARCHIVISTA Y ELÁSTICO ACTIVADO")
    
    while True:
        try:
            klines = client.futures_klines(symbol=symbol, interval='1m', limit=100)
            df = pd.DataFrame(klines, columns=['t','open','high','low','close','v','ct','q','n','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            
            v = df.iloc[-1]
            precio = v['close']
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            adx_val = calcular_adx(df)
            dist_pct = ((precio - ema_200) / ema_200) * 100
            
            es_roja = v['close'] < v['open']
            es_verde = v['close'] > v['open']
            mecha_sup = v['high'] - max(v['open'], v['close'])
            mecha_inf = min(v['open'], v['close']) - v['low']
            cuerpo = abs(v['close'] - v['open'])

            pos = client.futures_position_information(symbol=symbol)
            datos_pos = next((p for p in pos if p['symbol'] == symbol), None)
            amt = float(datos_pos['positionAmt']) if datos_pos else 0
            pnl = 0

            # --- LÓGICA DE ENTRADA ---
            if amt == 0:
                posicion_abierta = False
                precio_maximo_alcanzado = 0
                
                # SHORT: Arriba (+1.80%) + Vela Roja con mecha + ADX alto
                if dist_pct > 1.80 and es_roja and mecha_sup > cuerpo:
                    client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=cantidad_prueba)
                    guardar_en_memoria(precio, dist_pct, adx_val, 0, "📉 ENTRADA SHORT (Elástico + Vela)")

                # LONG: Abajo (-1.80%) + Vela Verde con mecha + ADX alto
                elif dist_pct < -1.80 and es_verde and mecha_inf > cuerpo:
                    client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=cantidad_prueba)
                    guardar_en_memoria(precio, dist_pct, adx_val, 0, "🚀 ENTRADA LONG (Elástico + Vela)")

            # --- LÓGICA DE SEGUIMIENTO Y CIERRE ---
            elif amt != 0:
                if not posicion_abierta:
                    posicion_abierta = True
                    precio_maximo_alcanzado = precio
                
                entrada = float(datos_pos['entryPrice'])
                pnl = ((precio - entrada) / entrada * 100) if amt > 0 else ((entrada - precio) / entrada * 100)
                
                if amt > 0: # En Long
                    if precio > precio_maximo_alcanzado: precio_maximo_alcanzado = precio
                    retroceso = (precio_maximo_alcanzado - precio) / precio_maximo_alcanzado * 100
                    # Cierre por objetivo de elástico o por vuelta de precio ganando
                    if dist_pct > 1.80 or (pnl > 0.4 and retroceso > 0.25):
                        client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=abs(amt))
                        guardar_en_memoria(precio, dist_pct, adx_val, pnl, "🎯 CIERRE LONG (Objetivo/Vuelta)")
                
                else: # En Short
                    if precio < precio_maximo_alcanzado: precio_maximo_alcanzado = precio
                    retroceso = (precio - precio_maximo_alcanzado) / precio_maximo_alcanzado * 100
                    if dist_pct < -1.80 or (pnl > 0.4 and retroceso > 0.25):
                        client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=abs(amt))
                        guardar_en_memoria(precio, dist_pct, adx_val, pnl, "🎯 CIERRE SHORT (Objetivo/Vuelta)")

            print(f"📊 SOL: {precio:.2f} | Dist: {dist_pct:.2f}% | ADX: {adx_val:.1f} | ROI: {pnl:.2f}%")
            time.sleep(15) 

        except Exception as e:
            print(f"⚠️ Alerta: {e}"); time.sleep(30)

if __name__ == "__main__":
    ejecutar_gladiador_v6_3()
