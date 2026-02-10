import os
import time
from datetime import datetime, timedelta
from binance.client import Client

# === 1. CONFIGURACIÓN DE LLAVES ===
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# === 2. PARÁMETROS DE ESTRATEGIA (Ajustables) ===
CAPITAL_INICIAL = 30.00
capital_actual = 30.00
interes_compuesto = 0.20
palanca = 10
distancia_gatillo = 2.0  # Elástico
adx_minimo = 25          # Fuerza
stop_loss_fijo = -0.8    # Seguridad
trailing_activacion = 1.5 # Cuando empieza a apretar

# === 3. CONTADORES ===
op_ganadas = 0
op_perdidas = 0
inicio_sesion = datetime.now()

# Inicializar Cliente
client = Client(API_KEY, API_SECRET)

def obtener_datos():
    try:
        ticker = client.get_symbol_ticker(symbol="SOLUSDT")
        return float(ticker['price'])
    except:
        return None

def guardar_balance():
    with open("balance_diario.txt", "a") as f:
        f.write(f"\n[{datetime.now()}] Capital: ${capital_actual:.2f} | G: {op_ganadas} | P: {op_perdidas}")

print("🚀 MOTOR INICIADO - ESPERANDO PRIMER ESCANEO (15s)...")

while True:
    try:
        precio = obtener_datos()
        if precio is None: continue

        # --- LÓGICA DE CÁLCULO (Media 200 estimada o fija para simulación) ---
        media_200 = 84.34 # Aquí podrías poner una función que la traiga de Binance
        
        if precio < media_200:
            sentido = "LONG (Compra) 🟢"
            distancia = ((media_200 - precio) / precio) * 100
        else:
            sentido = "SHORT (Venta) 🔴"
            distancia = ((precio - media_200) / precio) * 100

        # --- TABLERO VISUAL EN PANTALLA ---
        tiempo_vikingo = str(datetime.now() - inicio_sesion).split('.')[0]
        
        print("\n" + "═"*50)
        print(f"🔱 ALE IA QUANTUM | {tiempo_vikingo} ACTIVO")
        print(f"💰 CAPITAL: ${capital_actual:.2f} | NETO: ${capital_actual - 30:.2f}")
        print(f"✅ G: {op_ganadas} | ❌ P: {op_perdidas} | 🔄 TOTAL: {op_ganadas+op_perdidas}")
        print("-" * 50)
        print(f"📈 SOL: ${precio:.2f} | 📏 DIST. 200: {distancia:.2f}%")
        print(f"📡 DIRECCIÓN: {sentido}")
        
        # --- LÓGICA DE GATILLO ---
        if distancia >= distancia_gatillo:
            print("🎯 GATILLO DETECTADO - ANALIZANDO ADN...")
            # Aquí iría tu función de ejecución. 
            # Si gana: op_ganadas += 1 | capital_actual += ganancia
            # Si pierde: op_perdidas += 1 | capital_actual -= perdida
        else:
            print("🔍 BUSCANDO PUNTO DE ENTRADA...")
        
        print("═"*50)

        # --- GUARDAR EN ARCHIVO ---
        with open("analisis_ale.txt", "a") as f:
            f.write(f"\n{datetime.now().strftime('%H:%M:%S')} | SOL: {precio} | DIST: {distancia:.2f}%")

        # --- CIERRE DE CAJA (Cada 24hs) ---
        if datetime.now() >= inicio_sesion + timedelta(hours=24):
            guardar_balance()
            print("📢 BALANCE DIARIO GUARDADO EN balance_diario.txt")

        time.sleep(15) # EL CORAZÓN DEL BOT (15 SEGUNDOS)

    except Exception as e:
        print(f"⚠️ ERROR: {e}")
        time.sleep(10)
