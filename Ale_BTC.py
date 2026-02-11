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
en_op = False
historial_bloque = []

# --- LECTURA INICIAL DE 20 VELAS ---
def obtener_lectura_base():
    print("📡 FASE DE INICIO: Analizando 20 velas...")
    klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=40)
    elasts = []
    for i in range(20, 40):
        subset = klines[i-20:i]
        ema = sum([float(k[4]) for k in subset]) / 20
        precio_v = float(klines[i][4])
        elasts.append(abs(((ema - precio_v) / precio_v) * 100))
    return sum(elasts) / len(elasts)

elast_base_fijada = obtener_lectura_base()
print(f"✅ BASE FIJADA: {elast_base_fijada:.4f}%")

def mostrar_reporte_total():
    """CUADRO PARA CAPTURA CON CONTADORES"""
    global historial_bloque
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*60 + "╗")
    print(f"║ 🔱 REPORTE QUANTUM SNIPER | {ts}              ║")
    print(f"║ 📊 TOTAL: {ops_totales} OPS | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas}   ║") # AQUÍ ESTÁN
    print(f"║ 💰 NETO: ${neto:.4f} | 💵 CAPITAL: ${cap_base + neto:.2f}   ║")
    print("╠" + "═"*60 + "╣")
    for h in historial_bloque:
        print(f"║ • {h} ║")
    print("╚" + "═"*60 + "╝\n")
    historial_bloque.clear()

def registrar_evento(t_op, roi_n, res_p, e_ent):
    global ops_totales, ganado, perdido, ops_ganadas, ops_perdidas, historial_bloque
    ops_totales += 1
    icono = "✅" if res_p > 0 else "❌"
    if res_p > 0:
        ganado += res_p
        ops_ganadas += 1
    else:
        perdido += abs(res_p)
        ops_perdidas += 1
    
    detalle = f"{icono} {t_op:5} | ROI:{roi_n:>5.2f}% | E:{e_ent:.3f}%"
    historial_bloque.append(detalle)
    if ops_totales % 5 == 0:
        mostrar_reporte_total()

while ops_totales < 1000:
    try:
        sol = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=10)
        
        # Filtro 4 Velas
        def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
        v1, v2, v3, v4 = col(klines[-2]), col(klines[-3]), col(klines[-4]), col(klines[-5])
        
        ema_act = sum([float(k[4]) for k in klines]) / 10
        elast_act = abs(((ema_act - sol) / sol) * 100)
        
        if not en_op:
            print(f"🔍 BASE:{elast_base_fijada:.3f}% | ACT:{elast_act:.3f}% | RACHA:{v4}{v3}{v2}{v1}", end='\r')
            if v1 == v2 == v3 == v4 and elast_act >= elast_base_fijada:
                p_ent, en_op, max_roi = sol, True, -99.0
                t_op = "SHORT" if v1 == "V" else "LONG"
                e_al_entrar = elast_act
        else:
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.20
            if roi_neto > max_roi: max_roi = roi_neto
            if (max_roi >= 0.35 and roi_neto <= (max_roi - 0.12)) or roi_neto <= -0.85:
                res = (cap_base * (roi_neto / 100))
                registrar_evento(t_op, roi_neto, res, e_al_entrar)
                en_op = False
        time.sleep(12)
    except: time.sleep(5)
