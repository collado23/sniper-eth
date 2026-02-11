import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === CONFIGURACIÓN ALE IA QUANTUM (Capital Inicial $30) ===
cap_base = 30.00
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
en_op = False
historial_bloque = []

def libro_de_velas(k):
    """Analiza la forma de la vela: Martillo, Estrella o Marubozu"""
    op, hi, lo, cl = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    cuerpo = abs(cl - op)
    m_inf = min(op, cl) - lo
    m_sup = hi - max(op, cl)
    total = hi - lo
    if total == 0: return "Doji"
    if m_inf > (cuerpo * 2): return "Martillo 🔨"
    if m_sup > (cuerpo * 2): return "Estrella ☄️"
    if cuerpo > (total * 0.85): return "Marubozu 💪"
    return "Normal"

# --- FASE 1: ANÁLISIS ADN (20 VELAS PREVIAS) ---
def analizar_adn_20v():
    print("📡 ANALIZANDO ADN DEL MERCADO (20 VELAS ANTES DE ARRANCAR)...")
    klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=20)
    r = sum(1 for k in klines if float(k[4]) < float(k[1]))
    v = sum(1 for k in klines if float(k[4]) > float(k[1]))
    print(f"✅ ANÁLISIS COMPLETADO: {r} Rojas | {v} Verdes.")
    return klines

analizar_adn_20v()

def mostrar_reporte_total():
    """EL CUADRO PARA TU CAPTURA CON GANADAS Y PERDIDAS"""
    global historial_bloque
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*65 + "╗")
    print(f"║ 🔱 REPORTE ALE IA QUANTUM | {ts}                   ║")
    print(f"║ 📊 TOTAL: {ops_totales} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas} | 💰 NETO: ${neto:.4f} ║") # AQUÍ ESTÁN
    print(f"║ 💵 CAPITAL ACTUAL: ${cap_base + neto:.2f}                        ║")
    print("╠" + "═"*65 + "╣")
    for h in historial_bloque:
        print(f"║ • {h} ║")
    print("╚" + "═"*65 + "╝\n")
    historial_bloque.clear()

# --- BUCLE DE LA AMETRALLADORA ---
while ops_totales < 1000:
    try:
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=6)
        
        # Análisis de color y patrón
        def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
        v1, v2, v3, v4 = col(klines[-1]), col(klines[-2]), col(klines[-3]), col(klines[-4])
        patron_v1 = libro_de_velas(klines[-1])
        
        if not en_op:
            print(f"🔍 ESCANEANDO | RACHA: {v4}{v3}{v2}{v1} | PATRÓN: {patron_v1}", end='\r')
            
            # GATILLO: Racha de 4 o Vela de Reversión del Libro
            giro = (v1 == "V" and patron_v1 == "Martillo 🔨") or (v1 == "R" and patron_v1 == "Estrella ☄️")
            
            if (v1 == v2 == v3 == v4) or giro:
                p_ent, en_op, max_roi = sol, True, -99.0
                t_op = "LONG" if (v1 == "R" or patron_v1 == "Martillo 🔨") else "SHORT"
                p_al_entrar = patron_v1
                print(f"\n🚀 ENTRADA: {t_op} | MOTIVO: {p_al_entrar} | PRECIO: {p_ent}")
        
        else:
            # Trailing Stop para asegurar el centavo (+0.01 / +0.02 netos)
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.20 # X10 leverage y comisiones
            
            if roi_neto > max_roi: max_roi = roi_neto
            
            # Cierre con beneficio real
            if max_roi >= 0.35 and roi_neto <= (max_roi - 0.12):
                res = (cap_base * (roi_neto / 100))
                en_op = False
            elif roi_neto <= -0.85: # Stop Loss de seguridad
                res = (cap_base * (roi_neto / 100))
                en_op = False
            
            if not en_op:
                ops_totales += 1
                if res > 0:
                    ganado += res; ops_ganadas += 1; icono = "✅"
                else:
                    perdido += abs(res); ops_perdidas += 1; icono = "❌"
                
                # Detalle de la operación para el cuadro
                historial_bloque.append(f"{icono} {t_op:5} | ROI:{roi_neto:>5.2f}% | {p_al_entrar} | ${res:.4f}")
                
                if ops_totales % 5 == 0:
                    mostrar_reporte_total()

        time.sleep(6)
    except Exception as e:
        time.sleep(5)
