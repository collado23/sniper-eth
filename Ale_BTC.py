import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de cuenta actualizado
cap_actual = 19.52 
MIN_LOT = 15.0 
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'nivel': 0} for m in ms}

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

print(f"🔱 IA QUANTUM: MODO ESCALERA ACTIVADO | NETO: ${cap_actual}")

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
                    s['t'], s['p'], s['e'], s['v'], s['nivel'] = dir, px_actual, True, vela, 0
                    print(f"🚀 {m} | DISPARO: {dir} en {px_actual}")
            
            elif s['e']:
                roi = (((px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']) * 100 * 10) - 0.22
                
                # --- LÓGICA DE ESCALONES (BREAKING BAD) ---
                # Nivel 1: Llegó a 1.2% -> Protegemos en 0.2%
                if roi >= 1.2 and s['nivel'] < 1:
                    s['nivel'] = 1
                    print(f"🛡️ NIVEL 1: BE Activado en {m} (Protección 0.2%)")
                
                # Nivel 2: Llegó a 2.0% -> Subimos piso a 1.2%
                elif roi >= 2.0 and s['nivel'] < 2:
                    s['nivel'] = 2
                    print(f"🔥 NIVEL 2: Piso subido en {m} (Protección 1.2%)")
                
                # Nivel 3: Llegó a 3.0% -> Subimos piso a 2.0%
                elif roi >= 3.0 and s['nivel'] < 3:
                    s['nivel'] = 3
                    print(f"💎 NIVEL 3: Piso subido en {m} (Protección 2.0%)")
                
                # Nivel 4: CIERRE TOTAL a 5%
                elif roi >= 5.0:
                    cap_actual += (MIN_LOT * (roi / 100))
                    s['e'] = False
                    print(f"💰 COSECHA FINAL 5% en {m} | NETO: ${cap_actual:.2f}")

                # --- CONTROL DE SALIDAS POR RETROCESO (ZIG ZAG) ---
                if s['nivel'] == 1 and roi <= 0.2:
                    cap_actual += (MIN_LOT * (roi / 100))
                    s['e'] = False; print(f"🛡️ SALIDA N1 (Protección) en {m}")
                elif s['nivel'] == 2 and roi <= 1.2:
                    cap_actual += (MIN_LOT * (roi / 100))
                    s['e'] = False; print(f"💰 SALIDA N2 (Asegurado 1.2%) en {m}")
                elif s['nivel'] == 3 and roi <= 2.0:
                    cap_actual += (MIN_LOT * (roi / 100))
                    s['e'] = False; print(f"💰 SALIDA N3 (Asegurado 2.0%) en {m}")
                
                # --- STOP LOSS / GIRO (Si nunca llegó a Nivel 1) ---
                elif roi <= -3.0:
                    nueva_dir = "SHORT" if s['t'] == "LONG" else "LONG"
                    cap_actual += (MIN_LOT * (roi / 100))
                    print(f"🔄 GIRO {m}: SL 3% tocado. Entrando en {nueva_dir}...")
                    s['t'], s['p'], s['v'], s['nivel'] = nueva_dir, px_actual, "VELA DE GIRO", 0

                print(f"📊 {m} | ROI: {roi:.2f}% | Nivel: {s['nivel']}", end='\r')

            time.sleep(1); del df
        time.sleep(10)
    except Exception as e:
        time.sleep(5); cl = c()
