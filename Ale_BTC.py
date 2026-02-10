import os
import time
import socket
import pandas as pd
from datetime import datetime
from binance.client import Client

# === 1. LLAVES API (Se cargan desde Railway) ===
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# === 2. PARÁMETROS DE SIMULACIÓN ===
CAPITAL_INICIAL = 30.00
capital_actual = 30.00
distancia_gatillo = 2.0
op_ganadas = 0
op_perdidas = 0
inicio_sesion = datetime.now()

# === 3. FUNCIÓN DE SEGURIDAD DE RED ===
def esperar_red():
    while True:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except:
            print("⏳ Esperando red para conectar APIs...")
            time.sleep(5)

# === 4. CÁLCULO DE MEDIA 200 REAL ===
def obtener_ema_200(client):
    try:
        klines = client.get_klines(symbol='SOLUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=300)
        df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        df['close'] = df['close'].astype(float)
        ema = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        return round(ema, 2)
    except:
        return 84.34 # Valor de respaldo si falla la lectura

# === 5. MOTOR PRINCIPAL ===
esperar_red()
client = Client(API_KEY, API_SECRET)
print("✅ SISTEMA REINICIADO: Conectado a Binance con éxito.")

while True:
    try:
        precio = float(client.get_symbol_ticker(symbol="SOLUSDT")['price'])
        media_actual = obtener_ema_200(client)
        
        # Cálculo de Elástico Real
        if precio < media_actual:
            sentido = "LONG 🟢"
            distancia = ((media_actual - precio) / precio) * 100
        else:
            sentido = "SHORT 🔴"
            distancia = ((precio - media_actual) / precio) * 100

        # --- TABLERO EN PANTALLA ---
        print("\n" + "═"*50)
        print(f"🔱 ALE IA QUANTUM | {datetime.now().strftime('%H:%M:%S')}")
        print(f"💰 CAPITAL: ${capital_actual:.2f} | ✅ G: {op_ganadas} | ❌ P: {op_perdidas}")
        print("-" * 50)
        print(f"📈 PRECIO SOL: ${precio:.2f} | 🏗️ EMA 200: {media_actual}")
        print(f"📏 DISTANCIA ELÁSTICO: {distancia:.2f}%")
        print(f"📡 ADN DETECTA: {sentido}")
        print("═"*50)

        time.sleep(15)

    except Exception as e:
        print(f"⚠️ Reintentando... ({e})")
        time.sleep(10)
