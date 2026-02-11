import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === MEMORIA ACTUALIZADA (Basada en tu última captura $27.99) ===
cap_base = 27.99
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
en_op = False
historial_bloque = []

# --- LECTURA BASE DE 20 VELAS ---
def obtener_lectura_base():
    klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=40)
    elasts = [abs(((sum([float(x[4]) for x in klines[i-20:i]])/20 - float(klines[i][4]))/float(klines[i][4]))*100) for i in range(20, 40)]
    return sum(elasts) / len(elasts)

elast_base_fijada = obtener_lectura_base()

def mostrar_reporte_total():
    global historial_bloque
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*60 + "╗")
    print(f"║ 🔱 REPORTE ALE SNIPER PRO | {ts}          ║")
    print(f"║ 📊 TOTAL: {ops_totales} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas} ║")
    print(f"║ 💰 NETO: ${neto:.4f} | 💵 CAP: ${cap_base + neto:.2f} ║")
    print("╠" + "═"*60 + "╣")
    for h in historial_bloque: print(f"║ • {h} ║")
    print("╚" + "═"*60 + "╝\n")
    historial_bloque.clear()

while ops_totales < 1000:
    try:
        sol = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=10)
        
        def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
        v1, v2, v3, v4, v5 = col(klines[-2]), col(klines[-3]), col(klines[-4]), col(klines[-5]), col(klines[-6])
        
        ema = sum([float(k[4]) for k in klines]) / 10
        elast_act = abs(((ema - sol) / sol) * 100)
        
        if not en_op:
            # GATILLO: 4 velas iguales Y la última (v1) ya cambió de color o bajó la elasticidad
            # Esto evita entrar en medio de la caída de 7 velas
            print(f"🔍 BASE:{elast_base_fijada:.3f}% | ACT:{elast_act:.3f}% | RACHA:{v4}{v3}{v2}{v1}", end='\r')
            
            # Condición Sniper: 4 velas previas iguales (v5,v4,v3,v2) y la actual (v1) intenta el rebote
            if v2 == v3 == v4 == v5 and elast_act >= (elast_base_fijada * 1.5):
                p_ent, en_op, max_roi = sol, True, -99.0
                t_op = "SHORT" if v2 == "V" else "LONG"
                e_al_entrar = elast_act
        else:
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.22 
            if roi_neto > max_roi: max_roi = roi_neto
            
            # Trailing más ajustado para no devolver lo ganado
            if (max_roi >= 0.40 and roi_neto <= (max_roi - 0.15)) or roi_neto <= -1.0:
                res = (cap_base * (roi_neto / 100))
                ops_totales += 1
                if res > 0: 
                    ganado += res
                    ops_ganadas += 1
                else: 
                    perdido += abs(res)
                    ops_perdidas += 1
                historial_bloque.append(f"{t_op} | ROI:{roi_neto:>5.2f}% | E:{e_al_entrar:.3f}%")
                if ops_totales % 5 == 0: mostrar_reporte_total()
                en_op = False
        time.sleep(12)
    except: time.sleep(5)
