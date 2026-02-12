import os, time
import pandas as pd
from binance.client import Client

# Conexión Ale IA Quantum
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# --- CAPITAL ACTUAL ---
cap_actual = 18.61 
MIN_LOT = 15.0  
st = {m: {'e': False, 'p': 0, 't': '', 'v': '', 'nivel': 0} for m in ms}

def detectar_entrada(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() 
    df['vol_ema'] = df['v'].rolling(10).mean()
    act, ant = df.iloc[-1], df.iloc[-2]
    
    vol_ok = act['v'] > df['vol_ema'].iloc[-1]
    cuerpo = abs(act['close'] - act['open'])
    rango = act['high'] - act['low']
    mecha_ok = cuerpo > (rango * 0.75)
    env = cuerpo > abs(ant['close'] - ant['open'])
    
    if act['close'] > act['open'] and act['close'] > act['ema_9'] and act['ema_9'] > act['ema_27']:
        if env and mecha_ok and vol_ok: return "LONG", "ENVOLVENTE"
    if act['close'] < act['open'] and act['close'] < act['ema_9'] and act['ema_9'] < act['ema_27']:
        if env and mecha_ok and vol_ok: return "SHORT", "ENVOLVENTE"
    return None, None

print(f"🔱 IA QUANTUM V7 | ESCALERA HASTA 20% | CAP: ${cap_actual}")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=50)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close','v']] = df[['open','high','low','close','v']].astype(float)
            px = df['close'].iloc[-1]
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
                
                # --- ESCALERA MAESTRA (0.5% a 20.0%) ---
                # Generamos los niveles automáticamente para no fallar
                niv_cfg = {round(x * 0.5, 1): round((x * 0.5) - 0.4, 2) for x in range(1, 41)}
                # Ajuste manual para el primer nivel (Breakeven)
                niv_cfg[0.5] = 0.10

                # Actualizar Nivel dinámicamente
                for meta in sorted(niv_cfg.keys()):
                    if roi >= meta and meta > s['nivel']:
                        s['nivel'] = meta
                        print(f"\n🛡️ {m} Nivel {meta}% | Piso: {niv_cfg[meta]}% | GAN: ${gan_usd:.2f}")

                # --- LÓGICA DE SALIDAS ---
                
                # 1. Salida por Piso (Breakeven Dinámico)
                if s['nivel'] in niv_cfg:
                    if roi <= niv_cfg[s['nivel']]:
                        cap_actual += gan_usd
                        print(f"\n✅ PISO ASEGURADO N{s['nivel']} | GANASTE: ${gan_usd:.2f} | NETO: ${cap_actual:.2f}")
                        s['e'] = False

                # 2. SALIDA POR GIRO (Confirmación de tendencia)
                elif (s['t'] == "LONG" and px < e27) or (s['t'] == "SHORT" and px > e27):
                    cap_actual += gan_usd
                    print(f"\n🔄 GIRO DETECTADO | PNL: ${gan_usd:.2f} | Buscando nueva entrada...")
                    s['e'] = False

                # 3. STOP LOSS CORTO (-0.7%)
                elif roi <= -0.7:
                    cap_actual += gan_usd
                    print(f"\n❌ SL CORTO | PNL: ${gan_usd:.2f}")
                    s['e'] = False

                emoji = "🟢" if gan_usd >= 0 else "🔴"
                print(f"📊 {m} | {emoji} ${gan_usd:.2f} ({roi:.2f}%) | NIV: {s['nivel']}", end='\r')

            time.sleep(1)
            del df
    except Exception as e:
        time.sleep(5); cl = c()
