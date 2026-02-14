import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. MEMORIA DE CAPITAL E HISTORIAL ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77
    if not r: return cap_ini, 10
    hist = r.lrange("historial_bot", 0, -1)
    if leer:
        if not hist: return cap_ini, 10
        cap_act = cap_ini
        for t in reversed(hist):
            tr = json.loads(t)
            cap_act *= (1 + (tr.get('roi', 0) / 100))
        return cap_act, 10 
    else:
        r.lpush("historial_bot", json.dumps(datos))

# --- 📊 2. EL CEREBRO: ANÁLISIS DE OPORTUNIDAD + PROYECCIÓN DE ROI ---
def analizar_con_roi(simbolo, cliente, apalancamiento):
    try:
        klines = cliente.get_klines(symbol=simbolo, interval='5m', limit=100)
        df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','t1','t2','t3','t4','t5','t6'])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)

        # Indicadores de Análisis
        ema9 = df['close'].ewm(span=9, adjust=False).mean()
        ema21 = df['close'].ewm(span=21, adjust=False).mean()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        
        pre_act = df['close'].iloc[-1]

        # 🧠 CÁLCULO DE ROI PROYECTADO
        # Estimamos la ganancia llegando a la EMA21 (Rebote promedio)
        target_precio = ema21.iloc[-1]
        ganancia_estimada_porcentaje = ((target_precio - pre_act) / pre_act) * 100
        roi_proyectado = ganancia_estimada_porcentaje * apalancamiento

        # 🧠 EL PENSAMIENTO DEL BOT:
        
        # Escenario A: Rebote por Pánico (RSI < 35)
        if rsi < 35:
            # ANALIZA EL ROI: Si el ROI proyectado es menor al 1.5%, no vale la pena el riesgo
            if roi_proyectado > 1.5:
                return True, pre_act, f"🐊 ROI POSITIVO: {roi_proyectado:.2f}% | RSI: {rsi:.1f}"
            else:
                return False, pre_act, f"⏳ ROI Pobre ({roi_proyectado:.2f}%). No arriesgo."

        # Escenario B: Tendencia Fuerte
        if ema9.iloc[-1] > ema21.iloc[-1] and rsi < 60:
            if pre_act > ema9.iloc[-1]:
                return True, pre_act, f"🚀 TENDENCIA: ROI Proyectado {roi_proyectado:.2f}%"

        return False, pre_act, f"Analizando... RSI: {rsi:.1f} | ROI: {roi_proyectado:.2f}%"

    except Exception as e:
        return False, 0, f"Error: {e}"

# --- 🚀 3. BUCLE DE OPERACIÓN ---
cap_real, x_act = gestionar_memoria(leer=True)
print(f"🦁 BOT V96 | ANALISTA DE ROI Y OPORTUNIDAD")
print(f"💰 CAPITAL: ${cap_real:.2f} | X: {x_act}")

presas = ['BTCUSDT', 'XRPUSDT', 'SOLUSDT', 'PEPEUSDT', 'ADAUSDT']

while True:
    for p in presas:
        puedo, precio, razon = analizar_con_roi(p, Client(), x_act)
        print(f"🧐 {p}: {razon} | Cap: ${cap_real:.2f}", end='\r')
        
        if puedo:
            print(f"\n🎯 [MUESTRA DE ANALISIS] {p}")
            print(f"📊 {razon}")
            # Aquí el bot dispararía la orden sabiendo exactamente cuánto busca ganar.
            
    time.sleep(10)
