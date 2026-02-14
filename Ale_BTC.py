import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA Y GESTIÓN DE CAPITAL ---
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

# --- 💰 2. MONITOR DE OPERACIÓN EN VIVO (P&L) ---
def monitorear_pnl(simbolo, lado, precio_entrada, x, cap_usado):
    print(f"\n🔥 [ORDEN EJECUTADA] {simbolo} | {lado} | Precio: {precio_entrada}")
    
    while True:
        try:
            # Consultamos precio actual para calcular ganancia
            ticker = Client().get_symbol_ticker(symbol=simbolo)
            precio_actual = float(ticker['price'])
            
            # Cálculo de ROI según la dirección
            if lado == "LONG":
                roi = ((precio_actual - precio_entrada) / precio_entrada) * 100 * x
            else: # SHORT
                roi = ((precio_entrada - precio_actual) / precio_entrada) * 100 * x
            
            ganancia_usd = cap_usado * (roi / 100)
            
            # Reporte en pantalla
            color = "🟢" if roi > 0 else "🔴"
            print(f"📊 {simbolo} {lado}: {color} ROI: {roi:.2f}% | Ganancia: ${ganancia_usd:.2f}    ", end='\r')

            # --- LÓGICA DE SALIDA (Ajustable) ---
            if roi >= 1.5: # Take Profit al 1.5%
                print(f"\n✅ [VENTA] Objetivo alcanzado. Ganaste ${ganancia_usd:.2f}")
                return roi
            if roi <= -1.2: # Stop Loss al 1.2%
                print(f"\n❌ [CIERRE] Stop Loss tocado. Pérdida: ${ganancia_usd:.2f}")
                return roi
                
            time.sleep(3) # Actualización rápida del P&L
        except:
            continue

# --- 📊 3. CEREBRO ANALISTA (X Dinámicas) ---
def cerebro_analista(simbolo, cliente, racha):
    try:
        klines = cliente.get_klines(symbol=simbolo, interval='5m', limit=50)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i'])
        df['close'] = pd.to_numeric(df['c'])
        
        # Indicadores
        ema9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = df['close'].ewm(span=21, adjust=False).mean().iloc[-1]
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        pre_act = df['close'].iloc[-1]

        # Análisis de X (Dinámicas)
        x_sugerida = int(min(15, 5 + abs(50 - rsi) * 0.5))
        if racha > 0: x_sugerida = max(1, x_sugerida - (racha * 3))

        # Decisiones
        if rsi < 34 or (ema9 > ema21 and rsi < 55):
            return True, "LONG", pre_act, x_sugerida, f"Subida (RSI: {rsi:.1f})"
        if rsi > 66 or (ema9 < ema21 and rsi > 45):
            return True, "SHORT", pre_act, x_sugerida, f"Caída (RSI: {rsi:.1f})"

        return False, None, pre_act, 0, f"RSI: {rsi:.1f}"
    except: return False, None, 0, 0, "Analizando..."

# --- 🚀 4. EJECUCIÓN MAESTRA ---
cap_actual, racha_actual = gestionar_memoria(leer=True)
print(f"🦁 BOT V102 | ANALISTA CON REPORTE DE GANANCIAS | Cap: ${cap_actual:.2f}")

presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT']

while True:
    for p in presas:
        puedo, lado, precio, x_fin, razon = cerebro_analista(p, Client(), racha_actual)
        print(f"🧐 {p}: {razon} | Cap: ${cap_actual:.2f}   ", end='\r')
        
        if puedo:
            # Aquí se ejecutaría la orden real en Binance
            # Usamos el 50% del capital por operación para seguridad
            monto_operar = cap_actual * 0.5
            
            # Iniciamos seguimiento en vivo
            resultado_roi = monitorear_pnl(p, lado, precio, x_fin, monto_operar)
            
            # Guardamos resultado en Redis para el interés compuesto
            gestionar_memoria(False, {'m': p, 'roi': resultado_roi, 'res': 'WIN' if resultado_roi > 0 else 'LOSS'})
            
            # Actualizamos capital local para el siguiente ciclo
            cap_actual, racha_actual = gestionar_memoria(leer=True)
            print(f"\n💰 Nuevo Capital: ${cap_actual:.2f}. Volviendo a acechar...")

    time.sleep(15)
