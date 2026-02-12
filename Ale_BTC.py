import os, time
import pandas as pd
from binance.client import Client

def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

cap_actual = 22.71 
st = {m: {'e': False, 'p': 0, 't': '', 'm': -9.0} for m in ms}

def analizar_fisica_rapida(df):
    # Usamos menos velas para que el cálculo sea instantáneo
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean()
    
    e9 = df['ema_9'].iloc[-1]; e27 = df['ema_27'].iloc[-1]
    e9_p = df['ema_9'].iloc[-2]; e27_p = df['ema_27'].iloc[-2]
    
    # ENTRADA MÁS SENSIBLE: Detecta el cruce apenas ocurre
    if e9 < e27 and e9_p >= e27_p: return "🟥" 
    if e9 > e27 and e9_p <= e27_p: return "🟩" 
    return "."

print(f"🔱 IA QUANTUM FLASH | EJE 27 + TRAILING 1.8% | NETO: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            # Pedimos solo 50 velas para ganar velocidad de proceso
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df['close'] = df['close'].astype(float)
            
            px = df['close'].iloc[-1]
            
            if not s['e']:
                senal = analizar_fisica_rapida(df)
                if senal != ".":
                    s['t'] = "LONG" if senal == "🟩" else "SHORT"
                    s['p'], s['e'], s['m'] = px, True, -9.0
                    print(f"\n⚡ ENTRADA RÁPIDA {m} ({s['t']})")
            else:
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                if roi > s['m']: s['m'] = roi 
                
                ema_27 = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]
                
                # SALIDA FLASH: 
                # 1. Toque de la 27 (Tu dibujo)
                # 2. Trailing 1.8% (Tu seguro)
                # 3. Stop de emergencia (Protección)
                toca_27 = (s['t'] == "LONG" and px <= ema_27) or (s['t'] == "SHORT" and px >= ema_27)
                trail = (s['m'] >= 1.8 and roi <= (s['m'] - 0.3))

                if toca_27 or trail or roi <= -1.0:
                    cap_actual += (cap_actual * (roi / 100))
                    s['e'] = False
                    mot = "TRAIL" if trail else "EJE 27"
                    print(f"⏱️ SALIDA {m} ({mot}) | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(10) # Bajamos de 15 a 10 segundos para más velocidad
    except:
        time.sleep(5); cl = c()
