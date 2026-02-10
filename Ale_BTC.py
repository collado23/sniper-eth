import os
import time
import socket
from datetime import datetime, timedelta
from binance.client import Client

# === 1. CONFIGURACIÓN DE LLAVES (NOMBRES EXACTOS) ===
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# === 2. PARÁMETROS DE ESTRATEGIA ===
CAPITAL_INICIAL = 30.00
capital_actual = 30.00
palanca = 10
distancia_gatillo = 2.0   # Elástico (2%)
stop_loss_fijo = -0.8     # Seguridad máxima
trailing_activacion = 1.5 # Empieza a apretar al 1.5% de ROI
media_200_fija = 84.34    # Referencia para el elástico

# === 3. CONTADORES DE BATALLA ===
op_ganadas = 0
op_perdidas = 0
inicio_sesion = datetime.now()

# === FUNCIÓN DE SEGURIDAD DE RED ===
def esperar_red():
    print("⏳ Verificando conexión a internet...")
    while True:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            print("✅ Red detectada. Conectando a Binance...")
            break
        except OSError:
            time.sleep(5)

# === INICIO DEL MOTOR ===
esperar_red()
try:
    client = Client(API_KEY, API_SECRET)
    print("✅ CONEXIÓN EXITOSA CON BINANCE API")
except Exception as e:
    print(f"❌ ERROR CRÍTICO API: {e}")

def obtener_precio_real():
    try:
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        return float(ticker['price'])
    except Exception as e:
        print(f"⚠️ Error de lectura: {e}")
        return None

# === BUCLE PRINCIPAL (CADA 15 SEGUNDOS) ===
while True:
    try:
        precio = obtener_precio_real()
        if precio is None:
            time.sleep(5)
            continue

        # --- CÁLCULO DE DISTANCIA ---
        if precio < media_200_fija:
            sentido = "LONG (Suba) 🟢"
            distancia = ((media_200_fija - precio) / precio) * 100
        else:
            sentido = "SHORT (Baja) 🔴"
            distancia = ((precio - media_200_fija) / precio) * 100

        # --- TABLERO VISUAL ---
        tiempo_activo = str(datetime.now() - inicio_sesion).split('.')[0]
        
        print("\n" + "═"*50)
        print(f"🔱 ALE IA QUANTUM | {tiempo_activo} EN LÍNEA")
        print(f"💰 CAPITAL: ${capital_actual:.2f} | NETO: ${capital_actual - 30:.2f}")
        print(f"✅ G: {op_ganadas} | ❌ P: {op_perdidas} | 🔄 TOTAL: {op_ganadas+op_perdidas}")
        print("-" * 50)
        print(f"📈 PRECIO SOL: ${precio:.2f} | 📏 DISTANCIA: {distancia:.2f}%")
        print(f"📡 ADN DETECTA: {sentido}")
        
        # --- GATILLO SCALPER ---
        if distancia >= distancia_gatillo:
            print("🎯 !!! GATILLO ACTIVADO !!! Analizando ROI y Trailing...")
            # Lógica interna de simulación aquí
        else:
            print("🔍 BUSCANDO ELÁSTICO AL 2.0%")
        
        print("═"*50)

        # --- REGISTRO DE ARCHIVOS ---
        with open("analisis_ale.txt", "a") as f:
            f.write(f"\n[{datetime.now().strftime('%H:%M:%S')}] SOL: {precio} | DIST: {distancia:.2f}% | OP: {op_ganadas+op_perdidas}")

        # --- REPORTE DIARIO ---
        if datetime.now() >= inicio_sesion + timedelta(hours=24):
            with open("balance_diario.txt", "a") as f:
                f.write(f"\nCIERRE 24H: {datetime.now()} | Cap: {capital_actual} | G: {op_ganadas} | P: {op_perdidas}")
            print("📢 Balance de 24hs guardado.")

        time.sleep(15)

    except Exception as e:
        print(f"⚠️ Error en el bucle: {e}")
        time.sleep(10)
