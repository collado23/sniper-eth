import os, time, csv
import pandas as pd
import numpy as np
from binance.client import Client

# --- CONEXIÓN ---
def c(): 
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

try:
    cl = c()
    print("✅ Conexión establecida. Sistema de Armas Online.")
except:
    print("❌ Error de conexión. Revisa tus API Keys.")

# --- CONFIGURACIÓN ESTRATÉGICA ---
ms = ['XRPUSDT', 'LINKUSDT', 'SOLUSDT', 'ADAUSDT', 'MATICUSDT', 'DOTUSDT']
FILE_MEMORIA = "memoria_maestra.csv"
cap_inicial = 16.54  
riesgo_posicion = 0.95 

# --- 🧠 MEMORIA, APRENDIZAJE Y RANGOS ---
def gestionar_memoria(moneda="", tipo="", modo="", roi=0, resultado="", leer=False):
    if not os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['fecha', 'moneda', 'tipo', 'modo', 'roi', 'resultado'])
    
    if leer:
        try:
            df = pd.read_csv(FILE_MEMORIA)
            if len(df) < 2: return 1.0, cap_inicial, "⚔️ FRANCOTIRADOR"
            
            # Analizar últimas 3 batallas para definir RANGO
            ultimas = df.tail(3)
            fallos = (ultimas['resultado'] == "LOSS").sum()
            ganancias = (ultimas['resultado'] == "WIN").sum()
            
            if fallos >= 2: 
                return 1.4, cap_inicial + (df['roi'].sum() * 0.016), "🛡️ DEFENSIVO"
            elif ganancias >= 2: 
                return 0.8, cap_inicial + (df['roi'].sum() * 0.016), "🔥 BERSERKER"
            else:
                return 1.0, cap_inicial + (df['roi'].sum() * 0.016), "⚔️ FRANCOTIRADOR"
        except: return 1.0, cap_inicial, "⚔️ FRANCOTIRADOR"
    else:
        with open(FILE_MEMORIA, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), moneda, tipo, modo, roi, resultado])

# --- ⚔️ MOTOR DE ANÁLISIS V40 ---
def analizar_entrada(m, factor):
    try:
        k = cl.get_klines(symbol=m, interval='1m', limit=100)
        df = pd.DataFrame(k, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i']).astype(float)
        
        ema35 = df['c'].ewm(span=35).mean().iloc[-1]
        vol_avg = df['v'].tail(15).mean()
        px = df['c'].iloc[-1]
        
        # DETECTAR INYECCIÓN (Aumento de volumen > 250%)
        inyeccion = df['v'].iloc[-1] > (vol_avg * 2.5) and df['c'].iloc[-1] > df['o'].iloc[-1]
        
        if inyeccion and px > ema35:
            # Calcular X Dinámicas con tope de 15x
            fuerza_x = int(np.clip(12 / factor, 3, 15))
            return "LONG", "INYECCION", fuerza_x
            
        return None, None, 0
    except: return None, None, 0

# --- 🚀 BUCLE PRINCIPAL ---
print(f"\n🔱 V40 MASTER QUANTUM | AJEDREZ DE GUERRA ACTIVADO")
print(f"--------------------------------------------------")

st = {m: {'e': False, 'p': 0, 't': '', 'max': 0, 'modo': '', 'x': 10} for m in ms}
factor_actual, capital_trabajo, rango = gestionar_memoria(leer=True)

while True:
    try:
        for m in ms:
            s = st[m]
            # Obtener precio rápido
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            
            if not s['e']:
                # MODO ESCANEO CON NOMBRE DE RANGO
                print(f"[{rango}] 🔭 Buscando en {m} | Cap: ${capital_trabajo:.2f}", end='\r')
                tipo, modo, fuerza_x = analizar_entrada(m, factor_actual)
                
                if tipo:
                    s['e'], s['p'], s['t'], s['modo'], s['x'], s['max'] = True, px, tipo, modo, fuerza_x, px
                    print(f"\n🚀 ¡INYECCIÓN DETECTADA! {m} | Entrando con {fuerza_x}X de potencia")
            
            else:
                # GESTIÓN DE POSICIÓN (INTERÉS COMPUESTO)
                roi = ((px - s['p']) / s['p'] * 100 * s['x']) if s['t'] == "LONG" else ((s['p'] - px) / s['p'] * 100 * s['x'])
                roi -= 0.22 # Comisiones
                
                s['max'] = max(s['max'], px) if s['t'] == "LONG" else (min(s['max'], px) if s['max'] > 0 else px)
                retroceso = abs(s['max'] - px) / s['p'] * 100 * s['x']
                
                print(f"📊 {m} ROI: {roi:.2f}% | Max: {s['max']}", end='\r')

                # Cierre Inteligente (Resorte)
                if (roi > 0.45 and retroceso > 0.12) or roi <= -1.2:
                    res = "WIN" if roi > 0 else "LOSS"
                    # Aplicar Interés Compuesto al capital real
                    capital_trabajo += (capital_trabajo * (roi / 100))
                    gestionar_memoria(m, s['t'], s['modo'], round(roi, 2), res)
                    s['e'] = False
                    print(f"\n✅ OPERACIÓN FINALIZADA en {m} | ROI: {roi:.2f}% | Capital: ${capital_trabajo:.2f}")
                    # Actualizar rango y factor desde la memoria
                    factor_actual, _, rango = gestionar_memoria(leer=True)

        time.sleep(0.5)
    except Exception as e:
        time.sleep(2)
