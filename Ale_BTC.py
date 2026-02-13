import os, time, csv
import pandas as pd
import numpy as np
from binance.client import Client

# --- CONEXIÓN ---
def c(): 
    # Asegúrate de tener tus API Keys configuradas en el sistema
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')) 

try:
    cl = c()
    print("✅ Conexión exitosa con Binance")
except:
    print("❌ Error de conexión. Revisa tus API Keys.")

# --- CONFIGURACIÓN ESTRATÉGICA ---
ms = ['XRPUSDT', 'LINKUSDT', 'SOLUSDT', 'ADAUSDT', 'MATICUSDT', 'DOTUSDT']
FILE_MEMORIA = "memoria_maestra.csv"
cap_inicial = 16.54  # Tu capital de batalla
riesgo_posicion = 0.95 # Usa el 95% para Interés Compuesto

# --- 🧠 MEMORIA Y APRENDIZAJE ---
def gestionar_memoria(moneda="", tipo="", modo="", roi=0, resultado="", leer=False):
    if not os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['fecha', 'moneda', 'tipo', 'modo', 'roi', 'resultado'])
    
    if leer:
        try:
            df = pd.read_csv(FILE_MEMORIA)
            if len(df) < 2: return 1.0, 16.54
            # Factor de riesgo basado en últimas 3 operaciones
            ultimas = df.tail(3)
            fallos = (ultimas['resultado'] == "LOSS").sum()
            factor = 1.4 if fallos >= 2 else 0.8 if fallos == 0 else 1.0
            # Recuperar capital para Interés Compuesto
            ganancia_total = df['roi'].sum() / 100 # Simplificado
            return factor, 16.54 + (16.54 * ganancia_total)
        except: return 1.0, 16.54
    else:
        with open(FILE_MEMORIA, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), moneda, tipo, modo, roi, resultado])

# --- ⚔️ MOTOR DE ANÁLISIS (AJEDREZ Y GUERRA) ---
def analizar_entrada(m, factor):
    try:
        k = cl.get_klines(symbol=m, interval='1m', limit=100)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).astype(float)
        
        # Indicadores Rápidos
        ema35 = df['c'].ewm(span=35).mean().iloc[-1]
        ema200 = df['c'].ewm(span=200).mean().iloc[-1]
        vol_avg = df['v'].tail(15).mean()
        px = df['c'].iloc[-1]
        
        # 1. DETECTAR INYECCIÓN (Ballenas)
        inyeccion = df['v'].iloc[-1] > (vol_avg * 2.5) and df['c'].iloc[-1] > df['o'].iloc[-1]
        
        # 2. PSICOLOGÍA Y POSICIÓN
        distancia_segura = abs(px - ema200) / ema200 < 0.02 # No operar si está demasiado estirado
        
        if inyeccion and px > ema35 and distancia_segura:
            # Calcular X Dinámicas (Max 15x)
            x = int(np.clip(12 / factor, 3, 15))
            return "LONG", "INYECCION", x
            
        return None, None, 0
    except: return None, None, 0

# --- 🚀 BUCLE PRINCIPAL ---
print(f"\n🔱 V40 MASTER QUANTUM | 15X MAX | INTERÉS COMPUESTO")
print(f"--------------------------------------------------")

st = {m: {'e': False, 'p': 0, 't': '', 'max': 0, 'modo': '', 'x': 10} for m in ms}
factor_actual, capital_trabajo = gestionar_memoria(leer=True)

while True:
    try:
        for m in ms:
            s = st[m]
            # Tick de precio rápido
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            
            if not s['e']:
                # MODO FRANCOTIRADOR
                print(f"🔭 Escaneando {m} | Cap: ${capital_trabajo:.2f} | Factor: {factor_actual}x", end='\r')
                tipo, modo, fuerza_x = analizar_entrada(m, factor_actual)
                
                if tipo:
                    s['e'], s['p'], s['t'], s['modo'], s['x'], s['max'] = True, px, tipo, modo, fuerza_x, px
                    print(f"\n⚔️ ¡ATAQUE DETECTADO! {m} | Modo: {modo} | Apalancamiento: {fuerza_x}x")
            
            else:
                # GESTIÓN DE LA POSICIÓN (EL RESORTE)
                roi = ((px - s['p']) / s['p'] * 100 * s['x']) if s['t'] == "LONG" else ((s['p'] - px) / s['p'] * 100 * s['x'])
                roi -= 0.2 # Comisiones
                
                s['max'] = max(s['max'], px) if s['t'] == "LONG" else min(s['max'], px)
                retroceso = abs(s['max'] - px) / s['p'] * 100 * s['x']
                
                print(f"📊 {m} ROI: {roi:.2f}% | Max: {s['max']}", end='\r')

                # Salida por Ganancia (Resorte) o Stop Loss
                if (roi > 0.5 and retroceso > 0.15) or roi <= -1.5:
                    res = "WIN" if roi > 0 else "LOSS"
                    ganancia_usd = (capital_trabajo * (roi / 100))
                    capital_trabajo += ganancia_usd
                    gestionar_memoria(m, s['t'], s['modo'], roi, res)
                    s['e'] = False
                    print(f"\n✅ CIERRE EN {m} | Resultado: {res} | ROI: {roi:.2f}% | Nuevo Cap: ${capital_trabajo:.2f}")
                    factor_actual, _ = gestionar_memoria(leer=True) # Re-calibrar memoria

        time.sleep(0.5)
    except Exception as e:
        time.sleep(2)
