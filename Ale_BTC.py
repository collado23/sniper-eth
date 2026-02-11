import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN LIMPIA ===
try:
    client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
    print("✅ Conexión establecida con Binance")
except Exception as e:
    print(f"❌ Error de conexión: {e}")

# === CONFIGURACIÓN (Capital Inicial $30) ===
cap_base = 30.00
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
en_op = False
historial_bloque = []

def libro_de_velas(k):
    """Analiza mechas y cuerpos para detectar Martillos y Estrellas"""
    op, hi, lo, cl = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    cuerpo = abs(cl - op)
    m_inf, m_sup = min(op, cl) - lo, hi - max(op, cl)
    total = hi - lo
    if total == 0: return "Doji"
    if m_inf > (cuerpo * 2.2): return "Martillo 🔨"
    if m_sup > (cuerpo * 2.2): return "Estrella ☄️"
    return "Normal"

# --- FASE 1: ANÁLISIS DE 20 VELAS (Sin saturar el servidor) ---
def fase_inicio_adn():
    print("📡 Fase 1: Analizando 20 velas previas...")
    try:
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=21)
        rojas = sum(1 for k in klines if float(k[4]) < float(k[1]))
        verdes = sum(1 for k in klines if float(k[4]) > float(k[1]))
        print(f"📊 ADN Cargado: {rojas} Rojas / {verdes} Verdes detectadas.")
    except Exception as e:
        print(f"⚠️ Error en lectura inicial: {e}")

fase_inicio_adn()

def mostrar_reporte_total():
    """Cuadro de reporte cada 5 operaciones"""
    global historial_bloque
    ts = datetime.now().strftime('%H:%M:%S')
    neto = ganado - perdido
    print("\n" + "╔" + "═"*65 + "╗")
    print(f"║ 🔱 REPORTE DE OPERACIONES | {ts}                  ║")
    print(f"║ 📊 TOTAL: {ops_totales} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas} | 💰 NETO: ${neto:.4f} ║")
    print(f"║ 💵 CAPITAL FINAL: ${cap_base + neto:.2f}                        ║")
    print("╠" + "═"*65 + "╣")
    for h in historial_bloque: print(f"║ • {h} ║")
    print("╚" + "═"*65 + "╝\n")
    historial_bloque.clear()

# --- BUCLE PRINCIPAL (Optimizado para Railway) ---
print("🚀 AMETRALLADORA ACTIVADA - BUSCANDO MARTILLOS...")
while ops_totales < 1000:
    try:
        # Consulta rápida de precio y velas
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=5)
        
        def col(k): return "V" if float(k[4]) > float(k[1]) else "R"
        v1, v2, v3 = col(klines[-1]), col(klines[-2]), col(klines[-3])
        patron_v1 = libro_de_velas(klines[-1])
        
        if not en_op:
            # Escaneo silencioso
            print(f"🔍 Buscando... Racha: {v3}{v2}{v1} | Vela: {patron_v1}", end='\r')
            
            # Entrada por Martillo (Rebote Alza) o Estrella (Rebote Baja)
            es_martillo = (v1 == "R" and patron_v1 == "Martillo 🔨")
            es_estrella = (v1 == "V" and patron_v1 == "Estrella ☄️")
            
            if es_martillo or es_estrella:
                p_ent, en_op, max_roi = sol, True, -99.0
                t_op = "LONG" if es_martillo else "SHORT"
                p_al_entrar = patron_v1
                print(f"\n🎯 ENTRADA EN {t_op} | Motivo: {p_al_entrar} | Precio: {p_ent}")
        
        else:
            # Lógica de salida para ganar más que perder
            diff = ((sol - p_ent) / p_ent) if t_op == "LONG" else ((p_ent - sol) / p_ent)
            roi_neto = (diff * 100 * 10) - 0.20 # Apalancamiento x10 y comisión
            
            if roi_neto > max_roi: max_roi = roi_neto
            
            # 1. Take Profit (0.45% mínimo para cubrir comisión y ganar)
            if max_roi >= 0.45 and roi_neto <= (max_roi - 0.12):
                res = (cap_base * (roi_neto / 100))
                en_op = False
            
            # 2. Stop Loss ajustado (Cortamos rápido la pérdida)
            elif roi_neto <= -0.75:
                res = (cap_base * (roi_neto / 100))
                en_op = False
            
            if not en_op:
                ops_totales += 1
                if res > 0:
                    ganado += res; ops_ganadas += 1; ico = "✅"
                else:
                    perdido += abs(res); ops_perdidas += 1; ico = "❌"
                
                historial_bloque.append(f"{ico} {t_op:5} | ROI:{roi_neto:>5.2f}% | {p_al_entrar} | ${res:.4f}")
                if ops_totales % 5 == 0: mostrar_reporte_total()

        time.sleep(5) # Pausa justa para no saturar la cola de Railway
    except Exception as e:
        print(f"\n⚠️ Reintentando... {e}")
        time.sleep(10)
