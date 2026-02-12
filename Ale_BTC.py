import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')) 

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# --- CAPITAL ACTUALIZADO SEGÚN LOG ---
cap_actual = 18.17 
MIN_LOT = 15.0  
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'nivel': 0} for m in ms}

def detectar_entrada(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    df['vol_ema'] = df['v'].rolling(10).mean()
    
    act = df.iloc[-1]
    ant = df.iloc[-2]
    
    vol_ok = act['v'] > df['vol_ema'].iloc[-1]
    cuerpo = abs(act['close'] - act['open'])
    rango = act['high'] - act['low']
    mecha_ok = cuerpo > (rango * 0.75) # Más sólido todavía
    env = cuerpo > abs(ant['close'] - ant['open'])
    
    # LONG
    if act['close'] > act['open'] and act['close'] > act['ema_9'] and act['ema_9'] > act['ema_27']:
        if env and mecha_ok and vol_ok: return "LONG", "ENVOLVENTE"
    # SHORT
    if act['close'] < act['open'] and act['close'] < act['ema_9'] and act['ema_9'] < act['ema_27']:
        if env and mecha_ok and vol_ok: return "SHORT", "ENVOLVENTE"
            
    return None, None

print(f"🔱 IA QUANTUM V4 | SL QUIRÚRGICO: 0.8% | GIRO ACTIVO | CAP: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
            px = df['close'].iloc[-1]
            
            e9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
            e27 = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]
            
            if not s['e']:
                dir, vela = detectar_entrada(df)
                if dir:
                    s['t'], s['p'], s['e'], s['v'], s['nivel'] = dir, px, True, vela, 0
                    print(f"\n🚀 {m} | ENTRADA {dir} | Px: {px}")
            
            elif s['e']:
                diff = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (diff * 100 * 10) - 0.22
                gan_usd = (MIN_LOT * (roi / 100))
                
                # ESCALERA AGRESIVA
                niv_cfg = {0.5: (0.5, 0.1), 1: (1.2, 0.5), 2: (2.0, 1.2), 3: (3.0, 2.0)}

                for n, (meta, piso) in niv_cfg.items():
                    if roi >= meta and s['nivel'] < n:
                        s['nivel'] = n
                        print(f"\n🛡️ {m} N{n} Bloqueado")

                # --- LÓGICA DE SALIDAS Y GIRO ---
                
                # 1. Salida por Piso
                if s['nivel'] in niv_cfg and roi <= niv_cfg[s['nivel']][1]:
                    cap_actual += gan_usd
                    print(f"\n✅ CIERRE PISO N{s['nivel']} | PNL: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False

                # 2. SALIDA POR CRUCE + GIRO (FLIP)
                elif (s['t'] == "LONG" and px < e27) or (s['t'] == "SHORT" and px > e27):
                    cap_actual += gan_usd
                    nueva_dir = "SHORT" if s['t'] == "LONG" else "LONG"
                    print(f"\n🔄 GIRO DE TENDENCIA en {m} | PNL: ${gan_usd:.2f} | NUEVA: {nueva_dir}")
                    # Giramos la posición inmediatamente
                    s['t'], s['p'], s['nivel'] = nueva_dir, px, 0

                # 3. STOP LOSS CORTO (0.8%)
                elif roi <= -0.8:
                    cap_actual += gan_usd
                    print(f"\n❌ SL CORTO | PNL: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                    s['e'] = False

                emoji = "🟢" if gan_usd >= 0 else "🔴"
                print(f"📊 {m} | {emoji} PNL: ${gan_usd:.2f} ({roi:.2f}%) | Nivel: {s['nivel']}", end='\r')

            time.sleep(1)
            del df
    except Exception as e:
        time.sleep(5); cl = c()
