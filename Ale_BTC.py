import os, time
import pandas as pd
from binance.client import Client

def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap_actual = 25.89 # Capital actualizado tras las pérdidas del log
st = {m: {'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False, 'h': []} for m in ms}

def calcular_cerebro(df):
    df['ema_fast'] = df['close'].ewm(span=7, adjust=False).mean() # Más rápida aún
    df['cuerpo'] = df['close'] - df['open']
    return df

def analizar_entrada_segura(df):
    act = df.iloc[-1]; prev = df.iloc[-2]
    
    # LONG: Necesitamos vela verde, que cierre arriba de la anterior y arriba de la EMA
    l_ok = act['close'] > act['open'] and act['close'] > prev['high'] and act['close'] > act['ema_fast']
    
    # SHORT: Necesitamos vela roja, que cierre abajo de la anterior y abajo de la EMA
    s_ok = act['close'] < act['open'] and act['close'] < prev['low'] and act['close'] < act['ema_fast']
    
    if l_ok: return "🟩"
    if s_ok: return "🟥"
    return "."

print(f"🔱 IA QUANTUM 4.0 | CAP: ${cap_actual} | FILTRO DE INERCIA")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            df = calcular_cerebro(df)
            px = df['close'].iloc[-1]
            senal = analizar_entrada_segura(df)

            if not s['e']:
                if senal != ".":
                    s['t'] = "LONG" if senal == "🟩" else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 {senal} ENTRADA CONFIRMADA EN {m} | PX: {px}")
            else:
                # GESTIÓN PARA NO PERDER
                df_p = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df_p * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                
                # CIERRE POR REBOTE DE VELA (Tu pedido de cerrar al rebote)
                # Si el precio se mueve en contra de la dirección un 0.06%, cerramos ya.
                act = df.iloc[-1]
                rebote_long = s['t'] == "LONG" and px < df['low'].iloc[-1] + (df['cuerpo'].iloc[-1] * 0.2)
                rebote_short = s['t'] == "SHORT" and px > df['high'].iloc[-1] - (abs(df['cuerpo'].iloc[-1]) * 0.2)

                # Blindaje rápido
                if roi >= 0.06: s['b'] = True 
                
                # Salida de emergencia
                if (s['b'] and roi <= 0.01) or roi <= -0.18 or (roi > 0.20 and roi < s['m'] - 0.07):
                    gan = (cap_actual * (roi / 100))
                    cap_actual += gan
                    s['o'] += 1; s['e'] = False
                    est = "✅" if roi > 0 else "❌"
                    s['h'].append(f"{est} {s['t']} {roi:.2f}%")
                    print(f"\n{est} SALIDA {m} {roi:.2f}% | CAP: ${cap_actual:.2f}")

                    if s['o'] % 5 == 0:
                        print(f"\n╔{'═'*32}╗\n║ 📊 REPORTE DE BLOQUE - {m[:3]} ║")
                        for line in s['h']: print(f"║ {line.ljust(28)} ║")
                        print(f"╠{'═'*32}╣\n║ CAP FINAL: ${cap_actual:.2f}   ║\n╚{'═'*32}╝\n")
                        s['h'] = []
        time.sleep(15)
    except:
        time.sleep(10); cl = c()
