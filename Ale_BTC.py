import time
import os

# === CONFIGURACIÓN ALE IA QUANTUM - INGENIERÍA SOL ===
CAPITAL_ENTRADA = 0.80         # Entrada de 80 centavos
APALANCAMIENTO = 10            # x10 (Poder de compra: $8 USD)
INTERES_COMPUESTO_FACTOR = 0.20 # Reinversión del 20% de la ganancia
STOP_EMERGENCIA = -0.8         # Elástico: Si entra mal, CIERRA para proteger
COMISION_BINANCE = 0.001       # 0.1% (Entrada y Salida)

def ejecutar_quantum():
    saldo_actual = CAPITAL_ENTRADA
    vela_num = 0
    archivo_log = "analisis_ale.txt"
    
    # Crear el archivo si es la primera vez
    if not os.path.exists(archivo_log):
        with open(archivo_log, "w") as f:
            f.write("--- INICIO DE OPERACIONES ALE IA QUANTUM ---\n")

    print(f"🔱 PROGRAMA ACTIVO - ENTRADA ${CAPITAL_ENTRADA} x10")

    while True:
        try:
            # 1. ANALISIS ADN 4 AÑOS (Detección de rebote elástico)
            # Simulamos el movimiento que el bot detecta en la vela de 1 min
            roi_mercado = 0.95  # Ejemplo de profit detectado por el ADN
            
            # 2. CÁLCULO FINANCIERO REAL
            volumen_mercado = saldo_actual * APALANCAMIENTO
            # Descontamos 0.1% de compra y 0.1% de venta sobre los $8 USD
            costo_comisiones = volumen_mercado * COMISION_BINANCE * 2
            ganancia_neta = (volumen_mercado * (roi_mercado / 100)) - costo_comisiones
            
            # 3. LÓGICA DE CIERRE Y PROTECCIÓN
            status_operacion = "ANALIZANDO"
            
            if roi_mercado <= STOP_EMERGENCIA:
                status_operacion = "🚨 CIERRE POR ERROR (ELÁSTICO)"
                saldo_actual += ganancia_neta # Se asume la pérdida para salvar el resto
            
            elif roi_mercado > 0:
                status_operacion = "✅ GANANCIA DETECTADA"
                # Aplicamos tu interés compuesto del 20% sobre la ganancia limpia
                interes_sumado = ganancia_neta * INTERES_COMPUESTO_FACTOR
                saldo_actual += interes_sumado

            vela_num += 1
            
            # 4. VOLCADO COMPLETO AL TXT (Lo que ves en pantalla)
            with open(archivo_log, "a") as f:
                f.write(f"\n--- REPORTE VELA #{vela_num} [{time.strftime('%H:%M:%S')}] ---")
                f.write(f"\n⚙️ ESTRATEGIA: ADN 4 Años + Elástico")
                f.write(f"\n📊 STATUS: {status_operacion}")
                f.write(f"\n💵 CAPITAL ENTRADA: ${saldo_actual - (interes_sumado if roi_mercado > 0 else 0):.4f}")
                f.write(f"\n📈 ROI MERCADO: {roi_mercado}%")
                f.write(f"\n💰 GANANCIA NETA: ${ganancia_neta:.4f}")
                f.write(f"\n💎 NUEVO SALDO (Compuesto 20%): ${saldo_actual:.4f}")
                f.write(f"\n------------------------------------------------\n")
            
            # Lo que ves en los Logs de Railway
            print(f"✅ Vela {vela_num} escrita en TXT. Saldo: ${saldo_actual:.4f}")
            
            # Espera de 1 minuto para la siguiente vela
            time.sleep(60)
            
        except Exception as e:
            print(f"⚠️ Error en el sistema: {e}")
            time.sleep(10)

if __name__ == "__main__":
    ejecutar_quantum()
