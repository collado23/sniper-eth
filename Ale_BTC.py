import os, time
import pandas as pd
from binance.client import Client

def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap_actual = 28.01 
st = {m: {'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False, 'h': []} for m in ms}

def calcular_cerebro(df):
    # Análisis de 30 velas pero con EMAs rápidas (9 y 21) para entrar antes
    df['ema_fast'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=21, adjust=False).mean()
    df['rango'] = df['high'] - df['low']
    # Z-Score más permisivo (1.8) para que no sea tan "tímido"
    df['z_score'] = (df['rango'] - df['rango'].rolling(30).mean()) / df['rango'].rolling(30).std()
    return df

def predictor_color_veloz(df):
    act = df.iloc[-1]; prev = df.iloc[-2]
    
    v1 = act['close'] > act['open'] # Verde
    r1 = act['close'] < act['open'] # Roja
    
    # GATILLO VELOZ: Solo pide que la vela actual tenga el color y cruce la EMA
    # LONG: Si la vela es verde y está por encima de la media rápida
    if v1 and (act['close'] > act['ema_fast']) and (act['z_score'] < 1.8):
        return "🟩"

    # SHORT: Si la vela es roja y está por debajo de la media rápida
    if r1 and (act['close'] < act['ema_fast']) and (act['z_score'] < 1.8):
        return "🟥"
            
    return "."

print(f"🔱 MODO VELOCIDAD QUANTUM | CAP: ${cap_actual} | 10s")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=100)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            df = calcular_cerebro(df)
            px = df['close'].iloc[-1]
            senal = predictor_color_veloz(df)

            if not s['e']:
                if senal != ".":
                    s['t'] = "LONG" if senal == "🟩" else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 {senal} GATILLO RÁPIDO {m} | PX: {px}")
            else:
                # GESTIÓN DE SALIDA DE ALTA VELOCIDAD
                df_p = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df_p * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                
                # Blindaje instantáneo (apenas toque positivo, protege)
                if roi >= 0.04: s['b'] = True 
                
                # Trailing Stop muy corto (0.04) para cerrar en el pico
                t_stop = (roi <= (s['m'] - 0.04)) if s['m'] >= 0.12 else False
                sl_micro = roi <= -0.22 # Stop loss cortito

                if (s['b'] and roi <= 0.01) or t_stop or sl_micro:
                    gan = (cap_actual * (roi / 100))
                    cap_actual += gan
                    s['o'] += 1; s['e'] = False
                    est = "✅" if roi > 0 else "❌"
                    s['h'].append(f"{est} {s['t']} {roi:.2f}%")
                    print(f"\n{est} SALIDA {m} {roi:.2f}% | NETO: ${cap_actual:.2f}")

                    if s['o'] % 5 == 0:
                        print(f"\n╔{'═'*32}╗\n║ 📊 REPORTE VELOZ - {m[:3]}    ║")
                        for line in s['h']: print(f"║ {line.ljust(28)} ║")
                        print(f"╠{'═'*32}╣\n║ SALDO: ${cap_actual:.2f}         ║\n╚{'═'*32}╝\n")
                        s['h'] = []
        time.sleep(10) # Bajamos a 10 segundos para más rapidez
    except:
        time.sleep(5); cl = c()
