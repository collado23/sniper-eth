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
MIN_LOT = 17.0 
st = {m: {'e': False, 'p': 0, 't': '', 'nivel': 0} for m in ms}

def calcular_indicadores(df):
    # RSI y MACD
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['hist'] = df['macd'] - df['signal']
    # EMAs
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema27'] = df['close'].ewm(span=27, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    return df

def detectar_entrada(df):
    df = calcular_indicadores(df)
    act = df.iloc[-1]
    ant = df.iloc[-2]
    
    # Filtro de impulso agresivo
    impulso_ok = abs(act['hist']) > abs(ant['hist'])
    vol_ok = act['v'] > df['v'].rolling(12).mean().iloc[-1] * 1.3
    
    if act['close'] > act['ema200'] and act['ema9'] > act['ema27'] and act['rsi'] > 54 and act['hist'] > 0 and impulso_ok:
        if vol_ok: return "LONG"
    if act['close'] < act['ema200'] and act['ema9'] < act['ema27'] and act['rsi'] < 46 and act['hist'] < 0 and impulso_ok:
        if vol_ok: return "SHORT"
    return None

print(f"🔱 IA QUANTUM V24 | FRENO ANTIRRETROCESO | CAP: ${cap_actual}")

while True:
    try:
        ops_abiertas = sum(1 for m in ms if st[m]['e'])
        precios = {t['symbol']: float(t['price']) for t in cl.get_all_tickers() if t['symbol'] in ms}
        
        for m in ms:
            s = st[m]
            px = precios[m]
            if s['e']:
                # Pedimos velas recientes para ver si hay retroceso brusco
                k = cl.get_klines(symbol=m, interval='1m', limit=2)
                v_act = float(k[-1][4]) # Cierre actual
                v_open = float(k[-1][1]) # Apertura actual
                
                diff = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (diff * 100 * 10) - 0.22
                gan_usd = (MIN_LOT * (roi / 100))

                # ACTUALIZAR NIVELES CADA 0.1% (Más rápido)
                meta_actual = (int(roi * 10) / 10.0)
                if meta_actual > s['nivel'] and meta_actual >= 0.4:
                    s['nivel'] = meta_actual

                # --- LÓGICA DE SALIDA ANTIRRETROCESO ---
                piso = s['nivel'] - 0.12 # Piso muy pegado siempre
                
                # 1. Salida por Piso Tradicional
                salida_piso = s['nivel'] >= 0.4 and roi <= piso
                
                # 2. Salida de Emergencia: Si la vela actual se pone muy roja en un LONG
                retroceso_brusco = False
                if roi > 0.3: # Solo si ya estamos en ganancia
                    if s['t'] == "LONG" and v_act < v_open: # Vela bajista
                        retroceso_brusco = (v_open - v_act) / v_open * 100 * 10 > 0.15 # Retroceso de 0.15% en 1m
                    elif s['t'] == "SHORT" and v_act > v_open: # Vela alcista
                        retroceso_brusco = (v_act - v_open) / v_open * 100 * 10 > 0.15

                if salida_piso or retroceso_brusco:
                    cap_actual += gan_usd
                    razon = "PISO" if salida_piso else "FRENO"
                    print(f"\n✅ CIERRE {razon} en {m} | GANASTE: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False
                elif roi <= -0.75: # Stop Loss de seguridad
                    cap_actual += gan_usd
                    print(f"\n❌ SL PROTECTOR {m} | PNL: ${gan_usd:.2f}")
                    s['e'] = False
                
                print(f"📊 {m}: {roi:.2f}% (P: {piso:.2f}%)", end=' | ')
            
            else:
                if ops_abiertas < LIMITE_OPERACIONES:
                    k = cl.get_klines(symbol=m, interval='1m', limit=250)
                    df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
                    df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
                    res = detectar_entrada(df)
                    if res:
                        s['t'], s['p'], s['e'], s['nivel'] = res, px, True, 0
                        ops_abiertas += 1
                        print(f"\n🚀 DISPARO {res} en {m}")
        time.sleep(0.8) # Más rápido para no perder el retroceso
    except Exception as e:
        time.sleep(2); cl = c()
