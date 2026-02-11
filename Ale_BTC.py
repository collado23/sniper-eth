import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === CONFIGURACIÓN RESETEO $30 (O el saldo que tengas actual) ===
cap_base = 30.00
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
racha_positiva = 0
en_op = False
historial_bloque = []

# --- FASE 1: ANÁLISIS DE LAS 20 VELAS PREVIAS ---
def obtener_lectura_base():
    print("📡 FASE DE INICIO: Analizando últimas 20 velas para fijar Elasticidad Base...")
    # Pedimos 40 para tener margen de cálculo de la media móvil
    klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=40)
    elasts = []
    for i in range(20, 40):
        subset = klines[i-20:i]
        ema = sum([float(k[4]) for k in subset]) / 20
        precio_v = float(klines[i][4])
        elasts.append(abs(((ema - precio_v) / precio_v) * 100))
    return sum(elasts) / len(elasts)

# Ejecutamos la lectura antes de arrancar las operaciones
elast_base_fijada = obtener_lectura_base()
print(f"✅ ANÁLISIS COMPLETADO. Elasticidad de Referencia: {elast_base_fijada:.4f}%")

def mostrar_reporte_total():
    """El cuadro para tu captura de pantalla cada 5 ops"""
    global historial_bloque
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*60 + "╗")
    print(f"║ 🔱 REPORTE SNIPER 4V | BASE 20V: {elast_base_fijada:.3f}%      ║")
    print(f"║ 💰 NETO: ${neto:.4f} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas}   ║")
    print(f"║ 💵 CAPITAL ACTUAL: ${cap_base + neto:.2f}                        ║")
    print("╠" + "═"*60 + "╣")
    for h in historial_bloque:
        print(f"║ • {h} ║")
    print("╚" + "═"*60 + "╝\n")
    historial_bloque.clear()

def registrar_evento(t_op, roi_n, res_p, e_ent, modo):
    global ops_totales, ganado, perdido, ops_ganadas, ops_perdidas, racha_positiva, historial_bloque
    ops_totales += 1
    icono = "✅" if res_p > 0 else "❌"
    if res_p > 0:
        ganado += res_p
        ops_ganadas += 1
        racha_positiva += 1
    else:
        perdido += abs(res_p)
        ops_perdidas += 1
        racha_positiva = 0
    
    # Info detallada para la foto
    detalle = f"{icono} {t_op:5} | ROI:{roi_n:>5.2f}% | E:{e_ent:.3f}% | {modo}"
    historial_bloque.append(detalle)
    if ops_totales % 5 == 0:
        mostrar_reporte_total()

# --- BUCLE DE OPERACIONES ---
while ops_totales < 1000:
    try:
        sol = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=10)
        
        # FILTRO DE 4 VELAS (Basado en tu conteo de las imágenes)
        def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
        v1, v2, v3, v4 = col(klines[-2]), col(klines[-3]), col(klines[-4]), col(klines[-5])
        racha_str = f"{v4}{v3}{v2}{v1}"

        # ELASTICIDAD ACTUAL
        ema_act = sum([float(k[4]) for k in klines]) / 10
        elast_act = abs(((ema_act - sol) / sol) * 100)
        
        if not en_op:
            # INTERÉS COMPUESTO (Si hay 3 ganadas seguidas, +20%)
            cap_cur = cap_base * 1.20 if racha_positiva >= 3 else cap_base
            txt_m = "COMPUESTO 🚀" if racha_positiva >= 3 else "BASE 🛡️"
            
            # GATILLO ACOPLADO: 4 velas iguales Y elasticidad mayor a la base de las 20v
            if v1 == v2 == v3 == v4 and elast_act >= elast_base_fijada:
                p_ent, en_op, max_roi = sol, True, -99.0
                t_op = "SHORT" if v1 == "V" else "LONG"
                e_al_entrar = elast_act
                modo_al_entrar = txt_m
                cap_usado = cap_cur
            
            print(f"🔍 BASE:{elast_base_fijada:.3f}% | ACT:{elast_act:.3f}% | RACHA:{racha_str} | {txt_m}", end='\r')
        
        else:
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.20 # X10 y comisión
            if roi_neto > max_roi: max_roi = roi_neto
            
            # Cierre con Trailing dinámico para asegurar el centavo
            if (max_roi >= 0.35 and roi_neto <= (max_roi - 0.12)) or roi_neto <= -0.80:
                res = (cap_usado * (roi_neto / 100))
                registrar_evento(t_op, roi_neto, res, e_al_entrar, modo_al_entrar)
                en_op = False

        time.sleep(12)
    except: time.sleep(5)
