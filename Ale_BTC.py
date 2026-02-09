import os, time, pandas as pd, numpy as np
import yfinance as yf
from binance.client import Client

# --- CONFIGURACIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

def obtener_espejo_yahoo():
    print("📡 Sincronizando ADN de 4 años desde Yahoo Finanzas...")
    try:
        # Descarga optimizada
        data = yf.download("SOL-USD", period="5y", interval="1d", progress=False)
        if data.empty: return None
            
        # Limpieza de MultiIndex (el error que te salió)
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Cálculo de Física Matemática
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['dist'] = ((df['Close'] - df['EMA200']) / df['EMA200']) * 100
        
        # Filtramos momentos de alta tensión histórica
        espejo = df[abs(df['dist']) > 2.0][['Close', 'dist']].copy()
        print(f"✅ ADN Cargado: {len(espejo)} patrones históricos listos.")
        return espejo
    except Exception as e:
        print(f"⚠️ Error en sincronización: {e}")
        return None

# --- INICIO DEL CEREBRO ---
MEMORIA_HISTORICA = obtener_espejo_yahoo()

def ejecutar_v9_7():
    print("🔱 GLADIADOR V9.7: CEREBRO HISTÓRICO ACTIVADO")
    ganancia_acumulada = 0.0
    operaciones = 0

    while True:
        try:
            # 1. Obtener latido actual de Binance
            ticker = client.futures_symbol_ticker(symbol="SOLUSDT")
            p_actual = float(ticker['price'])
            
            # 2. Calcular elástico actual (últimas 200 velas de 1m)
            klines = client.futures_klines(symbol="SOLUSDT", interval='1m', limit=200)
            df_m1 = pd.DataFrame(klines).astype(float)
            ema_m1 = df_m1[4].ewm(span=200, adjust=False).mean().iloc[-1]
            dist_m1 = ((p_actual - ema_m1) / ema_m1) * 100
            
            # 3. Comparación Cuántica con Yahoo
            prob = 70
            matches = 0
            if MEMORIA_HISTORICA is not None:
                # Buscamos si en los últimos 4 años hubo distancias similares (+/- 0.15%)
                coincidencias = MEMORIA_HISTORICA[abs(MEMORIA_HISTORICA['dist'] - dist_m1) < 0.15]
                matches = len(coincidencias)
                if matches > 0:
                    prob = 92 if matches > 2 else 85

            # --- PANTALLITA DE CONTROL ---
            print(f"==================================================")
            print(f"💰 SESIÓN: {ganancia_acumulada:+.2f}% | TRADES: {operaciones}")
            print(f"📊 SOL: {p_actual:.2f} | Elástico: {dist_m1:+.2f}%")
            print(f"🔎 Prob. Espejo: {prob}% | Coincidencias: {matches}")
            print(f"==================================================")

            # 4. Disparo de Prueba (0.1 SOL)
            if abs(dist_m1) >= 2.45 and prob >= 85:
                # Aquí el bot ejecutaría la orden en Binance
                print(f"🚀 ¡REFLEJO DETECTADO! Entrada confirmada por historia.")
                operaciones += 1 # Simulación para el monitor

            time.sleep(20)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    ejecutar_v9_7()
