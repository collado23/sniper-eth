import pandas as pd
import time

def analista_maestro_velas(df):
    v = df.iloc[-2]      # Vela cerrada
    v_ant = df.iloc[-3]  # Vela anterior
    cuerpo = abs(v['c'] - v['o'])
    m_sup = v['h'] - max(v['c'], v['o'])
    m_inf = min(v['c'], v['o']) - v['l']
    
    # --- 📔 EL LIBRO COMPLETO DE PATRONES ---
    
    # 1. MARTILLOS (Giro Alcista en piso)
    es_martillo = m_inf > (cuerpo * 2.5) and m_sup < (cuerpo * 0.5)
    es_martillo_inv = m_sup > (cuerpo * 2.5) and m_inf < (cuerpo * 0.5)
    
    # 2. ESTRELLAS Y COLGADOS (Giro Bajista en techo)
    es_estrella_fugaz = es_martillo_inv # Misma forma, cambia el contexto (RSI)
    es_colgado = es_martillo # Misma forma, cambia el contexto (RSI)
    
    # 3. ENVOLVENTES (Fuerza absoluta)
    envolvente_alc = v['c'] > v['o'] and v_ant['c'] < v_ant['o'] and v['c'] > v_ant['o']
    envolvente_baj = v['c'] < v['o'] and v_ant['c'] > v_ant['o'] and v['c'] < v_ant['o']
    
    # 4. HARAMI (Freno de tendencia)
    harami_alc = v_ant['c'] < v_ant['o'] and v['c'] > v['o'] and v['c'] < v_ant['o'] and v['o'] > v_ant['c']

    # --- 🧠 CRUCE CON EMAs Y RSI (Lo que ya teníamos) ---
    ema_corta = df['c'].ewm(span=9).mean().iloc[-1]
    ema_larga = df['c'].ewm(span=21).mean().iloc[-1]
    rsi = calcular_rsi(df) # Función de siempre

    # --- 🎯 DECISIÓN FINAL ---
    # LONG: RSI bajo + EMA Alcista + Patrón del Libro
    if rsi < 40 and ema_corta > ema_larga:
        if es_martillo: return True, "LONG", "MARTILLO"
        if es_martillo_inv: return True, "LONG", "MARTILLO_INV"
        if envolvente_alc: return True, "LONG", "ENVOLVENTE"
        if harami_alc: return True, "LONG", "HARAMI"

    # SHORT: RSI alto + EMA Bajista + Patrón del Libro
    if rsi > 60 and ema_corta < ema_larga:
        if es_estrella_fugaz: return True, "SHORT", "ESTRELLA_FUGAZ"
        if es_colgado: return True, "SHORT", "HOMBRE_COLGADO"
        if envolvente_baj: return True, "SHORT", "ENVOLVENTE_BAJ"

    return False, None, "NORMAL"

# --- 🚀 BUCLE SINCRONIZADO (Cada 15 segundos) ---
while True:
    t_inicio = time.time()
    # 1. Analiza con el libro completo
    # 2. Si entra, usa X dinámicas según la fuerza de la vela
    # 3. Reporta con detalle de ROI y patrón detectado
    
    # Sincronización con Binance (15s)
    time.sleep(max(0, 15 - (time.time() - t_inicio)))
