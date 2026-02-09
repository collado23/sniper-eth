import os, time, pandas as pd, numpy as np
from binance.client import Client

# --- CONFIGURACIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol = "SOLUSDT"
cantidad_prueba = 0.1  
archivo_memoria = "memoria_gladiador.txt"
precio_extremo = None

def guardar_en_memoria(precio, dist, pnl, motivo):
    with open(archivo_memoria, "a") as f:
        log = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] P: {precio} | D: {dist:.2f}% | PnL: {pnl:.2f}% | {motivo}\n"
        f.write(log)
    print(f"📝 {motivo} | PnL Final: {pnl:.2f}%")

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

def ejecutar_gladiador_pnl():
    global precio_extremo
    print(f"🔱 GLADIADOR QUANTUM V5: LECTOR DE PnL Y LIBROS JAPONESES ACTIVADO")
    
    while True:
        try:
            klines = client.futures_klines(symbol=symbol, interval='1m', limit=100)
            df = pd.DataFrame(klines, columns=['t','open','high','low','close','v','ct','q','n','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            
            v = df.iloc[-1]
            precio = v['close']
            ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            adx_val = calcular_adx(df)
            dist_200 = (abs(precio - ema_200) / ema_200) * 100

            # --- ANÁLISIS DE VELAS ---
            cuerpo = abs(v['close'] - v['open'])
            mecha_sup = v['high'] - max(v['open'], v['close'])
            mecha_inf = min(v['open'], v['close']) - v['low']
            es_roja = v['close'] < v['open']
            es_verde = v['close'] > v['open']
            
            # Patrones con confirmación de color (como pediste)
            estrella_fugaz = es_roja and mecha_sup > (cuerpo * 1.8) 
            martillo_piso = es_verde and mecha_inf > (cuerpo * 1.8)

            pos = client.futures_position_information(symbol=symbol)
            datos_pos = next((p for p in pos if p['symbol'] == symbol), None)
            amt = float(datos_pos['positionAmt']) if datos_pos else 0
            
            # --- LÓGICA DE ENTRADA ---
            if amt == 0:
                precio_extremo = None
                # Giro Extremo (ADX > 65)
                if adx_val > 65:
                    if precio > ema_20 and estrella_fugaz:
                        client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=cantidad_prueba)
                        guardar_en_memoria(precio, dist_200, 0, "📉 SHORT: Estrella Fugaz Roja (ADX > 65)")
                    elif precio < ema_20 and martillo_piso:
                        client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=cantidad_prueba)
                        guardar_en_memoria(precio, dist_200, 0, "🚀 LONG: Martillo Verde (ADX > 65)")
                
                # Tendencia Sana (ADX 30-45)
                elif 30 < adx_val < 45 and dist_200 < 1.2:
                    if precio > (ema_20 * 1.002) and es_verde:
                        client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=cantidad_prueba)
                        guardar_en_memoria(precio, dist_200, 0, "🚀 LONG: Compra por Tendencia")
                    elif precio < (ema_20 * 0.998) and es_roja:
                        client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=cantidad_prueba)
                        guardar_en_memoria(precio, dist_200, 0, "📉 SHORT: Venta por Tendencia")

            # --- LÓGICA DE CIERRE CON SENSOR DE PnL ---
            elif amt != 0:
                entrada = float(datos_pos['entryPrice'])
                # Cálculo de Ganancia (PnL)
                pnl = ((precio - entrada) / entrada * 100) if amt > 0 else ((entrada - precio) / entrada * 100)
                if precio_extremo is None: precio_extremo = precio
                
                # Margen de cierre dinámico: si ya ganamos 0.4%, cerramos más rápido (0.2%)
                margen = 0.6 if pnl < 0.4 else 0.2
                
                if amt > 0: # En LONG (Verde en Binance)
                    if precio > precio_extremo: precio_extremo = precio
                    caida = (precio_extremo - precio) / precio_extremo * 100
                    if caida > margen or (estrella_fugaz and pnl > 0.1):
                        client.futures_create_order(symbol=symbol, side='SELL', type='MARKET', quantity=abs(amt))
                        guardar_en_memoria(precio, dist_200, pnl, f"🎯 CIERRE LONG (PnL: {pnl:.2f}%)")
                
                elif amt < 0: # En SHORT (Rojo en Binance si sube)
                    if precio < precio_extremo: precio_extremo = precio
                    rebote = (precio - precio_extremo) / precio_extremo * 100
                    if rebote > margen or (martillo_piso and pnl > 0.1):
                        client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=abs(amt))
                        guardar_en_memoria(precio, dist_200, pnl, f"🎯 CIERRE SHORT (PnL: {pnl:.2f}%)")

            print(f"📊 SOL: {precio:.2f} | ADX: {adx_val:.1f} | PnL: {pnl if amt != 0 else 0:.2f}%")
            time.sleep(10)

        except Exception as e:
            print(f"⚠️ Error: {e}"); time.sleep(10)

if __name__ == "__main__":
    ejecutar_gladiador_pnl()
