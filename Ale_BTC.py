import os
import time
from datetime import datetime
from binance.client import Client

# === CONEXIÓN ===
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

# === PARÁMETROS ADN ===
espera_segundos = 14
palanca = 10
ganancia_neta_ale = 0.50 
comision = 0.20
archivo_memoria = "memoria_quantum.txt"

# === CONTADORES CAJA 1 ===
capital_base = 30.00
ganado = 0.0
perdido = 0.0
contador_ops = 0
en_operacion = False

def registrar(tipo, msg, valor=0):
    global contador_ops, ganado, perdido
    ts = datetime.now().strftime('%H:%M:%S')
    try:
        with open(archivo_memoria, "a") as f:
            f.write(f"[{ts}] {tipo} | {msg} | ${valor:.4f}\n")
    except: pass
    if tipo == "CIERRE":
        contador_ops += 1
        if valor > 0: ganado += valor
        else: perdido += abs(valor)

print("🚀 SCANNER QUANTUM ACTIVADO - PREPARADO PARA CAPTURA DE PANTALLA")

while True:
    try:
        # 1. CAPTURA TÉCNICA
        sol = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
        btc = float(client.get_symbol_ticker(symbol="BTCUSDT")['price'])
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=50)
        
        # Cálculos de ADN
        cierres = [float(k[4]) for k in klines]
        ema = sum(cierres) / 50
        dist_x = abs(((ema - sol) / sol) * 100)
        # DX (Electricidad): Diferencia entre máximo y mínimo en 14 periodos
        dx = round(((max(cierres[-14:]) - min(cierres[-14:])) / ema * 1000), 2)
        
        # Lectura de Velas (Biblioteca)
        v_actual_color = "VERDE 🟢" if sol > float(klines[-1][1]) else "ROJA 🔴"
        v_ant_color = "VERDE 🟢" if float(klines[-2][4]) > float(klines[-2][1]) else "ROJA 🔴"
        
        neto_total = ganado - perdido

        # --- 📊 TABLERO DE ANÁLISIS TÉCNICO (Sácale foto a esto) ---
        print("\n" + "═"*60)
        print(f"🔱 ALE IA QUANTUM | {datetime.now().strftime('%H:%M:%S')} | CAJA 1")
        print(f"💰 NETO TOTAL: ${neto_total:.2f} | CAP: ${capital_base + neto_total:.2f}")
        print(f"✅ GAN: +${ganado:.2f} | ❌ PERD: -${perdido:.2f} | 🔢 OPS: {contador_ops}")
        print("-" * 60)
        print(f"📈 PRECIO SOL: ${sol:.2f}  |  🍊 BTC: ${btc:.0f}")
        print(f"⚡ ELECTRICIDAD (DX): {dx}") 
        print(f"📏 DISTANCIA X: {dist_x:.2f}% (Meta: 0.60%)")
        print(f"🕯️ VELAS: [Ant: {v_ant_color}] -> [Hoy: {v_actual_color}]")
        print(f"🎯 META OP: {ganancia_neta_ale}% NETO (+{comision}% Comis.)")
        print("═"*60)

        # Lógica de Operación
        if not en_operacion:
            # Entrada por ruptura y color (Sentimiento de vela)
            if dist_x >= 0.60 and dx >= 20:
                if sol > float(klines[-1][1]) and sol > float(klines[-2][4]):
                    en_operacion = True
                    p_entrada = sol
                    tipo_op = "LONG 🟢"
                    registrar("ENTRADA", f"LONG a ${sol}")
                elif sol < float(klines[-1][1]) and sol < float(klines[-2][4]):
                    en_operacion = True
                    p_entrada = sol
                    tipo_op = "SHORT 🔴"
                    registrar("ENTRADA", f"SHORT a ${sol}")
        else:
            # Salida Ametralladora
            diff = ((sol - p_entrada) / p_entrada) if "LONG" in tipo_op else ((p_entrada - sol) / p_entrada)
            roi_neto = (diff * 100 * palanca) - comision
            if roi_neto >= ganancia_neta_ale or roi_neto <= -0.7:
                registrar("CIERRE", f"{tipo_op} Fin", (capital_base * (roi_neto/100)))
                en_operacion = False

        time.sleep(espera_segundos)
    except Exception as e:
        time.sleep(10)
