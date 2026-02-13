import os, time
import pandas as pd
import pandas_ta as ta
from binance.client import Client

# Conexión
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# CAPITAL SEGÚN TU LOG
cap_actual = 18.45 
MIN_LOT = 15.0  
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'nivel': 0} for m in ms}

def detectar_entrada(df):
    # Calculamos fuerza y tendencia
    df['ema_9'] = ta.ema(df['close'], length=9)
    df['ema_27'] = ta.ema(df['close'], length=27)
    df['rsi'] = ta.rsi(df['close'], length=14)
    adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
    df['adx'] = adx_df['ADX_14']
    
    act = df.iloc[-1]
    
    # FILTROS DE ALTA PRECISIÓN
    fuerza_ok = act['adx'] > 22 # Solo si hay tendencia moviéndose
    vol_ok = act['v'] > df['v'].rolling(10).mean().iloc[-1] * 1.1
    cuerpo = abs(act['close'] - act['open'])
    mecha_ok = cuerpo > ((act['high'] - act['low']) * 0.7)

    # Lógica de Disparo
    if fuerza_ok and vol_ok and mecha_ok:
        # LONG
        if act['close'] > act['ema_9'] > act['ema_27'] and act['rsi'] > 52:
            return "LONG"
        # SHORT
        if act['close'] < act['ema_9'] < act['ema_27'] and act['rsi'] < 48:
            return "SHORT"
            
    return None

print(f"🔱 IA QUANTUM V12 | MODO FRANCOTIRADOR | CAP: ${cap_actual}")

while True:
    try:
        # Una sola petición para todos los precios (Optimiza los 14s)
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios[m]
            
            if s['e']:
                # CALCULO ROI Y GANANCIA
                diff = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (diff * 100 * 10) - 0.22 # x10 palanca y comisiones
                gan_usd = (MIN_LOT * (roi / 100))
                
                # --- ESCALERA 0.5 A 20% ---
                # Cada 0.5% sube el nivel. El piso es siempre nivel - 0.4%
                meta_detectada = (int(roi * 2) / 2.0) 
                if meta_detectada > s['nivel'] and meta_detectada >= 0.5:
                    s['nivel'] = meta_detectada
                    print(f"\n🛡️ {m} BLOQUEÓ NIVEL {s['nivel']}%")

                # EJECUCIÓN DE SALIDAS
                piso_salida = s['nivel'] - 0.4
                
                # 1. Salida por Piso (Breakeven/Trail)
                if s['nivel'] >= 0.5 and roi <= piso_salida:
                    cap_actual += gan_usd
                    print(f"\n✅ CIERRE PROTEGIDO {m} | GANASTE: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False

                # 2. Stop Loss de Seguridad (Apretado a -0.7%)
                elif roi <= -0.7:
                    cap_actual += gan_usd
                    print(f"\n❌ SL CORTADO {m} | PNL: ${gan_usd:.2f}")
                    s['e'] = False

                print(f"📊 {m}: {roi:.2f}% (N{s['nivel']})", end=' | ')

            else:
                # Análisis de entrada
                k = cl.get_klines(symbol=m, interval='1m', limit=50)
                df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                
                res = detectar_entrada(df)
                if res:
                    s['t'], s['p'], s['e'], s['nivel'] = res, px, True, 0
                    print(f"\n🚀 ENTRADA CONFIRMADA {m} | {res} | Px: {px}")

        time.sleep(1.5) # Respiro para la API

    except Exception as e:
        time.sleep(2); cl = c()
