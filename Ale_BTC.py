import pandas as pd
from binance.client import Client
import time

# Conexión para datos públicos
client = Client()

def extraer_datos_para_github():
    print("⏳ BUSCANDO 4 AÑOS DE HISTORIA... DAME UN MINUTO...")
    # Bajamos la historia de SOL (Velas de 1 hora para ir rápido)
    klines = client.futures_historical_klines("SOLUSDT", "1h", "1 Jan, 2021")
    
    df = pd.DataFrame(klines).astype(float)
    # 4 es el precio de cierre, calculamos la EMA y la distancia
    df['ema'] = df[4].ewm(span=200, adjust=False).mean()
    df['dist'] = ((df[4] - df['ema']) / df['ema']) * 100
    
    # Filtramos solo los momentos clave (el espejo)
    espejo = df[abs(df['dist']) > 2.0][[0, 4, 'dist']]
    
    print("\n" + "="*40)
    print("👇 COPIÁ DESDE AQUÍ ABAJO 👇")
    print("fecha,precio,distancia") # Encabezado para GitHub
    
    for i, row in espejo.iterrows():
        # Imprime: Fecha (en milisegundos), Precio, Distancia
        print(f"{int(row[0])},{row[1]},{row['dist']:.2f}")
    
    print("👆 HASTA AQUÍ 👆")
    print("="*40)
    print("✅ Proceso terminado. Copiá los números y llevalos a GitHub.")

if __name__ == "__main__":
    extraer_datos_para_github()
