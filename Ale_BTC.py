import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Parámetros Ale (Neto actual y disparo fijo)
cap_actual = 20.50 
MIN_LOT = 15.0 # Tu disparo de $15
st = {m: {'e': False, 'p': 0, 't': ''} for m in ms}

def detectar_rebote_agresivo(df):
    # EMAs para ver la panza
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   # Amarilla
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() # Azul
    
    # Precios y velas
    c = df['close'].iloc[-1]; o = df['open'].iloc[-1]
    cp = df['close'].iloc[-2]; op = df['open'].iloc[-2]
    e9 = df['ema_9'].iloc[-1]; e27 = df['ema_27'].iloc[-1]
    
    # LOGICA DE REBOTE LARGO (Tu dibujo)
    # 1. Venimos de una roja (cp < op) que toca o se acerca a la azul (e27)
    # 2. Sale una verde (c > o) con fuerza que cruza la amarilla (e9)
    if c > o and cp < op and c > e9: 
        if e9 >= e27: return "LONG"   # Rebote hacia arriba
        if e9 <= e27: return "SHORT"  # Rebote hacia abajo (caída libre)
    return None

print(f"🔱 MODO CAZADOR DE REBOTES | NETO: ${cap_actual} | DISPARO: ${MIN_LOT}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px = df['close'].iloc[-1]
            
            senal = detectar_rebote_agresivo(df)

            if not s['e'] and senal:
                # DISPARO AGRESIVO
                s['t'], s['p'], s['e'] = senal, px, True
                print(f"🚀 REBOTE DETECTADO en {m}: Entrando en {senal} a {px}")
            
            elif s['e']:
                # Calculo de ganancia con x10
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                
                # SALIDA POR CIERRE DE PANZA (Cuando la vela se cansa y vuelve a la azul)
                e27 = df['ema_27'].iloc[-1]
                toca_azul = (s['t'] == "LONG" and px <= e27) or (s['t'] == "SHORT" and px >= e27)
                
                if toca_azul:
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    print(f"💰 REBOTE COMPLETADO en {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(15)
    except Exception as e:
        time.sleep(10); cl = c()
