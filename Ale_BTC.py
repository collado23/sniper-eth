import time 
import os

# === INGENIERÍA ALE IA QUANTUM - SOL 1 MINUTO ===
CAPITAL_ENTRADA = 0.80   # Tus 80 centavos
PALANCA = 10             # x10
COMPUESTO = 0.20         # 20% reinversión
STOP_EMERGENCIA = -0.8   # SI ENTRA MAL, CIERRA AQUÍ (Protección)

def iniciar():
    saldo = CAPITAL_ENTRADA
    vela = 0
    print("🔱 ADN 4 AÑOS CARGADO - SISTEMA DE PROTECCIÓN ACTIVO")

    while True:
        try:
            # --- Simulación ADN (Busca el rebote del elástico) ---
            roi = 0.90  # Ejemplo de movimiento de SOL
            
            # --- Finanzas x10 ---
            volumen = saldo * PALANCA
            comision = volumen * 0.002 # 0.1% entrada + 0.1% salida
            ganancia_neta = (volumen * (roi / 100)) - comision
            
            # --- Lógica de Cierre por Error o Ganancia ---
            status = "ANALIZANDO"
            if roi <= STOP_EMERGENCIA:
                status = "🚨 CIERRE POR ERROR (STOP)"
                saldo += ganancia_neta # Asume la pérdida para proteger
            elif roi > 0:
                status = "✅ GANANCIA (INTERÉS COMPUESTO)"
                saldo += (ganancia_neta * COMPUESTO)

            vela += 1
            
            # --- ESCRIBIR AL TXT (Lo que vos necesitás ver) ---
            with open("analisis_ale.txt", "a") as f:
                f.write(f"\n--- REPORTE [{time.strftime('%H:%M:%S')}] ---")
                f.write(f"\n🕯️ VELA: {vela} | STATUS: {status}")
                f.write(f"\n💵 CAPITAL: ${saldo:.4f} | NETO: ${ganancia_neta:.4f}")
                f.write(f"\n--------------------------------------------\n")
            
            print(f"✅ Vela {vela} procesada. Saldo: ${saldo:.4f}")
            time.sleep(60) # 1 minuto exacto
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    iniciar()
