import os, time
import pandas as pd
from binance.client import Client

def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap_actual = 29.20 
st = {m: {'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False, 'h': []} for m in ms}

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
    l_ok = (act['close'] > act['ema_200']) and (act['ema_35'] > act['ema_50'])
    s_ok = (act['close'] < act['ema_200']) and (act['ema_35'] < act['ema_50'])
    
    # LONG - Más exigente para no entrar en techos
    m_inf = act['open'] - act['low'] if act['close'] > act['open'] else act['close'] - act['low']
    if l_ok and (m_inf > cuerpo * 3.5) and (act['acel'] > 0) and (act['z_score'] < 1.5): return "🔨"
    
    # SHORT - Más exigente para no entrar en suelos
    m_sup = act['high'] - act['close'] if act['close'] > act['open'] else act['high'] - act['open']
    if s_ok and (m_sup > cuerpo * 3.0) and (act['acel'] < 0) and (act['z_score'] < 1.5): return "☄️"
    
    return "."

print(f"🔱 ESCUDO QUANTUM ACTIVADO | CAP: ${cap_actual} | SL: -0.25%")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            df = calcular_cerebro(df)
            px = df['close'].iloc[-1]
            ptr = ni(df)

            if not s['e']:
                if ptr != ".":
                    s['t'] = "LONG" if ptr == "🔨" else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 ENTRADA {m} {s['t']} | CAP: ${cap_actual:.2f}")
            else:
                df_p = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df_p * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                
                # --- LÓGICA DE SUPERVIVENCIA ---
                # 1. Breakeven al 0.05%: Si estamos en verde mínimo, protegemos.
                if roi >= 0.05: s['b'] = True 
                
                # 2. Trailing Stop pegadísimo: Si ganamos 0.20%, el stop está a 0.05%.
                t_stop = (roi <= (s['m'] - 0.05)) if s['m'] >= 0.20 else False
                
                # 3. Stop Loss de Emergencia (Corte rápido)
                sl_emergencia = roi <= -0.25

                if (s['b'] and roi <= 0.01) or t_stop or sl_emergencia:
                    gan = (cap_actual * (roi / 100))
                    cap_actual += gan
                    s['o'] += 1; s['e'] = False
                    est = "✅" if roi > 0 else "❌"
                    s['h'].append(f"{est} {s['t']} {roi:.2f}%")
                    print(f"\n{est} SALIDA {m} {roi:.2f}% | NETO: ${cap_actual:.2f}")

                    if s['o'] % 5 == 0:
                        print(f"\n╔{'═'*32}╗\n║ 📊 REPORTE 5 OPS - {m[:3]} ║")
                        for line in s['h']: print(f"║ {line.ljust(28)} ║")
                        print(f"╠{'═'*32}╣\n║ SALDO ACTUAL: ${cap_actual:.2f}    ║\n╚{'═'*32}╝\n")
                        s['h'] = []
        time.sleep(15)
    except:
        time.sleep(10); cl = c()
