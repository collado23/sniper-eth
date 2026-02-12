import os, time
import pandas as pd
from binance.client import Client

# Conexión Segura Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de cuenta
cap_inicial = 18.73 
cap_actual = 18.73 
MIN_LOT = 15.0 
ops_count = 0
ops_ganadas = 0
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'be': False} for m in ms}

def detectar_entrada(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    c_act, o_act = df['close'].iloc[-1], df['open'].iloc[-1]
    c_ant, o_ant = df['close'].iloc[-2], df['open'].iloc[-2]
    e9, e27 = df['ema_9'].iloc[-1], df['ema_27'].iloc[-1]
    envolvente = abs(c_act - o_act) > abs(c_ant - o_ant)

    if c_act > o_act and c_act > e9 and e9 > e27 and envolvente:
        return "LONG", "ENVOLVENTE ALCISTA"
    if c_act < o_act and c_act < e9 and e9 < e27 and envolvente:
        return "SHORT", "ENVOLVENTE BAJISTA"
    return None, None

print(f"🔱 IA QUANTUM | STOP LOSS: 3% | BREAK EVEN: 1.2% | NETO: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px_actual = df['close'].iloc[-1]
            
            if not s['e']:
                dir, vela = detectar_entrada(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'], s['be'] = dir, px_actual, True, vela, False
                    print(f"🔥 {m} | VELA: {vela} | {dir} en {px_actual}")
            
            elif s['e']:
                roi = (((px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']) * 100 * 10) - 0.22
                
                # MONITOR DE PRECIO Y ROI
                print(f"📊 {m} | ROI: {roi:.2f}% | Precio: {px_actual} | BE: {'SI' if s['be'] else 'NO'}")

                # 1. ACTIVAR BREAK EVEN (A 1.2%)
                if roi >= 1.2 and not s['be']:
                    s['be'] = True
                    print(f"🛡️ ESCUDO ACTIVADO en {m} (Protegiendo en 1.2%)")

                # 2. COSECHA (2%)
                if roi >= 2.0:
                    cap_actual += (MIN_LOT * (roi / 100))
                    ops_count += 1; ops_ganadas += 1; s['e'] = False
                    print(f"💰 COSECHA {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")
                
                # 3. SALIDA POR BREAK EVEN (Si cae tras tocar 1.2%)
                elif s['be'] and roi <= 0.2:
                    cap_actual += (MIN_LOT * (roi / 100))
                    ops_count += 1; s['e'] = False
                    print(f"🛡️ SALIDA SEGURA {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

                # 4. STOP LOSS NUEVO (A -3.0% con GIRO)
                elif roi <= -3.0:
                    nueva_dir = "SHORT" if s['t'] == "LONG" else "LONG"
                    cap_actual += (MIN_LOT * (roi / 100))
                    ops_count += 1
                    print(f"🔄 GIRO {m}: SL 3% tocado. Entrando en {nueva_dir}...")
                    s['t'], s['p'], s['v'], s['be'] = nueva_dir, px_actual, "VELA DE GIRO", False

            time.sleep(1); del df

        time.sleep(10)
    except Exception as e:
        time.sleep(5); cl = c()
