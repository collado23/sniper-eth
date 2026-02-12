import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado de cuenta (Neto según tu último log)
cap_actual = 19.27 
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

print(f"🔱 IA QUANTUM: ESCALERA EXTENDIDA (N15) | NETO: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px_actual = df['close'].iloc[-1]
            
            # Cálculo de EMAs para re-entrada
            ema_data = df['close'].ewm(span=9, adjust=False).mean()
            e9 = ema_data.iloc[-1]
            e27 = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]
            
            if not s['e']:
                dir, vela = detectar_entrada(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'], s['nivel'] = dir, px_actual, True, vela, 0
                    print(f"\n🚀 {m} | DISPARO: {dir} en {px_actual} ({vela})")
            
            elif s['e']:
                # ROI Neto (Ajustado x10 y comisión)
                roi = (((px_actual - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px_actual) / s['p']) * 100 * 10) - 0.22
                
                # --- ESCALERA DE BLINDAJE EXTENDIDA (N1 a N15) ---
                niveles_config = {
                    1: (1.2, 0.2), 2: (2.0, 1.2), 3: (2.5, 2.0), 4: (3.5, 2.5),
                    5: (4.0, 3.5), 6: (4.5, 4.0), 7: (5.0, 4.5), 8: (5.5, 5.0),
                    9: (6.0, 5.5), 10: (6.5, 6.0), 11: (7.0, 6.5), 12: (8.0, 7.5),
                    13: (8.5, 8.0), 14: (9.5, 9.0), 15: (10.0, 9.5)
                }

                # Actualización de Nivel
                for n, (meta, piso) in niveles_config.items():
                    if roi >= meta and s['nivel'] < n:
                        s['nivel'] = n
                        print(f"\n🛡️ {m} Nivel {n} alcanzado! Meta {meta}% -> Piso {piso}%")

                # --- CONTROL DE RETROCESOS ---
                if s['nivel'] in niveles_config:
                    piso_actual = niveles_config[s['nivel']][1]
                    if roi <= piso_actual:
                        ganancia = (MIN_LOT * (roi / 100))
                        cap_actual += ganancia
                        print(f"\n💰 SALIDA PROTEGIDA N{s['nivel']} en {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")
                        
                        # Lógica de Re-entrada inmediata si la tendencia es fuerte
                        if (s['t'] == "LONG" and e9 > e27) or (s['t'] == "SHORT" and e9 < e27):
                            s['p'], s['nivel'] = px_actual, 0
                            print(f"🔄 Manteniendo tendencia, re-ajustando entrada...")
                        else: 
                            s['e'] = False

                # COSECHA FINAL (Por encima de Nivel 15)
                elif roi >= 10.5:
                    ganancia = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia
                    print(f"\n👑 COSECHA MÁXIMA 10.5% en {m} | NETO: ${cap_actual:.2f}")
                    s['e'] = False

                # STOP LOSS / GIRO (-3%)
                elif roi <= -3.0:
                    cap_actual += (MIN_LOT * (roi / 100))
                    nueva_dir = "SHORT" if s['t'] == "LONG" else "LONG"
                    print(f"\n🔄 GIRO {m}: SL 3% tocado. Entrando en {nueva_dir}")
                    s['t'], s['p'], s['nivel'] = nueva_dir, px_actual, 0

                print(f"📊 {m} | ROI: {roi:.2f}% | Nivel: {s['nivel']} | Px: {px_actual}", end='\r')

            time.sleep(1)
            del df
    except Exception as e:
        print(f"\n⚠️ Error: {e}")
        time.sleep(5)
        cl = c()
