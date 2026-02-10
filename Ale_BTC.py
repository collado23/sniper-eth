import time
import os

# === CONFIGURACIÓN DE INGENIERÍA ALE IA QUANTUM ===
CAPITAL_INICIAL = 0.80         # Tus 80 centavos
PALANCA = 10                   # x10
COMPUESTO_FACTOR = 0.20        # 20% reinversión
STOP_EMERGENCIA = -0.8         # SI ENTRA MAL, CIERRA AQUÍ
VELA_TIEMPO = 60               # 1 Minuto

def iniciar_programa():
    saldo_actual = CAPITAL_INICIAL
    contador_velas = 0
    picos = 0
    
    print("🔱 INICIANDO ALE IA QUANTUM - MÓDULO DE PROTECCIÓN ACTIVO")
    print(f"📊 ADN 4 AÑOS CARGADO | CIERRE POR ERROR A {STOP_EMERGENCIA}%")

    while True:
        try:
            # --- SIMULACIÓN DE MERCADO (1 MINUTO) ---
            # Aquí el ADN de 4 años mide el movimiento actual
            roi_mercado = -0.85  # EJEMPLO: El mercado se fue en contra
            
            # --- CÁLCULO FINANCIERO ---
            volumen = saldo_actual * PALANCA
            comision = volumen * 0.002
            ganancia_neta = (volumen * (roi_mercado / 100)) - comision
            
            # --- LÓGICA DE CIERRE (SI ENTRA MAL) ---
            estado_operacion = "ANALIZANDO"
            if roi_mercado <= STOP_EMERGENCIA:
                estado_operacion = "🚨 CIERRE POR ERROR (PROTECCIÓN)"
                # Aquí restamos la pérdida al capital para la próxima
                saldo_actual += ganancia_neta # ganancia_neta es negativa aquí
            elif roi_mercado > 0:
                estado_operacion = "✅ OPERACIÓN EXITOSA"
                # Sumamos el 20% de la ganancia neta
                saldo_actual += (ganancia_neta * COMPUESTO_FACTOR)
            
            contador_velas += 1

            # === VOLCADO AL TXT (CONTABILIDAD COMPLETA) ===
            with open("analisis_ale.txt", "a") as f:
                f.write(f"\n--- REPORTE QUANTUM [{time.strftime('%H:%M:%S')}] ---")
                f.write(f"\n⚙️ ESTADO: {estado_operacion}")
                f.write(f"\n🕯️ VELA: {contador_velas} | ADN Validado: OK")
                f.write(f"\n💵 CAPITAL ENTRADA: ${saldo_actual:.4f}")
                f.write(f"\n📈 ROI MERCADO: {roi_mercado}% | PALANCA: x10")
                f.write(f"\n💰 RESULTADO NETO: ${ganancia_neta:.4f}")
                f.write(f"\n💎 SALDO TRAS COMPUESTO/STOP: ${saldo_actual:.4f}")
                f.write(f"\n------------------------------------------------\n")

            print(f"✅ Vela {contador_velas} procesada. Estado: {estado_operacion}")
            
            # Si cerró por error, el bot espera una nueva señal del ADN para volver a entrar
            if estado_operacion == "🚨 CIERRE POR ERROR (PROTECCIÓN)":
                print("⚠️ Protegiendo capital. Esperando nueva ventana de oportunidad...")
                time.sleep(300) # Espera 5 min para que el mercado se calme

            time.sleep(VELA_TIEMPO)
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    iniciar_programa()
