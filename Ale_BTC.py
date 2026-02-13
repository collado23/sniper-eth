import os, time
import pandas as pd
import numpy as np
from binance.client import Client

def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'MATICUSDT']
LIMITE_OPERACIONES = 3

cap_actual = 17.29 
MIN_LOT = 17.0 # Subimos para acelerar la ganancia neta
st = {m: {'e': False, 'p': 0, 't': '', 'nivel': 0} for m in ms}

def calcular_indicadores(df):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    
    # MACD + Histograma (Fuerza de impulso)
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['hist'] = df['macd'] - df['signal']
    
    # Tendencia Mayor y Menor
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema27'] = df['close'].ewm(span=27, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    return df

def detectar_entrada(df):
    df = calcular_indicadores(df)
    act = df.iloc[-1]
    ant = df.iloc[-2]
    
    # El impulso debe ser fuerte: Histograma actual mayor al anterior en valor absoluto
    impulso_ok = abs(act['hist']) > abs(ant['hist'])
    vol_ok = act['v'] > df['v'].rolling(12).mean().iloc[-1] * 1.25
    
    # LONG: Confirmación de tendencia y fuerza
    if act['close'] > act['ema200'] and act['ema9'] > act['ema27'] and act['rsi'] > 54 and act['hist'] > 0 and impulso_ok:
        if vol_ok: return "LONG"
    
    # SHORT: Confirmación de tendencia y fuerza
    if act['close'] < act['ema200'] and act['ema9'] < act['ema27'] and act['rsi'] < 46 and act['hist'] < 0 and impulso_ok:
        if vol_ok: return "SHORT"
    return None

print(f"🔱 IA QUANTUM V23 | AJUSTE DE PRECISIÓN | MÁX OPS: 3 | CAP: ${cap_actual}")

while True:
    try:
        ops_abiertas = sum(1 for m in ms if st[m]['e'])
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios[m]
            if s['e']:
                diff = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (diff * 100 * 10) - 0.22
                gan_usd = (MIN_LOT * (roi / 100))

                # Escalera más fina (cada 0.15%)
                meta_actual = (int(roi * 6.66) / 6.66) 
                if meta_actual > s['nivel'] and meta_actual >= 0.4:
                    s['nivel'] = meta_actual
                    print(f"\n🛡️ {m} BLOQUEÓ: {s['nivel']:.2f}%")

                # PISO DINÁMICO MEJORADO
                # Cuanto más ganamos, más pegamos el piso para no regalar nada
                if s['nivel'] < 1.0:
                    distancia = 0.20
                elif s['nivel'] < 1.8:
                    distancia = 0.15
                else:
                    distancia = 0.10 # Modo "Garrapata" para ganancias grandes
                
                piso = s['nivel'] - distancia
                
                if s['nivel'] >= 0.4 and roi <= piso:
                    cap_actual += gan_usd
                    print(f"\n✅ CIERRE ESTRATÉGICO {m} | GANASTE: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False
                elif roi <= -0.85: # SL equilibrado
                    cap_actual += gan_usd
                    print(f"\n❌ SL PROTECTOR {m} | PNL: ${gan_usd:.2f}")
                    s['e'] = False
                
                print(f"📊 {m}: {roi:.2f}% (Piso: {piso:.2f}%)", end=' | ')
            
            else:
                if ops_abiertas < LIMITE_OPERACIONES:
                    k = cl.get_klines(symbol=m, interval='1m', limit=250)
                    df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                    df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                    res = detectar_entrada(df)
                    if res:
                        s['t'], s['p'], s['e'], s['nivel'] = res, px, True, 0
                        ops_abiertas += 1
                        print(f"\n🚀 DISPARO {res} en {m} (Impulso y Volumen OK)")
        time.sleep(1)
    except Exception as e:
        time.sleep(2); cl = c()
