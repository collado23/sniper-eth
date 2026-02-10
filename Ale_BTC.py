import os
import time
from datetime import datetime
from binance.client import Client

# === CONFIGURACIÓN DE APIS (Usa tus variables de entorno) ===
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
client = Client(API_KEY, API_SECRET)

# === ADN ALE IA QUANTUM - PARÁMETROS MAESTROS ===
distancia_x_gatillo = 2.0   # Elástico: Distancia a la Media 200
dx_minimo = 25              # Electricidad mínima
dx_maximo = 65              # Techo de seguridad (para no comprar en el pico)
palanca = 10                # Apalancamiento x10
objetivo_neto = 1.5         # 1.5% de ganancia limpia para Ale
espera_segundos = 11        # Límite de seguridad Binance
archivo_memoria = "memoria_quantum.txt"

# === CONTADORES DE CAJA Y CICLO ===
capital_base = 30.00
ganancia_hoy = 0.0
perdida_hoy = 0.0
contador_ops = 0
en_operacion = False

def escribir_biblioteca(tipo, mensaje, resultado=0):
    global contador_ops, ganancia_hoy, perdida_hoy
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(archivo_memoria, "a") as f:
        f.write(f"[{ts}] {tipo} | {mensaje}\n")
    
    if tipo == "CIERRE":
        contador_ops += 1
        if resultado > 0: ganancia_hoy += resultado
        else: perdida_hoy += abs(resultado)
        
        # --- DISPARADOR ANÁLISIS UNO ---
        if contador_ops % 20 == 0:
            neto = ganancia_hoy - perdida_hoy
            resumen = (f"\n--- 🧠 ANÁLISIS UNO (Operación {contador_ops}) ---\n"
                       f"NETO TOTAL: ${neto:.2f} | GANADO: ${ganancia_hoy:.2f} | PERDIDO: ${perdida_hoy:.2f}\n"
                       f"ESTADO: {'EFICIENTE ✅' if neto > 0 else 'REVISAR ADN ⚠️'}\n")
            with open(archivo_memoria, "a") as f:
                f.write(resumen)

def obtener_datos_mercado():
    try:
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=100)
        cierre = [float(k[4]) for k in klines]
        ema_200 = sum(cierre) / len(cierre)
        precio_actual = cierre[-1]
        
        # DX (Electricidad) y Velas (Biblioteca)
        dx = round(((max(cierre[-14:]) - min(cierre[-14:])) / ema_200 * 1000), 2)
        v_verdes = sum(1 for i in range(-3, 0) if float(klines[i][4]) > float(klines[i][1]))
        v_rojas = 3 - v_verdes
        
        return precio_actual, ema_200, dx, v_verdes, v_rojas
    except: return 0, 0, 0, 0, 0

print(f"🔱 ALE IA QUANTUM INICIADO - BUSCANDO 1.5% NETO - CICLO {espera_segundos}s")

while True:
    try:
        precio, ema, dx, verdes, rojas = obtener_datos_mercado()
        if precio == 0: continue
        
        distancia_x = abs(((ema - precio) / precio) * 100)
        neto_actual = ganancia_hoy - perdida_hoy

        # --- TABLERO DE CONTROL EN PANTALLA ---
        print("\n" + "═"*55)
        print(f"🔱 ALE IA QUANTUM | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💎 PRECIO SOL: ${precio:.2f}")
        print(f"💰 CAP: ${capital_base + neto_actual:.2f} | 📈 NETO HOY: ${neto_actual:.2f}")
        print(f"✅ GAN: +${ganancia_hoy:.2f} | ❌ PERD: -${perdida_hoy:.2f}")
        print("-" * 55)
        print(f"📏 DIST X: {distancia_x:.2f}% | ⚡ DX: {dx} | 🕯️ {verdes}V/{rojas}R")
        print(f"🔢 OPS: {contador_ops}/20 (Hacia ANÁLISIS UNO)")
        print("═"*55)

        if not en_operacion:
            # GATILLO DUAL (ALZA Y BAJA)
            sentido = "LONG 🟢" if precio < ema else "SHORT 🔴"
            confirmacion = (verdes >= 1 if sentido == "LONG 🟢" else rojas >= 1)
            
            if distancia_x >= distancia_x_gatillo and dx_minimo <= dx <= dx_maximo and confirmacion:
                en_operacion = True
                precio_entrada = precio
                tipo_op = sentido
                escribir_biblioteca("GATILLO", f"Entrada {sentido} a ${precio} | DX: {dx}")
        
        else:
            # LÓGICA DE SALIDA (BUSCANDO EL 1.5% NETO)
            if "LONG" in tipo_op:
                roi_bruto = ((precio - precio_entrada) / precio_entrada) * 100 * palanca
            else:
                roi_bruto = ((precio_entrada - precio) / precio_entrada) * 100 * palanca
            
            # Descontamos 0.2% de comisiones (Entrada + Salida)
            roi_neto = roi_bruto - 0.20
            
            # Cierre por Objetivo o Stop Loss
            if roi_neto >= objetivo_neto or roi_neto <= -0.8:
                resultado_final = (capital_base * (roi_neto / 100))
                escribir_biblioteca("CIERRE", f"{tipo_op} finalizado. ROI Neto: {roi_neto:.2f}%", resultado_final)
                en_operacion = False
                print(f"🎯 OBJETIVO ALCANZADO: {roi_neto:.2f}%")

        time.sleep(espera_segundos)

    except Exception as e:
        escribir_biblioteca("ERROR", str(e))
        time.sleep(espera_segundos)
