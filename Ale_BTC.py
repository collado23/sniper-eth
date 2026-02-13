import os, time
import pandas as pd
import numpy as np
from binance.client import Client

def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()

# Mantenemos tus 6 monedas y el límite de 3
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'MATICUSDT']
LIMITE_OPERACIONES = 3

cap_actual = 17.40 # Ajustar según tu balance real actual
MIN_LOT = 15.0  
st = {m: {'e': False, 'p': 0, 't': '', 'nivel': 0} for m in ms}

def calcular_indicadores(df):
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    
    # MACD con Histograma
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['hist'] = df['macd'] - df['signal']
    
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema27'] = df['close'].ewm(span=27, adjust=False).mean()
    return df

def detectar_entrada(df):
    df = calcular_indicadores(df)
    act = df.iloc[-1]
    ant = df.iloc[-2]
    
    # FILTRO DE IMPULSO: El histograma debe estar creciendo
    impulso_alcista = act['hist'] > ant['hist'] and act['hist'] > 0
    impulso_bajista = act['hist'] < ant['hist'] and act['hist'] < 0
    
    vol_ok = act['v'] > df['v'].rolling(10).mean().iloc[-1] * 1.2

    if act['close'] > act['ema9'] > act['ema27'] and act['rsi'] > 54 and impulso_alcista:
        if vol_ok: return "LONG"
    if act['close'] < act['ema9'] < act['ema27'] and act['rsi'] < 46 and impulso_bajista:
        if vol_ok: return "SHORT"
    return None

print(f"🔱 IA QUANTUM V21 | FILTRO IMPULSO MACD | MÁX OPS: 3 | CAP: ${cap_actual}")

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

                # Escalera de niveles
                meta_actual = (int(roi * 5) / 5.0) # Niveles cada 0.2%
                if meta_actual > s['nivel'] and meta_actual >= 0.4:
                    s['nivel'] = meta_actual
                    print(f"\n🛡️ {m} NIVEL ALCANZADO: {s['nivel']}%")

                # PISO DINÁMICO: 
                # Si el ROI es bajo, damos aire (0.2). Si es alto, apretamos (0.1)
                distancia = 0.20 if s['nivel'] < 1.0 else 0.10
                piso = s['nivel'] - distancia
                
                if s['nivel'] >= 0.4 and roi <= piso:
                    cap_actual += gan_usd
                    print(f"\n✅ CIERRE TÉCNICO {m} | GANASTE: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False
                elif roi <= -0.85: # Stop Loss con un poco más de aire
                    cap_actual += gan_usd
                    print(f"\n❌ SL PROTECTOR {m} | PNL: ${gan_usd:.2f}")
                    s['e'] = False
                
                print(f"📊 {m}: {roi:.2f}% (Piso: {piso:.2f}%)", end=' | ')
            
            else:
                if ops_abiertas < LIMITE_OPERACIONES:
                    k = cl.get_klines(symbol=m, interval='1m', limit=60)
                    df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                    df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                    res = detectar_entrada(df)
                    if res:
                        s['t'], s['p'], s['e'], s['nivel'] = res, px, True, 0
                        ops_abiertas += 1
                        print(f"\n🚀 DISPARO {res} en {m} (Impulso Confirmado)")

        time.sleep(1.2)

    except Exception as e:
        time.sleep(2); cl = c()
