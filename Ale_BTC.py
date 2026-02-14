import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA DE CAPITAL (Redis) ---
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
    else:
        r.lpush("historial_bot", json.dumps(datos))

# --- 💰 2. MONITOR DE OPERACIÓN (G y P) ---
def monitorear_pnl(simbolo, lado, precio_entrada, x, cap_usado):
    print(f"\n🚀 [ENTRADA] {simbolo} | {lado} | {x}x")
    
    while True:
        try:
            ticker = Client().get_symbol_ticker(symbol=simbolo)
            precio_act = float(ticker['price'])
            
            # Cálculo de ROI
            if lado == "LONG":
                roi = ((precio_act - precio_entrada) / precio_entrada) * 100 * x
            else: # SHORT
                roi = ((precio_entrada - precio_act) / precio_entrada) * 100 * x
            
            valor_pnl = cap_usado * (roi / 100)
            status = "🟢" if roi >= 0 else "🔴"
            
            # REPORTE ACORTADO: G (Ganancia) / P (Pérdida)
            tipo_res = "G" if roi >= 0 else "P"
            print(f"📊 {simbolo} {lado} ({x}x) | {status} {tipo_res}: ${abs(valor_pnl):.2f} ({roi:.2f}%)      ", end='\r')

            # Salidas automáticas
            if roi >= 1.6:
                print(f"\n✅ [VENTA G] +${valor_pnl:.2f} (ROI: {roi:.2f}%)")
                return roi
            if roi <= -1.3:
                print(f"\n❌ [CIERRE P] -${abs(valor_pnl):.2f} (ROI: {roi:.2f}%)")
                return roi
                
            time.sleep(5)
        except: continue

# --- 📊 3. CEREBRO ANALISTA ---
def cerebro_analista(simbolo, cliente, racha):
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

        # DIRECCIONES
        if rsi < 34 or (ema9 > ema21 and rsi < 55):
            return True, "LONG", pre_act, x_analizadas, f"RSI: {rsi:.1f}"
        if rsi > 66 or (ema9 < ema21 and rsi > 45):
            return True, "SHORT", pre_act, x_analizadas, f"RSI: {rsi:.1f}"

        return False, None, pre_act, 0, f"RSI: {rsi:.1f}"
    except: return False, None, 0, 0, "Analizando..."

# --- 🚀 4. BUCLE MAESTRO ---
cap, racha = gestionar_memoria(leer=True)
print(f"🦁 BOT V104 | MODO G/P ACTIVADO | Cap: ${cap:.2f}")

presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT']

while True:
    for p in presas:
        puedo, lado, precio, x_final, info = cerebro_analista(p, Client(), racha)
        print(f"🧐 {p}: {info} | Cap: ${cap:.2f}    ", end='\r')
        
        if puedo:
            # Operamos con el 50% del capital para tener margen
            monto = cap * 0.5
            res_roi = monitorear_pnl(p, lado, precio, x_final, monto)
            
            # Guardar en memoria
            gestionar_memoria(False, {'m': p, 'roi': res_roi, 'res': 'WIN' if res_roi > 0 else 'LOSS'})
            
            # Recargar capital
            cap, racha = gestionar_memoria(leer=True)
            print(f"\n💰 Cap Actual: ${cap:.2f}")

    time.sleep(15)
