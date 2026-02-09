import os, time, pandas as pd
import numpy as np
from binance.client import Client

# --- CONEXIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol = "SOLUSDT"
leverage = 10
cantidad_prueba = 0.1  # MÍNIMO PARA PRUEBAS
archivo_memoria = "memoria_gladiador.txt"
precio_extremo = None

def guardar_en_memoria(mensaje):
    with open(archivo_memoria, "a") as f:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {mensaje}\n")
    print(f"📝 MEMORIA: {mensaje}")

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

def ejecutar_gladiador_con_memoria():
    global precio_extremo
    print(f"🔱 GLADIADOR CON MEMORIA ACTIVADO | {symbol}")
    
    while True:
        try:
            klines = client.futures_klines(symbol=symbol, interval='1m', limit=200)
            df = pd.DataFrame(klines, columns=['time','open','high','low','close','vol','ct','q','n','tb','tq','i'])
            df[['high','low','close']] = df[['high','low','close']].astype(float)
            
            precio = df['close'].iloc[-1]
            ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            adx_val = calcular_adx(df)
            
            distancia_200 = abs(precio - ema_200) / ema_200 * 100
            pos = client.futures_position_information(symbol=symbol)
            datos_pos = next((p for p in pos if p['symbol'] == symbol), None)
            amt = float(datos_pos['positionAmt']) if datos_pos else 0

            # --- DETECCIÓN DE AGOTAMIENTO PARA LA MEMORIA ---
            if distancia_200 > 1.8: # Si se aleja mucho de la EMA 200 (la violeta)
                guardar_en_memoria(f"Nivel de agotamiento detectado en {precio}. Posible zigzag.")

            # --- LÓGICA DE ENTRADA ---
            if amt == 0:
                precio_extremo = None
                # No entramos si estamos en zona de agotamiento extremo para evitar el piso sucio
                if adx_val > 30 and distancia_200 < 1.8:
                    if precio > (ema_20 * 1.002):
                        client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=cantidad_prueba)
                        print(f"🚀 ENTRADA LONG")
                    elif precio < (ema_20 * 0.998):
                        client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=cantidad_prueba)
                        print(f"📉 ENTRADA SHORT")

            # --- CIERRE INVISIBLE (TRAILING MENTAL) ---
            elif amt != 0:
                if precio_extremo is None: precio_extremo = precio
                
                if amt < 0: # SHORT
                    if precio < precio_extremo: precio_extremo = precio
                    rebote = (precio - precio_extremo) / precio_extremo * 100
                    if rebote > 0.3 or precio > (ema_20 * 1.001):
                        client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=abs(amt))
                        guardar_en_memoria(f"CIERRE SHORT en {precio} por rebote de {rebote:.2f}%")
                
                elif amt > 0: # LONG
                    if precio > precio_extremo: precio_extremo = precio
                    caida = (precio_extremo - precio) / precio_extremo * 100
                    if caida > 0.3 or precio < (ema_20 * 0.999):
                        client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=abs(amt))
                        guardar_en_memoria(f"CIERRE LONG en {precio} por caída de {caida:.2f}%")

            print(f"📊 {precio:.2f} | ADX: {adx_val:.1f} | Dist200: {distancia_200:.2f}%")
            time.sleep(10)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    ejecutar_gladiador_con_memoria()
