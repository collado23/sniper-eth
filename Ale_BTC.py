import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === CONFIGURACIÓN DE RESETEO ($30) + INTERÉS COMPUESTO ===
cap_base = 30.00
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
racha_positiva = 0 # Contador para activar el 20%
en_op = False
historial_bloque = []

def mostrar_reporte_total():
    global historial_bloque
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*60 + "╗")
    print(f"║ 🔱 REPORTE QUANTUM + INTERÉS COMPUESTO | {ts}        ║")
    print("╠" + "═"*60 + "╣")
    print(f"║  🔢 TOTAL: {ops_totales} OPS | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas}   ║")
    print(f"║  💰 NETO: ${neto:.4f} | 💵 CAPITAL: ${cap_base + neto:.2f}   ║")
    print("╠" + "═"*60 + "╣")
    print("║  📝 DETALLE (ROI NETO | ELASTICIDAD | MODO):            ║")
    for h in historial_bloque:
        print(f"║  • {h} ║")
    print("╚" + "═"*60 + "╝\n")
    historial_bloque = []

def registrar_evento(t_op, roi_n, res_plata, elast_entrada, modo_cap):
    global ops_totales, ganado, perdido, ops_ganadas, ops_perdidas, racha_positiva
    ops_totales += 1
    icono = "✅" if res_plata > 0 else "❌"
    
    # Manejo de Racha para Interés Compuesto
    if res_plata > 0:
        racha_positiva += 1
        ganado += res_plata
        ops_ganadas += 1
    else:
        racha_positiva = 0 # Reset de racha si pierde
        perdido += abs(res_plata)
        ops_perdidas += 1
    
    # Detalle para el reporte
    detalle = f"{icono} {t_op:5} | ROI:{roi_n:>5.2f}% | E:{elast_entrada:.3f}% | {modo_cap}"
    historial_bloque.append(detalle)
    
    if ops_totales % 5 == 0:
        mostrar_reporte_total()

print(f"🚀 AMETRALLADORA 1000 OPS + INTERÉS COMPUESTO (3 G -> +20%)")

while ops_totales < 1000:
    try:
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=5)
        
        # Análisis de Velas y Elasticidad
        def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
        v1, v2 = col(klines[-2]), col(klines[-3])
        
        k_ema = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=15)
        ema = sum([float(k[4]) for k in k_ema]) / 15
        elasticidad = abs(((ema - sol) / sol) * 100)
        
        if not en_op:
            # Si racha >= 3, usamos interés compuesto (20% extra)
            cap_operacion = cap_base * 1.20 if racha_positiva >= 3 else cap_base
            modo_texto = "COMPUESTO 🚀" if racha_positiva >= 3 else "BASE 🛡️"
            
            print(f"🔍 [{modo_texto}] Ops:{ops_totales} | SOL:${sol} | E:{elasticidad:.3f}% | Racha:{racha_positiva}", end='\r')
            
            if v1 == v2 and elasticidad >= 0.015:
                p_ent, en_op, max_roi = sol, True, -99.0
                e_al_entrar = elasticidad
                t_op = "SHORT" if v1 == "V" else "LONG"
                cap_usado = cap_operacion
                txt_cap = modo_texto
        
        else:
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.20
            if roi_neto > max_roi: max_roi = roi_neto
            
            # Cierre con Trailing dinámico
            if (max_roi >= 0.30 and roi_neto <= (max_roi - 0.10)) or roi_neto <= -0.65:
                res = (cap_usado * (roi_neto / 100))
                registrar_evento(t_op, roi_neto, res, e_al_entrar, txt_cap)
                en_op = False

        time.sleep(10)
    except Exception as e:
        time.sleep(5)
