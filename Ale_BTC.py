import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === CONFIGURACIÓN $30 ===
cap_base = 30.00
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
en_op = False
historial_bloque = []

def analizar_y_gatillar():
    """Analiza las 20 velas previas y decide si entra YA"""
    print("📡 ANALIZANDO PASADO INMEDIATO PARA DISPARO INSTANTÁNEO...")
    klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=40)
    
    # 1. Calculamos la elasticidad base de esas 20
    elasts = []
    for i in range(20, 40):
        subset = klines[i-20:i]
        ema = sum([float(k[4]) for k in subset]) / 20
        precio_v = float(klines[i][4])
        elasts.append(abs(((ema - precio_v) / precio_v) * 100))
    e_base = sum(elasts) / len(elasts)
    
    # 2. Vemos cómo terminaron las últimas 4 velas justo antes de ahora
    def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
    v1, v2, v3, v4 = col(klines[-1]), col(klines[-2]), col(klines[-3]), col(klines[-4])
    
    # 3. Precio actual y elasticidad actual
    sol = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
    ema_ahora = sum([float(k[4]) for k in klines[-10:]]) / 10
    e_act = abs(((ema_ahora - sol) / sol) * 100)
    
    print(f"✅ ANÁLISIS: Base {e_base:.3f}% | Actual {e_act:.3f}% | Racha: {v4}{v3}{v2}{v1}")
    
    # Si al arrancar ya se cumple la racha, devolvemos los datos para entrar
    if v1 == v2 == v3 == v4 and e_act >= e_base:
        tipo = "SHORT" if v1 == "V" else "LONG"
        return True, e_base, tipo, sol, e_act
    
    return False, e_base, None, sol, e_act

# --- ARRANQUE ---
disparo_ya, elast_base_fijada, t_op_ini, p_ent_ini, e_ent_ini = analizar_y_gatillar()

if disparo_ya:
    print(f"🚀 ¡GATILLO DETECTADO EN EL PASADO! Entrando en {t_op_ini} ya mismo...")
    en_op = True
    t_op, p_ent, e_al_entrar = t_op_ini, p_ent_ini, e_ent_ini
    max_roi = -99.0
    cap_usado = cap_base
else:
    print("⏳ Sin racha clara en el pasado. Empezando escaneo en vivo...")

def mostrar_reporte_total():
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*60 + "╗")
    print(f"║ 🔱 REPORTE QUANTUM INSTANTÁNEO | {ts}      ║")
    print(f"║ 📊 TOTAL: {ops_totales} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas} ║")
    print(f"║ 💰 NETO: ${neto:.4f} | 💵 CAP: ${cap_base + neto:.2f} ║")
    print("╠" + "═"*60 + "╣")
    for h in historial_bloque: print(f"║ • {h} ║")
    print("╚" + "═"*60 + "╝\n")
    historial_bloque.clear()

# --- BUCLE PRINCIPAL ---
while ops_totales < 1000:
    try:
        if not en_op:
            ticker = client.get_symbol_ticker(symbol="SOLUSDT")
            sol = float(ticker['price'])
            klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=10)
            
            def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
            v1, v2, v3, v4 = col(klines[-1]), col(klines[-2]), col(klines[-3]), col(klines[-4])
            
            ema_v = sum([float(k[4]) for k in klines]) / 10
            elast_act = abs(((ema_v - sol) / sol) * 100)
            
            print(f"🔍 BASE:{elast_base_fijada:.3f}% | ACT:{elast_act:.3f}% | RACHA:{v4}{v3}{v2}{v1}", end='\r')
            
            if v1 == v2 == v3 == v4 and elast_act >= elast_base_fijada:
                p_ent, en_op, max_roi = sol, True, -99.0
                t_op = "SHORT" if v1 == "V" else "LONG"
                e_al_entrar = elast_act
                cap_usado = cap_base
        else:
            # Lógica de Trailing (Igual que antes para asegurar el verde)
            sol = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.20
            if roi_neto > max_roi: max_roi = roi_neto
            
            if (max_roi >= 0.30 and roi_neto <= (max_roi - 0.10)) or roi_neto <= -0.80:
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

        time.sleep(5)
    except: time.sleep(2)
