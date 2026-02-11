import os, time
import pandas as pd
from binance.client import Client

def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap_actual = 30.80 
st = {m: {'n': 0.0, 'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False, 'h': []} for m in ms}

def calcular_cerebro(df):
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema_35'] = df['close'].ewm(span=35, adjust=False).mean()
    df['vel'] = df['close'].diff()
    df['acel'] = df['vel'].diff()
    df['rango'] = df['high'] - df['low']
    df['z_score'] = (df['rango'] - df['rango'].rolling(20).mean()) / df['rango'].rolling(20).std()
    return df

def ni(df):
    act = df.iloc[-1]; prev = df.iloc[-2]
    cuerpo = abs(act['close'] - act['open']) or 0.001
    # LONG
    l_ok = (act['close'] > act['ema_200']) and (act['ema_35'] > act['ema_50'])
    m_inf = act['open'] - act['low'] if act['close'] > act['open'] else act['close'] - act['low']
    if l_ok:
        if (m_inf > cuerpo * 3.0) and (act['acel'] > 0): return "🔨"
        if (act['close'] > prev['high']) and (act['z_score'] < 1.8): return "V"
    # SHORT
    s_ok = (act['close'] < act['ema_200']) and (act['ema_35'] < act['ema_50'])
    m_sup = act['high'] - act['close'] if act['close'] > act['open'] else act['high'] - act['open']
    if s_ok:
        if (m_sup > cuerpo * 2.2) and (act['acel'] < 0): return "☄️"
        if (act['close'] < prev['low']) and (act['z_score'] < 2.2): return "R"
    return "."

print(f"🔱 SCALPER QUANTUM ON | CAP: ${cap_actual} | 15s")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=201)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            df = calcular_cerebro(df)
            px = df['close'].iloc[-1]
            ptr = ni(df)

            if not s['e']:
                print(f"{m[:2]}:{ptr}", end=' ')
                if ptr != ".":
                    s['t'] = "LONG" if ptr in ["🔨", "V"] else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 IN {m} {s['t']} ({ptr})")
            else:
                # --- NÚCLEO TÁCTICO SCALPER ---
                df_p = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df_p * 100 * 10) - 0.20 # Apalancamiento x10 - Comisiones
                
                if roi > s['m']: s['m'] = roi
                if roi >= 0.08: s['b'] = True # Breakeven Agresivo

                # Trailing Stop "Scalper"
                distancia = 0.08 if s['t'] == "SHORT" else 0.12
                t_stop = (roi <= (s['m'] - distancia)) if s['m'] >= 0.25 else False
                
                # Cierre de Operación
                if (s['b'] and roi <= 0.02) or t_stop or roi <= -0.45:
                    gan = (cap_actual * (roi / 100))
                    cap_actual += gan
                    s['o'] += 1; s['e'] = False
                    est = "✅" if roi > 0 else "❌"
                    s['h'].append(f"{est} {s['t']} {roi:.2f}%")
                    print(f"\n{est} OUT {m} {roi:.2f}% | CAP: ${cap_actual:.2f}")

                    if s['o'] % 5 == 0:
                        print(f"\n╔{'═'*32}╗\n║ 📊 REPORTE 5 OPS - {m[:3]} ║")
                        for line in s['h']: print(f"║ {line.ljust(28)} ║")
                        print(f"╠{'═'*32}╣\n║ CAP TOTAL: ${cap_actual:.2f}   ║\n╚{'═'*32}╝\n")
                        s['h'] = []
        time.sleep(15)
    except:
        time.sleep(10); cl = c()
