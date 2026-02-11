import os
import time
from datetime import datetime
from binance.client import Client

client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === MEMORIA SEGÚN TU ÚLTIMA CAPTURA ===
cap_base = 30.76
ganado, perdido = 0.75, 0.0 # Ya estás en positivo!
ops_ganadas, ops_perdidas, ops_totales = 8, 7, 15
en_op = False
historial_bloque = []

def libro_de_velas_pro(k):
    op, hi, lo, cl = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    cuerpo = abs(cl - op)
    m_inf, m_sup = min(op, cl) - lo, hi - max(op, cl)
    if (hi - lo) == 0: return "Doji"
    # Solo Martillos con mechas MUY largas (3x cuerpo)
    if m_inf > (cuerpo * 3.0): return "Martillo 🔨⚡" 
    if m_sup > (cuerpo * 3.0): return "Estrella ☄️"
    return "Normal"

while ops_totales < 1000:
    try:
        sol = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=5)
        patron = libro_de_velas_pro(klines[-1])
        v1, v2, v3 = [("V" if float(k[4]) > float(k[1]) else "R") for k in klines[-3:]]

        if not en_op:
            # GATILLO SNIPER: Martillo real + racha de 3 mínimas
            if patron == "Martillo 🔨⚡" and v1 == "R":
                p_ent, en_op, t_op, p_al_entrar = sol, True, "LONG", patron
                max_roi = -99.0
            elif patron == "Estrella ☄️" and v1 == "V":
                p_ent, en_op, t_op, p_al_entrar = sol, True, "SHORT", patron
                max_roi = -99.0

        else:
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.22 
            if roi_neto > max_roi: max_roi = roi_neto
            
            # SALIDA: Buscamos el centavo neto o cortamos pérdida rápido
            if (max_roi >= 0.40 and roi_neto <= (max_roi - 0.10)) or roi_neto <= -0.80:
                res = (cap_base * (roi_neto / 100))
                ops_totales += 1
                if res > 0: ganado += res; ops_ganadas += 1; ico = "✅"
                else: perdido += abs(res); ops_perdidas += 1; ico = "❌"
                historial_bloque.append(f"{ico} {t_op:5} | ROI:{roi_neto:>5.2f}% | {p_al_entrar}")
                if ops_totales % 5 == 0:
                    print(f"\n🔱 REPORTE: {ops_totales} OPS | NETO: ${ganado-perdido:.4f}")
                en_op = False
        time.sleep(6)
    except: time.sleep(5)
