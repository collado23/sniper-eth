import os, time, pandas as pd
import numpy as np
from binance.client import Client

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Chequeá que en Railway las variables se llamen exactamente así
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

# CAMBIO DE MONEDA A SOL PARA PRUEBA
symbol = "SOLUSDT" 
leverage = 10
capital_percent = 0.10  # Subimos al 10% para que Binance acepte la orden de SOL sin errores

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

def ejecutar_gladiador_sol():
    print(f"🔱 CAMBIANDO A SOLANA - SIMULACIÓN ACTIVA")
    
    while True:
        try:
            # Forzamos 1 minuto para ver el cambio rápido
            klines = client.futures_klines(symbol=symbol, interval='1m', limit=100)
            df = pd.DataFrame(klines, columns=['time','open','high','low','close','vol','ct','q','n','tb','tq','i'])
            df[['high','low','close']] = df[['high','low','close']].astype(float)
            
            precio = df['close'].iloc[-1]
            ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
            adx_val = calcular_adx(df)
            
            pos = client.futures_position_information(symbol=symbol)
            datos_pos = next((p for p in pos if p['symbol'] == symbol), None)
            amt = float(datos_pos['positionAmt']) if datos_pos else 0
            balance = float(client.futures_account_balance()[1]['balance'])

            # LÓGICA DE GIRO (FLIP) PARA SOL
            if amt == 0:
                # Entrada inicial
                side = 'SELL' if precio < ema_20 else 'BUY'
                qty = round((balance * capital_percent * leverage) / precio, 1) # SOL usa 1 decimal
                client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=qty)
                print(f"🚀 ENTRADA SOL: {side} a {precio}")

            elif amt < 0 and precio > ema_20: # Giro a Long
                client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=abs(amt))
                qty = round((balance * capital_percent * leverage) / precio, 1)
                client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=qty)
                print(f"🔄 GIRO SOL: Pasando a LONG")

            elif amt > 0 and precio < ema_20: # Giro a Short
                client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=abs(amt))
                qty = round((balance * capital_percent * leverage) / precio, 1)
                client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=qty)
                print(f"🔄 GIRO SOL: Pasando a SHORT")

            print(f"📊 SOL: {precio} | EMA20: {ema_20:.2f} | ADX: {adx_val:.1f}")
            time.sleep(10)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    ejecutar_gladiador_sol()
