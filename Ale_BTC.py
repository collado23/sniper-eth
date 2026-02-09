import os, time, pandas as pd
import numpy as np
from binance.client import Client

# --- CONEXIÓN Y CONFIGURACIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol = "SOLUSDT"
leverage = 10
cantidad_prueba = 0.5 # Media moneda de SOL para testear sin riesgo

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

def ejecutar_gladiador_protector():
    print(f"🔱 GLADIADOR SOL: MODO SUPER-PROTECCIÓN ACTIVADO (0.3% MARGEN)")
    
    while True:
        try:
            klines = client.futures_klines(symbol=symbol, interval='1m', limit=100)
            df = pd.DataFrame(klines, columns=['time','open','high','low','close','vol','ct','q','n','tb','tq','i'])
            df[['high','low','close']] = df[['high','low','close']].astype(float)
            
            precio = df['close'].iloc[-1]
            ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
            adx_val = calcular_adx(df)
            
            pos = client.futures_position_information(symbol=symbol)
            datos_pos = next((p for p in pos if p['symbol'] == symbol), None)
            amt = float(datos_pos['positionAmt']) if datos_pos else 0

            # --- PARÁMETROS DE BLINDAJE ---
            margen = 0.003 # 0.3% para ignorar el serrucho
            adx_fuerte = 35 # Solo entra si hay mucha fuerza
            adx_muerto = 25 # Cierra si la fuerza desaparece

            # 1. ENTRADA (Solo si estamos fuera)
            if amt == 0:
                if adx_val > adx_fuerte:
                    if precio > (ema_20 * (1 + margen)):
                        client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=cantidad_prueba)
                        print(f"🚀 ENTRADA LONG SEGURA | ADX: {adx_val:.1f}")
                    elif precio < (ema_20 * (1 - margen)):
                        client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=cantidad_prueba)
                        print(f"📉 ENTRADA SHORT SEGURA | ADX: {adx_val:.1f}")

            # 2. SALIDA DE SHORT
            elif amt < 0:
                if precio > (ema_20 * (1 + margen)) or adx_val < adx_muerto:
                    razon = "Giro fuerte" if precio > ema_20 else "Tendencia agotada"
                    client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=abs(amt))
                    print(f"⚠️ CERRANDO SHORT: {razon} | ADX: {adx_val:.1f}")

            # 3. SALIDA DE LONG
            elif amt > 0:
                if precio < (ema_20 * (1 - margen)) or adx_val < adx_muerto:
                    razon = "Giro fuerte" if precio < ema_20 else "Tendencia agotada"
                    client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=abs(amt))
                    print(f"⚠️ CERRANDO LONG: {razon} | ADX: {adx_val:.1f}")

            print(f"📊 MONITOR: SOL {precio:.2f} | EMA20 {ema_20:.2f} | ADX {adx_val:.1f}")
            time.sleep(10)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    ejecutar_gladiador_protector()
