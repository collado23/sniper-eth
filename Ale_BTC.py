import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# ¡FELICITACIONES! Neto rompió los $22
cap_actual = 22.14 
MIN_LOT = 15.0 
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'nivel': 0} for m in ms}

def detectar_entrada(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    c_act, o_act = df['close'].iloc[-1], df['open'].iloc[-1]
    c_ant, o_ant = df['close'].iloc[-2], df['open'].iloc[-2]
    e9, e27 = df['ema_9'].iloc[-1], df['ema_27'].iloc[-1]
    envolvente = abs(c_act - o_act) > abs(c_ant - o_ant)
    if c_act > o_act and c_act > e9 and e9 > e27 and envolvente: return "LONG", "ALCISTA"
    if c_act < o_act and c_act < e9 and e9 < e27 and envolvente: return "SHORT", "BAJISTA"
    return None, None

print(f"🔱 IA QUANTUM: MODO INFINITO (9.5%) | NETO: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px_actual = df['close'].iloc[-1]
            e9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
            e27 = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]
            
            if not s['e']:
                dir, vela = detectar_entrada(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'], s['nivel'] = dir, px_actual, True, vela, 0
                    print(f"🚀 {m} | DISPARO: {dir} en {px_actual}")
            
            elif s['e']:
                roi = (((px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']) * 100 * 10) - 0.22
                
                # --- SUPER ESCALERA DE NIVELES ---
                niveles_roi = [1.2, 2.0, 2.5, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0]
                for i, valor in enumerate(niveles_roi):
                    if roi >= valor and s['nivel'] < (i + 1):
                        s['nivel'] = i + 1
                        print(f"⭐ {m} ALCANZÓ NIVEL {s['nivel']} (ROI: {roi:.2f}%)")

                # META FINAL 9.5%
                if roi >= 9.5:
                    cap_actual += (MIN_LOT * (roi / 100))
                    print(f"💰 COSECHA TOTAL 9.5% en {m} | NETO: ${cap_actual:.2f}")
                    if (s['t'] == "LONG" and e9 > e27) or (s['t'] == "SHORT" and e9 < e27):
                        s['p'], s['nivel'] = px_actual, 0
                        print(f"🔄 PERSISTENCIA ACTIVADA EN {m}")
                    else: s['e'] = False

                # CONTROL DE ZIG ZAG (PISOS)
                pisos = {1:0.2, 2:1.2, 3:2.0, 4:2.5, 5:3.5, 6:4.0, 7:4.5, 8:5.0, 9:5.5, 10:6.0, 11:6.5, 12:7.0, 13:7.5, 14:8.0, 15:8.5}
                if s['nivel'] in pisos and roi <= pisos[s['nivel']]:
                    cap_actual += (MIN_LOT * (roi / 100))
                    s['e'] = False
                    print(f"🛡️ SALIDA PROTEGIDA N{s['nivel']} en {m} | NETO: ${cap_actual:.2f}")

                # GIRO POR STOP LOSS (-3%)
                elif roi <= -3.0:
                    cap_actual += (MIN_LOT * (roi / 100))
                    s['t'] = "SHORT" if s['t'] == "LONG" else "LONG"
                    s['p'], s['nivel'] = px_actual, 0
                    print(f"🔄 GIRO {m} en {s['t']}...")

                print(f"📊 {m} | ROI: {roi:.2f}% | Nivel: {s['nivel']}", end='\r')

            time.sleep(1); del df
        time.sleep(10)
    except Exception as e:
        time.sleep(5); cl = c()
