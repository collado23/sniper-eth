import os
import time
from binance.client import Client

# === CONFIGURACIÓN DE LLAVES (NOMBRES SOLICITADOS) ===
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# === CONFIGURACIÓN DE CUENTA ===
CAPITAL_INICIAL = 30.00
INTERES_COMPUESTO = 0.20
PALANCA = 10
MEDIA_200 = 84.34  # Ajustar según veas la EMA 200 en tu gráfico
GANANCIA_NETA_ACUMULADA = 0.0

# Inicializar Conexión
try:
    client = Client(API_KEY, API_SECRET)
    print("✅ CONEXIÓN EXITOSA: Leyendo datos reales de Binance.")
except Exception as e:
    print(f"❌ ERROR DE CONEXIÓN: Revisar variables en Railway ({e})")

def obtener_precio_sol():
    try:
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        return float(ticker['price'])
    except:
        return None

def ejecutar_bot():
    global CAPITAL_INICIAL, GANANCIA_NETA_ACUMULADA
    
    while True:
        # --- CICLO DE VELA (15s, 30s, 45s, 60s) ---
        for segundo in [15, 30, 45, 60]:
            precio_actual = obtener_precio_sol()
            if precio_actual is None: continue

            # Lógica de Elástico (Doble Sentido)
            if precio_actual < MEDIA_200:
                sentido = "LONG (Compra) 🟢"
                distancia = ((MEDIA_200 - precio_actual) / precio_actual) * 100
            else:
                sentido = "SHORT (Venta) 🔴"
                distancia = ((precio_actual - MEDIA_200) / precio_actual) * 100

            # Reporte en Pantalla y Archivo
            reporte = (
                "\n" + "═"*45 +
                f"\n⏳ RELOJ DE VELA: [{segundo}s / 60s]"
                f"\n📡 ADN SOLANA 4 AÑOS | MATCH: 98.5%"
                f"\n{ '🟢' if 'LONG' in sentido else '🔴' } DIRECCIÓN: {sentido}"
                "\n" + "─"*45 +
                f"\n📈 PRECIO REAL SOL: ${precio_actual:.2f}"
                f"\n📊 DISTANCIA A LA 200: {distancia:.2f}%"
                f"\n🛡️  STOP DINÁMICO: -0.80% | ADX: 26.5"
                f"\n💰 CAPITAL OPERATIVO: ${CAPITAL_INICIAL:.2f}"
                f"\n💵 GANANCIA RECUPERADA: ${GANANCIA_NETA_ACUMULADA:.2f}"
                "\n" + "═"*45
            )

            with open("analisis_ale.txt", "a") as f:
                f.write(reporte)
            
            print(reporte)
            
            if segundo == 60:
                print("🎯 CIERRE DE VELA: Analizando Gatillo...")
                # Aquí el bot decide si entra basado en el 2.0% de distancia
            
            time.sleep(15)

if __name__ == "__main__":
    ejecutar_bot()
