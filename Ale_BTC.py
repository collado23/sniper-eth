import time

# === CONFIGURACIÓN DE INGENIERÍA SOL 1 MINUTO (x10) === 
CAPITAL_INICIAL = 10.0          # Tus $10 USD reales
APALANCAMIENTO = 10             # x10
INTERES_COMPUESTO_FACTOR = 0.20 # 20% para reinvertir
STOP_SEGURIDAD = -0.8           # Tu stop de -0.8%
COMISION_BINANCE = 0.001        # 0.1% de comisión

# Variables de Seguimiento
saldo_acumulado = CAPITAL_INICIAL
contador_velas_bajada = 0
contador_velas_subida_previa = 15 # Ajustable según el espejo que veas
picos_detectados = 0

def calcular_resultado_plata(roi_mercado):
    """Calcula la ganancia real en USD usando x10 y restando comisiones"""
    poder_compra = saldo_acumulado * APALANCAMIENTO
    ganancia_bruta = poder_compra * (roi_mercado / 100)
    # Comisión de entrada y salida
    comisiones = poder_compra * COMISION_BINANCE * 2
    return ganancia_bruta - comisiones

def ejecutar_ingenieria_sol():
    global saldo_acumulado, contador_velas_bajada, picos_detectados
    
    print(f"🔱 --- MÓDULO SOL 1 MINUTO ACTIVADO (x10) ---")
    print(f"💰 Capital Base: ${saldo_acumulado} | Inversión: ${saldo_acumulado*APALANCAMIENTO}")

    while True:
        # --- ENTRADA DE DATOS (Simulado para 1 min) ---
        # Aquí el bot leería el precio de SOL cada 60 segundos
        roi_mercado_actual = 0.95 # Ejemplo: movimiento de SOL del 0.95%
        
        # 1. CONTADOR DE VELAS (SIMETRÍA 1 MINUTO)
        contador_velas_bajada += 1
        
        # 2. CÁLCULO DE GANANCIA EN PLATA
        resultado_usd = calcular_resultado_plata(roi_mercado_actual)
        
        # 3. INTERÉS COMPUESTO (Si hay ganancia, sumamos el 20% al capital base)
        if resultado_usd > 0:
            saldo_acumulado += (resultado_usd * INTERES_COMPUESTO_FACTOR)
        
        # --- VOLCADO AL TXT (ANÁLISIS DE PLATA Y ESPEJO) ---
        with open("analisis_sol_1min.txt", "a") as f:
            f.write(f"\n--- LOG SOL 1min [{time.strftime('%H:%M:%S')}] ---")
            f.write(f"\n🕯️ Vela de 1 min: #{contador_velas_bajada} de {contador_velas_subida_previa}")
            f.write(f"\n📈 ROI Mercado: {roi_mercado_actual}% (x10)")
            f.write(f"\n💵 GANANCIA REAL: ${resultado_usd:.2f} USD")
            f.write(f"\n💎 Capital Base Actualizado: ${saldo_acumulado:.4f} USD")
            f.write(f"\n🔱 Picos detectados: {picos_detectados}/3")
            f.write(f"\n--------------------------------------------\n")

        # 4. LÓGICA DE SALIDA
        if roi_mercado_actual <= STOP_SEGURIDAD:
            print(f"🚨 STOP ALCANZADO: Perdimos centavos, protegiendo capital.")
            break
            
        if contador_velas_bajada >= contador_velas_subida_previa:
            print(f"🔱 ESPEJO COMPLETADO: Revisando salida en Ganancia.")

        # ESPERA DE 60 SEGUNDOS (VELA DE 1 MINUTO)
        time.sleep(60)

if __name__ == "__main__":
    ejecutar_ingenieria_sol()
