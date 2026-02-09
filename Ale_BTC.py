import os, time, pandas as pd, numpy as np
import yfinance as yf
from binance.client import Client

# --- CONFIGURACIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

def obtener_espejo_yahoo():
    print("📡 Conectando con Yahoo Finanzas para extraer el ADN de 4 años...")
    try:
        # Descargamos SOL-USD directamente desde Yahoo (Data histórica)
        data = yf.download("SOL-USD", period="5y", interval="1d")
        
        # Limpiamos y calculamos la física del elástico
        df = pd.DataFrame(data)
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['distancia'] = ((df['Close'] - df['EMA200']) / df['EMA200']) * 100
        
        # Filtramos los momentos espejo
        espejo = df[abs(df['distancia']) > 2.0][['Close', 'distancia']]
        print(f"✅ ADN cargado: {len(espejo)} patrones históricos encontrados.")
        return espejo
    except Exception as e:
        print(f"⚠️ Error al conectar con Yahoo: {e}")
        return None

# --- CARGAMOS EL CEREBRO AL ARRANCAR ---
MEMORIA_HISTORICA = obtener_espejo_yahoo()

def ejecutar_v9_5():
    print("🔱 GLADIADOR V9.5 ACTIVADO (MODO CELULAR AUTOMÁTICO)")
    
    while True:
        try:
            # 1. Precio actual de Binance
            res = client.futures_symbol_ticker(symbol="SOLUSDT")
            p_s = float(res['price'])
            
            # 2. Obtenemos velas recientes de Binance para la EMA actual
            k = client.futures_klines(symbol="SOLUSDT", interval='1m', limit=200)
            df_now = pd.DataFrame(k).astype(float)
            ema_actual = df_now[4].ewm(span=200, adjust=False).mean().iloc[-1]
            dist_actual = ((p_s - ema_actual) / ema_actual) * 100
            
            # 3. Consultamos el espejo de Yahoo
            prob = 70
            if MEMORIA_HISTORICA is not None:
                # Buscamos coincidencias en el ADN
                coincidencias = MEMORIA_HISTORICA[abs(MEMORIA_HISTORICA['distancia'] - dist_actual) < 0.2]
                if not coincidencias.empty:
                    prob = 95 # ¡Es un reflejo del pasado!

            # --- PANTALLITA ---
            print(f"--------------------------------------------------")
            print(f"📊 SOL: {p_s:.2f} | Distancia: {dist_actual:+.2f}%")
            print(f"🔎 Probabilidad según Yahoo: {prob}%")
            
            # 4. Entrada (0.1 SOL para prueba)
            if abs(dist_actual) >= 2.45 and prob > 90:
                side = 'SELL' if dist_actual > 0 else 'BUY'
                client.futures_create_order(symbol="SOLUSDT", side=side, type='MARKET', quantity=0.1)
                print(f"🚀 ¡ENTRADA CUÁNTICA! Basada en ADN de Yahoo.")

            time.sleep(20)

        except Exception as e:
            print(f"⚠️ Error de sistema: {e}")
            time.sleep(30)

if __name__ == "__main__":
    ejecutar_v9_5()
