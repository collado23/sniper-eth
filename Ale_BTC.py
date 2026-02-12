import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de cuenta
cap_actual = 19.27 
MIN_LOT = 15.0 # El valor nominal de tu posición (Margin x Apalancamiento)
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'nivel': 0} for m in ms}

def detectar_entrada(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    act = df.iloc[-1]
    ant = df.iloc[-2]
    
    cuerpo = abs(act['close'] - act['open'])
    rango_total = act['high'] - act['low']
    mecha_ok = cuerpo > (rango_total * 0.6)
    envolvente = cuerpo > abs(ant['close'] - ant['open'])
    distancia_ema = abs(act['close'] - act['ema_9']) / act['ema_9']
    cerca_ema = distancia_ema < 0.003

    if act['close'] > act['open'] and act['close'] > act['ema_9'] and act['ema_9'] > act['ema_27']:
        if envolvente and mecha_ok and cerca_ema:
            return "LONG", "ENVOLVENTE PURA"
            
    if act['close'] < act['open'] and act['close'] < act['ema_9'] and act['ema_9'] < act['ema_27']:
        if envolvente and mecha_ok and cerca_ema:
            return "SHORT", "ENVOLVENTE PURA"
            
    return None, None

print(f"🔱 IA QUANTUM V2 | CAP INICIAL: ${cap_actual} | LOTE: ${MIN_LOT}")

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
                    print(f"\n🚀 {m} | ENTRADA {dir} en {px_actual}")
            
            elif s['e']:
                # Cálculo de ROI Neto (x10 palanca - comisión)
                diff = (px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']
                roi = (diff * 100 * 10) - 0.22
                
                # CÁLCULO DE GANANCIA/PÉRDIDA EN DÓLARES (PNL)
                pnl_usd = (MIN_LOT * (roi / 100))
                
                # --- ESCALERA DE BLINDAJE ---
                niv_cfg = {
                    1: (1.2, 0.2), 2: (2.0, 1.2), 3: (2.5, 2.0), 4: (3.5, 2.5),
                    5: (4.0, 3.5), 6: (4.5, 4.0), 7: (5.0, 4.5), 8: (5.5, 5.0),
                    9: (6.0, 5.5), 10: (6.5, 6.0), 11: (7.0, 6.5), 12: (8.0, 7.5),
                    13: (8.5, 8.0), 14: (9.5, 9.0), 15: (10.0, 9.5)
                }

                for n, (meta, piso) in niv_cfg.items():
                    if roi >= meta and s['nivel'] < n:
                        s['nivel'] = n
                        print(f"\n🛡️ {m} SUBIÓ A NIVEL {n} | PNL: ${pnl_usd:.2f}")

                # Salida por Protección (Piso)
                if s['nivel'] in niv_cfg:
                    if roi <= niv_cfg[s['nivel']][1]:
                        cap_actual += pnl_usd
                        print(f"\n✅ SALIDA PROTEGIDA {m} | GANANCIA: ${pnl_usd:.2f} | CAP TOTAL: ${cap_actual:.2f}")
                        s['e'] = False

                # Stop Loss Dinámico (Evita perder más de lo debido)
                elif roi <= -1.8: 
                    cap_actual += pnl_usd
                    print(f"\n❌ STOP LOSS {m} | PÉRDIDA: ${pnl_usd:.2f} | CAP TOTAL: ${cap_actual:.2f}")
                    s['e'] = False

                # Imprimir estado actual en pantalla (PNL en USD incluido)
                color = "🟢" if pnl_usd >= 0 else "🔴"
                print(f"📊 {m} | {color} PNL: ${pnl_usd:.2f} ({roi:.2f}%) | Nivel: {s['nivel']} | Px: {px_actual}", end='\r')

            time.sleep(1)
            del df
    except Exception as e:
        print(f"\n⚠️ Error de conexión: {e}")
        time.sleep(5); cl = c()
