import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA Y CAPITAL ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77
    if not r: return cap_ini, 0
    hist = r.lrange("historial_bot", 0, -1)
    if leer:
        if not hist: return cap_ini, 0
        cap_act = cap_ini
        racha = 0
        for t in reversed(hist):
            tr = json.loads(t)
            cap_act *= (1 + (tr.get('roi', 0) / 100))
            racha = racha + 1 if tr.get('res') == "LOSS" else 0
        return cap_act, racha
    else: r.lpush("historial_bot", json.dumps(datos))

# --- 📊 2. CEREBRO ANALISTA ---
def analizar(simbolo, cliente, racha):
    try:
        klines = cliente.get_klines(symbol=simbolo, interval='5m', limit=50)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i'])
        df['close'] = pd.to_numeric(df['c'])
        
        ema9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = df['close'].ewm(span=21, adjust=False).mean().iloc[-1]
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        pre_act = df['close'].iloc[-1]

        # X DINÁMICAS
        x_analizadas = int(min(15, 5 + abs(50 - rsi) * 0.6))
        if racha > 0: x_analizadas = max(1, x_analizadas - (racha * 2))

        if rsi < 34 or (ema9 > ema21 and rsi < 55): return True, "LONG", pre_act, x_analizadas, rsi
        if rsi > 66 or (ema9 < ema21 and rsi > 45): return True, "SHORT", pre_act, x_analizadas, rsi

        return False, None, pre_act, 0, rsi
    except: return False, None, 0, 0, 0

# --- 🚀 3. BUCLE MAESTRO (DOBLE OPERACIÓN) ---
cap, racha = gestionar_memoria(leer=True)
operaciones = [] # Lista para manejar hasta 2 compras
print(f"🦁 BOT V106 | DOBLE MORDIDA | Cap: ${cap:.2f}")

presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT', 'ETHUSDT']

while True:
    # A. MONITOREAR OPERACIONES ACTIVAS (G/P)
    for op in operaciones[:]:
        try:
            ticker = Client().get_symbol_ticker(symbol=op['s'])
            p_act = float(ticker['price'])
            roi = ((p_act - op['p'])/op['p'])*100*op['x'] if op['l']=="LONG" else ((op['p'] - p_act)/op['p'])*100*op['x']
            gan_usd = op['c'] * (roi / 100)
            
            status = "🟢 G" if roi >= 0 else "🔴 P"
            print(f"📊 {op['s']} {op['l']} ({op['x']}x) | {status}: ${abs(gan_usd):.2f} ({roi:.2f}%)")

            if roi >= 1.6 or roi <= -1.3:
                print(f"\n✅ CIERRE {op['s']} | ROI: {roi:.2f}%")
                gestionar_memoria(False, {'m': op['s'], 'roi': roi, 'res': 'WIN' if roi > 0 else 'LOSS'})
                operaciones.remove(op)
                cap, racha = gestionar_memoria(leer=True)
        except: continue

    # B. ANALIZAR EL RESTO (Incluso si hay una abierta)
    if len(operaciones) < 2: # Solo busca si hay menos de 2 abiertas
        for p in presas:
            # No analizar lo que ya compramos
            if any(o['s'] == p for o in operaciones): continue
            
            puedo, lado, precio, x_f, rsi_f = analizar(p, Client(), racha)
            
            if puedo:
                print(f"\n🎯 [MUESTRA]: {p} analizada {lado} con {x_f}x")
                # Dividimos el capital: usa el 40% del capital actual para cada una
                monto_op = cap * 0.4 
                operaciones.append({'s': p, 'l': lado, 'p': precio, 'x': x_f, 'c': monto_op})
                if len(operaciones) >= 2: break 

            print(f"🧐 Analizando {p}... RSI: {rsi_f:.1f}   ", end='\r')

    time.sleep(15)
