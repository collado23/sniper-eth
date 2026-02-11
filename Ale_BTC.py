import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN DIRECTA ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === CONFIGURACIÓN LIMPIA ===
cap_base = 30.00
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
racha_positiva = 0
en_op = False
historial_bloque = []
elast_base_fijada = 0.125  # Valor fijo para que arranque YA

print("🚀 ARRANQUE FORZADO - MEMORIA LIMPIA - AMETRALLADORA OK")

def mostrar_reporte_total():
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*55 + "╗")
    print(f"║ 🔱 REPORTE ALE SNIPER | RESET TOTAL | {ts}  ║")
    print(f"║ TOTAL: {ops_totales} | NETO: ${neto:.4f} | CAP: ${cap_base+neto:.2f} ║")
    for h in historial_bloque: print(f"║  • {h} ║")
    print("╚" + "═"*55 + "╝\n")
    historial_bloque.clear()

while ops_totales < 1000:
    try:
        sol = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=10)
        
        def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
        v1, v2, v3, v4 = col(klines[-2]), col(klines[-3]), col(klines[-4]), col(klines[-5])
        
        ema_v = sum([float(k[4]) for k in klines]) / 10
        elast_act = abs(((ema_v - sol) / sol) * 100)
        
        if not en_op:
            print(f"🔍 SOL: ${sol} | E_ACT: {elast_act:.3f}% | RACHA: {v4}{v3}{v2}{v1}", end='\r')
            if v1 == v2 == v3 == v4 and elast_act >= elast_base_fijada:
                p_ent, en_op, max_roi = sol, True, -99.0
                t_op = "SHORT" if v1 == "V" else "LONG"
                e_al_entrar = elast_act
        else:
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.20
            if roi_neto > max_roi: max_roi = roi_neto
            if (max_roi >= 0.35 and roi_neto <= (max_roi - 0.10)) or roi_neto <= -0.80:
                res = (cap_base * (roi_neto / 100))
                ops_totales += 1
                if res > 0: 
                    ganado += res
                    ops_ganadas += 1
                else: 
                    perdido += abs(res)
                    ops_perdidas += 1
                historial_bloque.append(f"{t_op} | ROI: {roi_neto:.2f}% | E: {e_al_entrar:.3f}%")
                if ops_totales % 5 == 0: mostrar_reporte_total()
                en_op = False
        time.sleep(10)
    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(5)
