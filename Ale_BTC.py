import os, time
import pandas as pd
import numpy as np
from binance.client import Client

def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'MATICUSDT']
LIMITE_OPERACIONES = 2

cap_actual = 16.54 
MIN_LOT = 16.5
st = {m: {'e': False, 'p': 0, 't': '', 'max_px': 0, 'break_even': False} for m in ms}

def calcular_indicadores(df):
    df['ema35'] = df['close'].ewm(span=35, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # Índice de Fuerza Relativa (RSI) para detectar agotamiento
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    
    # ATR para medir la "normalidad" del movimiento
    high_low = df['high'] - df['low']
    df['atr'] = high_low.rolling(14).mean()
    return df

def detectar_entrada(df):
    df = calcular_indicadores(df)
    act = df.iloc[-1]
    
    # DISTANCIA ENTRE EMAs (Reduce Trend)
    # Si las medias están muy pegadas, el riesgo es alto (lateral)
    distancia_medias = abs(act['ema35'] - act['ema50']) / act['ema50'] * 100
    vol_ok = act['v'] > df['v'].rolling(20).mean().iloc[-1] * 1.5

    if distancia_medias > 0.05 and vol_ok: # Solo si hay tendencia clara
        if act['ema35'] > act['ema50'] and act['rsi'] > 52:
            return "LONG"
        if act['ema35'] < act['ema50'] and act['rsi'] < 48:
            return "SHORT"
    return None

print(f"🔱 IA QUANTUM V32 | MULTIMODAL & RISK REDUCE | CAP: ${cap_actual}")

while True:
    try:
        ops_abiertas = sum(1 for m in ms if st[m]['e'])
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios[m]
            if s['e']:
                # Calcular ROI y distancias
                if s['t'] == "LONG":
                    s['max_px'] = max(s['max_px'], px)
                    retroceso = (s['max_px'] - px) / s['p'] * 1000
                else:
                    s['max_px'] = min(s['max_px'], px) if s['max_px'] > 0 else px
                    retroceso = (px - s['max_px']) / s['p'] * 1000

                roi = ((px - s['p']) / s['p'] * 1000) if s['t'] == "LONG" else ((s['p'] - px) / s['p'] * 1000)
                roi -= 0.22 

                # 🛡️ PROTECCIÓN DE RIESGO (Reduce Trend Logic)
                # Si llega a 0.4% de ROI, movemos el Stop al precio de entrada (Break Even)
                if roi > 0.4 and not s['break_even']:
                    s['break_even'] = True
                    print(f"\n🛡️ {m} EN BREAK-EVEN (Riesgo Cero)")

                # LÓGICA DE SALIDA SEGÚN EL MOVIMIENTO
                # Si el ROI es alto (explosión), el resorte es más sensible
                freno = 0.20 if roi > 1.2 else 0.40
                
                # Salida por retroceso, stop loss inicial o break even
                if (roi > 0.3 and retroceso > freno) or (s['break_even'] and roi < 0.05) or roi <= -1.0:
                    gan_usd = (MIN_LOT * (roi / 100))
                    cap_actual += gan_usd
                    print(f"\n✅ SALIDA ASEGURADA {m} | GANASTE: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False
                
                print(f"📊 {m}: {roi:.2f}%", end=' | ')
            
            else:
                if ops_abiertas < LIMITE_OPERACIONES:
                    k = cl.get_klines(symbol=m, interval='1m', limit=150)
                    df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i']).astype(float)
                    res = detectar_entrada(df)
                    if res:
                        s['t'], s['p'], s['e'], s['max_px'], s['break_even'] = res, px, True, px, False
                        ops_abiertas += 1
                        print(f"\n🎯 ENTRADA {res} en {m} (Tendencia Validada)")

        time.sleep(1)
    except Exception as e:
        time.sleep(2); cl = c()
