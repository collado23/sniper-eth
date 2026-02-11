import os, time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN DIRECTA ===
def conectar():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

client = conectar()

# === CONFIGURACIÓN $30.76 ===
cap_base = 30.76
ganado, perdido = 0.0, 0.0
ops_ganadas, ops_perdidas, ops_totales = 0, 0, 0
en_op = False
historial_bloque = []

def libro_nison_blindado(k1, k2):
    """Matemática de Nison: Filtro 2.5x"""
    op, hi, lo, cl = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cuerpo = abs(cl - op) if abs(cl - op) > 0 else 0.001
    m_inf, m_sup = min(op, cl) - lo, hi - max(op, cl)
    
    op_p, cl_p = float(k2[1]), float(k2[4])
    cuerpo_p = abs(cl_p - op_p)

    # SEÑALES LONG
    if m_inf > (cuerpo * 2.5) and m_sup < (cuerpo * 0.7): return "MARTILLO 🔨"
    if cl > op and cl_p < op_p and cuerpo > (cuerpo_p * 1.1): return "ENVOLVENTE_V 🌊"

    # SEÑALES SHORT
    if m_sup > (cuerpo * 2.5) and m_inf < (cuerpo * 0.7): return "ESTRELLA ☄️"
    if cl < op and cl_p > op_p and cuerpo > (cuerpo_p * 1.1): return "ENVOLVENTE_R 🌊"

    return "Normal"

def mostrar_reporte():
    global historial_bloque
    neto = ganado - perdido
    print(f"\n╔{'═'*55}╗")
    print(f"║ 🔱 REPORTE BLINDADO | {datetime.now().strftime('%H:%M:%S')}          ║")
    print(f"║ TOTAL: {ops_totales} | ✅ G: {ops_ganadas} | ❌ P: {ops_perdidas} | 💰 NETO: ${neto:.4f}  ║")
    print(f"╠{'═'*55}╣")
    for h in historial_bloque: print(f"║ • {h:<51} ║")
    print(f"╚{'═'*55}╝\n")
    historial_bloque.clear()

print("🚀 SNIPER CARGADO - PROTECCIÓN 0.18% - SINCRO 15s")

while True:
    try:
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        sol = float(ticker['price'])
        k = client.get_klines(symbol='SOLUSDT', interval='1m', limit=3)
        
        patron = libro_nison_blindado(k[-1], k[-2])
        precio_cierre_v1 = float(k[-1][4])

        if not en_op:
            print(f"📡 SCAN: {patron} | SOL: {sol} | {datetime.now().strftime('%S')}s", end='\r')
            
            # GATILLOS
            if ("MARTILLO" in patron or "ENVOLVENTE_V" in patron) and sol > precio_cierre_v1:
                p_ent, en_op, t_op, p_al_entrar = sol, True, "LONG", patron
                max_roi, break_even_listo = -99.0, False
                print(f"\n🔥 ENTRADA: {t_op} | {p_al_entrar} a {p_ent}")
            
            elif ("ESTRELLA" in patron or "ENVOLVENTE_R" in patron) and sol < precio_cierre_v1:
                p_ent, en_op, t_op, p_al_entrar = sol, True, "SHORT", patron
                max_roi, break_even_listo = -99.0, False
                print(f"\n🔥 ENTRADA: {t_op} | {p_al_entrar} a {p_ent}")
        
        else:
            diff = (sol - p_ent) / p_ent if t_op == "LONG" else (p_ent - sol) / p_ent
            roi = (diff * 100 * 10) - 0.22 
            if roi > max_roi: max_roi = roi
            
            # BREAK EVEN ULTRA-RÁPIDO (Cuidar el capital)
            if roi >= 0.18: 
                break_even_listo = True
            
            if break_even_listo and roi <= 0.01:
                res, motivo = (cap_base * (roi / 100)), "🛡️ BREAK EVEN (BLINDADO)"
                en_op = False
            elif (max_roi >= 0.40 and roi <= (max_roi - 0.12)) or roi <= -0.55:
                res, motivo = (cap_base * (roi / 100)), p_al_entrar
                en_op = False
                
            if not en_op:
                ops_totales += 1
                if res > 0: ganado += res; ops_ganadas += 1; ico = "✅"
                else: perdido += abs(res); ops_perdidas += 1; ico = "❌"
                historial_bloque.append(f"{ico} {t_op} {roi:>5.2f}% | {motivo}")
                if ops_totales % 5 == 0: mostrar_reporte()

        time.sleep(15)

    except Exception as e:
        time.sleep(10)
        client = conectar()
