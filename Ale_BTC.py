import os, time
import pandas as pd
from binance.client import Client

def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT'] 

# Iniciamos con el neto de tus últimos logs
cap_actual = 22.32 
st = {m: {'e': False, 'p': 0, 't': '', 'm': -9.0} for m in ms}

def analizar_fisica_ale(df):
    act = df.iloc[-1]; prev = df.iloc[-2]
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   # Sigue a la vela
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() # Inercia (Salida)
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean() # Gravedad
    
    e9 = df['ema_9'].iloc[-1]
    e27 = df['ema_27'].iloc[-1]
    e200 = df['ema_200'].iloc[-1]
    
    # ENTRADA: Cuando la 9 (vela) cruza la 27 y estamos a favor de la 200
    # SHORT (Bajada): Si estamos bajo la 200 y la 9 cruza hacia abajo la 27
    if act['close'] < e200 and e9 < e27 and df['ema_9'].iloc[-2] >= df['ema_27'].iloc[-2]:
        return "🟥"
    # LONG (Subida): Si estamos sobre la 200 y la 9 cruza hacia arriba la 27
    if act['close'] > e200 and e9 > e27 and df['ema_9'].iloc[-2] <= df['ema_27'].iloc[-2]:
        return "🟩"
    return "."

print(f"🔱 IA QUANTUM | MODO DIBUJO ALE | EJE 27 | CAP: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=200)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            
            px = df['close'].iloc[-1]
            senal = analizar_fisica_ale(df)

            if not s['e']:
                if senal != ".":
                    s['t'] = "LONG" if senal == "🟩" else "SHORT"
                    s['p'], s['e'] = px, True
                    print(f"\n🎯 ENTRADA EN {m} ({s['t']}) | Siguiendo inercia...")
            else:
                # GESTIÓN DE SALIDA: Solo cuando toca la 27 (como tu dibujo)
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                
                e27_act = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]
                
                # CONDICIÓN DE VENTA ALE: Cruzar la 27
                vender = (s['t'] == "LONG" and px <= e27_act) or (s['t'] == "SHORT" and px >= e27_act)

                if vender or roi <= -0.80: # Stop de seguridad un poco más ancho
                    cap_actual += (cap_actual * (roi / 100))
                    s['e'] = False
                    icon = "✅" if roi > 0 else "❌"
                    print(f"{icon} SALIDA {m} EN 27 | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(15)
    except:
        time.sleep(10); cl = c()
