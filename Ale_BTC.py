import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === CONFIGURACIÓN RESETEO $30 ===
cap_base = 30.00
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
racha_positiva = 0
en_op = False
historial_bloque = []

print(f"📡 FASE 1: LEYENDO 20 VELAS ANTES DE ARRANCAR...")

def obtener_elasticidad_promedio():
    """Analiza las últimas 20 velas para fijar el punto de partida"""
    klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=35)
    elasticidades = []
    # Calculamos la elasticidad de cada una de las últimas 20 velas
    for i in range(20):
        subset = klines[i:i+15] # Ventana de 15 para la media móvil
        cierres = [float(k[4]) for k in subset]
        ema = sum(cierres) / len(cierres)
        precio = float(klines[i+15][4])
        elast = abs(((ema - precio) / precio) * 100)
        elasticidades.append(elast)
    
    promedio = sum(elasticidades) / len(elasticidades)
    return promedio

# --- ARRANQUE CON MEMORIA ---
elast_base = obtener_elasticidad_promedio()
print(f"✅ ANÁLISIS COMPLETADO. Elasticidad Base: {elast_base:.4f}%")
print(f"🚀 INICIANDO OPERACIONES A PARTIR DE ESTE PARÁMETRO...")

def mostrar_reporte_total():
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*60 + "╗")
    print(f"║ 🔱 REPORTE QUANTUM | LECTURA BASE: {elast_base:.3f}%       ║")
    print(f"║ 💰 NETO: ${neto:.4f} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas}   ║")
    print("╠" + "═"*60 + "╣")
    for h in historial_bloque:
        print(f"║  • {h} ║")
    print("╚" + "═"*60 + "╝\n")
    historial_bloque.clear()

# ... (Mantenemos la lógica de racha de 2 o 4 velas según tu preferencia)
while ops_totales < 1000:
    try:
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=10)
        
        # Conteo de velas (usaremos 4 como vimos en tus fotos)
        def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
        v1, v2, v3, v4 = col(klines[-2]), col(klines[-3]), col(klines[-4]), col(klines[-5])
        
        # Elasticidad actual
        k_ema = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=15)
        ema = sum([float(k[4]) for k in k_ema]) / 15
        elasticidad_actual = abs(((ema - sol) / sol) * 100)
        
        if not en_op:
            # Solo entra si la elasticidad actual es mayor a la base de las 20 velas
            # Y si tenemos la racha de velas confirmada
            if v1 == v2 == v3 == v4 and elasticidad_actual >= elast_base:
                p_ent, en_op, max_roi = sol, True, -99.0
                t_op = "SHORT" if v1 == "V" else "LONG"
                cap_usado = cap_base * 1.20 if racha_positiva >= 3 else cap_base
                e_entrada = elasticidad_actual
                
            print(f"🔍 BASE:{elast_base:.3f}% | ACT:{elasticidad_actual:.3f}% | RACHA:{v4}{v3}{v2}{v1}", end='\r')
        
        else:
            # Lógica de cierre y trailing (igual que antes)
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.20
            if roi_neto > max_roi: max_roi = roi_neto
            
            if (max_roi >= 0.30 and roi_neto <= (max_roi - 0.10)) or roi_neto <= -0.65:
                res = (cap_usado * (roi_neto / 100))
                # Registrar y resetear si llega a 5
                # ... (resto de funciones de registro)
                en_op = False

        time.sleep(10)
    except: time.sleep(5)
