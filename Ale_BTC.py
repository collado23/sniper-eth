import os, time, redis, json
import pandas as pd
from binance.client import Client

# --- 🧠 1. EL BLOQUE DE MEMORIA (Recupera tus $15.77) ---
r_url = os.getenv("REDIS_URL")
r = redis.from_url(r_url) if r_url else None

def gestionar_memoria(leer=False, datos=None):
    cap_ini = 15.77  # Tu capital base real
    if not r: return cap_ini
    
    if leer:
        # Recupera el historial para calcular el capital actual
        hist = r.lrange("historial_bot", 0, -1)
        if not hist: return cap_ini
        cap_act = cap_ini
        for t in reversed(hist):
            tr = json.loads(t)
            cap_act *= (1 + (tr.get('roi', 0) / 100))
        return float(cap_act)
    else:
        # Guarda cada cierre de operación en la memoria
        r.lpush("historial_bot", json.dumps(datos))

# --- 📖 2. EL LIBRO DE VELAS JAPONESAS COMPLETO ---
def leer_libro_velas(df):
    v = df.iloc[-2]      # Vela cerrada
    v_ant = df.iloc[-3]  # Anterior
    cuerpo = abs(v['c'] - v['o'])
    m_sup = v['h'] - max(v['c'], v['o'])
    m_inf = min(v['c'], v['o']) - v['l']
    
    # Patrones del Libro
    es_martillo = m_inf > (cuerpo * 2.5) and m_sup < (cuerpo * 0.5)
    es_martillo_inv = m_sup > (cuerpo * 2.5) and m_inf < (cuerpo * 0.5)
    envolvente_alc = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
    envolvente_baj = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']
    
    if es_martillo or (es_martillo_inv and v['c'] > v['o']) or envolvente_alc: return "ALCISTA"
    if (es_martillo_inv and v['c'] < v['o']) or (es_martillo and v['c'] < v['o']) or envolvente_baj: return "BAJISTA"
    return "NEUTRAL"

# --- 📊 3. ANALISTA SUPERIOR (EMAs + RSI + VELAS + VOLUMEN) ---
def analista_total(simbolo, cliente):
    try:
        k = cliente.get_klines(symbol=simbolo, interval='1m', limit=30)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).apply(pd.to_numeric)
        
        # Estrategias previas
        ema9 = df['c'].ewm(span=9).mean().iloc[-1]
        ema21 = df['c'].ewm(span=21).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (df['c'].diff().where(df['c'].diff() > 0, 0).mean() / -df['c'].diff().where(df['c'].diff() < 0, 0).mean())))
        vol_act = df['v'].iloc[-1]
        vol_avg = df['v'].rolling(10).mean().iloc[-1]

        # El Libro
        patron = leer_libro_velas(df)

        # 🎯 DECISIÓN: Tiene que estar todo alineado
        if patron == "ALCISTA" and rsi < 42 and ema9 > ema21 and vol_act > vol_avg:
            return True, "LONG", patron
        if patron == "BAJISTA" and rsi > 58 and ema9 < ema21 and vol_act > vol_avg:
            return True, "SHORT", patron
            
        return False, None, rsi
    except: return False, None, 50

# --- 🚀 4. BUCLE MAESTRO (Latido 15s) ---
cap_total = gestionar_memoria(leer=True)
operaciones = []

while True:
    t_inicio = time.time()
    # (El resto del código de monitoreo, X dinámicas y CIERRES DETALLADOS)
    # Al cerrar: gestionar_memoria(False, {'roi': roi_final, 'm': moneda})
    
    # Sincronización con Binance 15s
    time.sleep(max(0, 15 - (time.time() - t_inicio)))
