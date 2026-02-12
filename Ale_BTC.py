import os, time
import pandas as pd
from binance.client import Client

# Conexión Segura
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Parámetros Ale
cap_actual = 20.50 
MIN_LOT = 15.0 
st = {m: {'e': False, 'p': 0, 't': ''} for m in ms}

def detectar_rebote_agresivo(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   # Amarilla
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() # Azul
    
    c = df['close'].iloc[-1]; o = df['open'].iloc[-1]
    cp = df['close'].iloc[-2]; op = df['open'].iloc[-2]
    e9 = df['ema_9'].iloc[-1]; e27 = df['ema_27'].iloc[-1]
    
    # REBOTE: Vela actual verde, anterior roja, y precio sobre la amarilla
    if c > o and cp < op and c > e9:
        return "LONG" if e9 >= e27 else "SHORT"
    return None

print(f"🔱 TRIPLE CAZADOR ACTIVADO | MONEDAS: {ms} | DISPARO: ${MIN_LOT}")

while True:
    try:
        for m in ms:
            s = st[m]
            # Pedimos 100 velas para tener historial de sobra
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px = df['close'].iloc[-1]
            
            senal = detectar_rebote_agresivo(df)

            # ENTRADA: Si no está en esa moneda y ve rebote
            if not s['e'] and senal:
                s['t'], s['p'], s['e'] = senal, px, True
                print(f"🚀 DISPARO en {m}: Rebote {senal} a {px}")
            
            # SALIDA: Si está dentro de esa moneda
            elif s['e']:
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                e27 = df['ema_27'].iloc[-1]
                
                # Cerramos cuando el rebote vuelve a tocar la base (línea azul)
                toca_base = (s['t'] == "LONG" and px <= e27) or (s['t'] == "SHORT" and px >= e27)
                
                if toca_base:
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    print(f"💰 CIERRE en {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(10) # Escaneo rápido cada 10 segundos
    except Exception as e:
        time.sleep(5); cl = c()
