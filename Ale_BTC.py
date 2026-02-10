import time
import os

# === CONFIGURACIÓN ALE IA QUANTUM - SOL 1 MINUTO ===
CAPITAL_INICIAL = 0.80         # Tu capital de entrada: 80 centavos
PALANCA = 10                   # x10
COMPUESTO = 0.20               # 20% reinversión
STOP_EMERGENCIA = -0.8         # Tu stop de seguridad

def iniciar_bot():
    saldo_real = CAPITAL_INICIAL
    contador = 0
    print("🔱 SISTEMA SOL ACTIVADO - ENTRADA $0.80 x10")

    while True:
        try:
            # Simulación de mercado para el reporte
            roi_mercado = 0.9  # Simulando el movimiento para tus 80 centavos
            
            # Cálculo de ganancia limpia (80 centavos x 10 = $8 operando)
            volumen = saldo_real * PALANCA
            ganancia_neta = (volumen * (roi_mercado / 100)) - (volumen * 0.002)
            
            # Aplicar tu interés compuesto del 20%
            if ganancia_neta > 0:
                saldo_real += (ganancia_neta * COMPUESTO)
            
            contador += 1
            
            # Volcado rápido al log y archivo
            reporte = (
                f"\n--- REPORTE SOL [{time.strftime('%H:%M:%S')}] ---\n"
                f"💵 Entrada: ${saldo_real:.4f} | 📈 ROI: {roi_mercado}%\n"
                f"💰 Ganancia Neta: ${ganancia_neta:.4f}\n"
                f"🕯️ Vela 1m: #{contador} | Espejo en proceso...\n"
                f"--------------------------------------------"
            )
            
            print(reporte)
            with open("analisis_sol_fijo.txt", "a") as f:
                f.write(reporte)

            time.sleep(60) # 1 minuto exacto
            
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    iniciar_bot()
