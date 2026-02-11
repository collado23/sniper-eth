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
    # Análisis sobre 30 velas para estabilidad
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
    df['ema_35'] = df['close'].ewm(span=35, adjust=False).mean()
    df['vel'] = df['close'].diff()
    df['acel'] = df['vel'].diff()
    # Volatilidad basada en 30 velas
    df['rango'] = df['high'] - df['low']
    df['z_score'] = (df['rango'] - df['rango'].rolling(30).mean()) / df['rango'].rolling(30).std()
    return df

def ni(df):
    act = df.iloc[-1]; prev = df.iloc[-2]; ant = df.iloc[-3]
    
    # Lógica de Color (C: Verde, V: Roja)
    actual_verde = act['close'] > act['open']
    actual_roja = act['close'] < act['open']
    prev_verde = prev['close'] > prev['open']
    prev_roja = prev['close'] < prev['open']
    
    cuerpo = abs(act['close'] - act['open']) or 0.001
    l_ok = (act['close'] > act['ema_200']) 
    s_ok = (act['close'] < act['ema_200'])
    
    # GATILLO LONG: Necesitamos vela alta + confirmación de color verde
    m_inf = act['open'] - act['low'] if actual_verde else act['close'] - act['low']
    # Entra si: Es Martillo O si vienen 2 verdes fuertes superando la anterior
    if l_ok and actual_verde and prev_verde:
        if (m_inf > cuerpo * 3.0) or (act['close'] > prev['high'] and act['acel'] > 0):
            if act['z_score'] < 1.4: return "🔨" # Confirmado: Viene más verde

    # GATILLO SHORT: Necesitamos vela alta + confirmación de color rojo
    m_sup = act['high'] - act['close'] if actual_verde else act['high'] - act['open']
    if s_ok and actual_roja and prev_roja:
        if (m_sup > cuerpo * 2.5) or (act['close'] < prev['low'] and act['acel'] < 0):
            if act['z_score'] < 1.4: return "☄️" # Confirmado: Viene más rojo
            
    return "."

print(f"🔱 PREDICTOR DE COLOR ON | 30 VELAS | CAP: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=150)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            df = calcular_cerebro(df)
            px = df['close'].iloc[-1]
            ptr = ni(df)

            if not s['e']:
                if ptr != ".":
                    s['t'] = "LONG" if ptr == "🔨" else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 CONFIRMADO {m} {s['t']} | CAP: ${cap_actual:.2f}")
            else:
                df_p = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df_p * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                
                # Blindaje rápido para no perder más
                if roi >= 0.06: s['b'] = True 
                t_stop = (roi <= (s['m'] - 0.06)) if s['m'] >= 0.18 else False
                sl_micro = roi <= -0.25

                if (s['b'] and roi <= 0.01) or t_stop or sl_micro:
                    gan = (cap_actual * (roi / 100))
                    cap_actual += gan
                    s['o'] += 1; s['e'] = False
                    est = "✅" if roi > 0 else "❌"
                    s['h'].append(f"{est} {s['t']} {roi:.2f}%")
                    print(f"\n{est} SALIDA {m} {roi:.2f}% | CAP: ${cap_actual:.2f}")

                    if s['o'] % 5 == 0:
                        print(f"\n╔{'═'*32}╗\n║ 📊 REPORTE 5 OPS - {m[:3]} ║")
                        for line in s['h']: print(f"║ {line.ljust(28)} ║")
                        print(f"╠{'═'*32}╣\n║ CAP FINAL: ${cap_actual:.2f}   ║\n╚{'═'*32}╝\n")
                        s['h'] = []
        time.sleep(15)
    except:
        time.sleep(10); cl = c()
