import os
import time
from datetime import datetime
from binance.client import Client

# === CONFIGURACIÓN ===
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
client = Client(API_KEY, API_SECRET)

# === PARÁMETROS AMETRALLADORA NETA ===
espera_segundos = 14
distancia_x_gatillo = 0.7   # Gatillo fácil: se activa con poco estiramiento
palanca = 10
ganancia_neta_objetivo = 0.5 # Lo que querés ganar vos (0.5%)
comision_total = 0.2         # Lo que se lleva Binance (0.1% entra + 0.1% sale)
meta_bruta = ganancia_neta_objetivo + comision_total # El bot busca 0.7% para darte 0.5%

archivo_memoria = "memoria_quantum.txt"

# === ESTADO DE CAJA ===
capital_base = 30.00
ganancia_hoy = 0.0
perdida_hoy = 0.0
contador_ops = 0
en_operacion = False

def registrar(tipo, msg, valor=0):
    global contador_ops, ganancia_hoy, perdida_hoy
    ts = datetime.now().strftime('%H:%M:%S')
    with open(archivo_memoria, "a") as f:
        f.write(f"[{ts}] {tipo} | {msg}\n")
    if tipo == "CIERRE":
        contador_ops += 1
        if valor > 0: ganancia_hoy += valor
        else: perdida_hoy += abs(valor)
        # Análisis automático cada 20
        if contador_ops % 20 == 0:
            with open(archivo_memoria, "a") as f:
                f.write(f"\n--- 🧠 ANÁLISIS UNO (OP {contador_ops}) | NETO HOY: ${ganancia_hoy - perdida_hoy:.2f} ---\n")

print(f"🔥 AMETRALLADORA NETA ACTIVADA - BUSCANDO {ganancia_neta_objetivo}% LIMPIO")

while True:
    try:
        # Datos rápidos de SOL y BTC
        ticker_sol = client.get_symbol_ticker(symbol="SOLUSDT")
        p_sol = float(ticker_sol['price'])
        ticker_btc = client.get_symbol_ticker(symbol="BTCUSDT")
        p_btc = float(ticker_btc['price'])
        
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=50)
        cierre = [float(k[4]) for k in klines]
        ema = sum(cierre) / len(cierre)
        dist_x = abs(((ema - p_sol) / p_sol) * 100)
        
        neto_real = ganancia_hoy - perdida_hoy

        # --- TABLERO AMETRALLADORA ---
        print("\n" + "═"*50)
        print(f"🔱 ALE IA AMETRALLADORA | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💎 SOL: ${p_sol:.2f} | 🍊 BTC: ${p_btc:.0f}")
        print(f"💰 CAP: ${capital_base + neto_real:.2f} | 📈 NETO: ${neto_real:.2f}")
        print(f"✅ GAN: +${ganancia_hoy:.2f} | ❌ PERD: -${perdida_hoy:.2f}")
        print(f"🔢 OPS: {contador_ops}/20 | 📏 DIST X: {dist_x:.2f}%")
        print("═"*50)

        if not en_operacion:
            # Entrada rápida por distancia
            if dist_x >= distancia_x_gatillo:
                en_operacion = True
                p_entrada = p_sol
                tipo_op = "LONG 🟢" if p_sol < ema else "SHORT 🔴"
                registrar("ENTRADA", f"{tipo_op} en ${p_sol} (BTC: ${p_btc})")
        else:
            # Cálculo de ROI Bruto
            if "LONG" in tipo_op:
                roi_bruto = ((p_sol - p_entrada) / p_entrada) * 100 * palanca
            else:
                roi_bruto = ((p_entrada - p_sol) / p_entrada) * 100 * palanca
            
            # ROI Neto = Bruto - Gastos de Binance
            roi_neto = roi_bruto - comision_total
            
            # CIERRE: Si llegamos al 0.5% neto o perdemos 0.7% neto (Stop Loss)
            if roi_neto >= ganancia_neta_objetivo or roi_neto <= -0.7:
                ganancia_limpia = (capital_base * (roi_neto / 100))
                registrar("CIERRE", f"{tipo_op} Neto: {roi_neto:.2f}% | P_SALIDA: ${p_sol}", ganancia_limpia)
                en_operacion = False
                print(f"🎯 ¡PUM! Ametralladora cobró: {roi_neto:.2f}% neto.")

        time.sleep(espera_segundos)
    except Exception as e:
        time.sleep(espera_segundos)
