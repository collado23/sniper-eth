import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de cuenta (Ajustado a $18.73)
cap_actual = 18.73 
MIN_LOT = 15.0 
st = {m: {'e': False, 'p': 0, 't': '', 'v': ''} for m in ms}

def identificar_vela_maestra(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    c_act, o_act = df['close'].iloc[-1], df['open'].iloc[-1]
    c_ant, o_ant = df['close'].iloc[-2], df['open'].iloc[-2]
    e9, e27 = df['ema_9'].iloc[-1], df['ema_27'].iloc[-1]
    
    envolvente = abs(c_act - o_act) > (abs(c_ant - o_ant) * 1.1)

    if c_act > o_act and c_ant < o_ant and c_act > e9 and e9 > e27 and envolvente:
        return "LONG", "ENVOLVENTE ALCISTA"
    if c_act < o_act and c_ant > o_ant and c_act < e9 and e9 < e27 and envolvente:
        return "SHORT", "ENVOLVENTE BAJISTA"
    return None, None

print(f"🔱 IA QUANTUM: MODO GIRO TOTAL | NETO: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px_actual = df['close'].iloc[-1]
            
            # 1. BUSCAR ENTRADA
            if not s['e']:
                dir, vela = identificar_vela_maestra(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'] = dir, px_actual, True, vela
                    print(f"🔥 {m} | VELA: {vela} | {dir} en {px_actual}")
            
            # 2. MONITOR Y GIRO
            elif s['e']:
                roi = (((px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']) * 100 * 10) - 0.22
                print(f"📊 {m} | {s['t']} | Entró: {s['p']} | Ahora: {px_actual} | ROI: {roi:.2f}%")
                
                # REGLA DE GIRO: Si perdemos 2%, cerramos y entramos al revés
                if roi <= -2.0:
                    nueva_dir = "SHORT" if s['t'] == "LONG" else "LONG"
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    print(f"🔄 ¡GIRO EN {m}! Falló {s['t']}, entrando en {nueva_dir}")
                    s['t'], s['p'], s['v'] = nueva_dir, px_actual, "VELA DE GIRO"
                
                # COSECHA: Si ganamos 2%, cobramos
                elif roi >= 2.0:
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    print(f"💰 COSECHA en {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(15)
    except Exception as e:
        time.sleep(10); cl = c()
