import pandas as pd
from binance.client import Client
import time

# Conexión simple
client = Client()

def mostrar_adn_para_copiar():
    print("⏳ BUSCANDO ADN DE 4 AÑOS... ESPERE UN MOMENTO...")
    # Bajamos la historia de SOL
    klines = client.futures_historical_klines("SOLUSDT", "1h", "1 Jan, 2021")
    df = pd.DataFrame(klines).astype(float)
    df['ema'] = df[4].ewm(span=200, adjust=False).mean()
    df['dist'] = ((df[4] - df['ema']) / df['ema']) * 100
    
    # Filtramos los momentos espejo
    espejo = df[abs(df['dist']) > 2.0][[0, 4, 'dist']]
    
    print("\n" + "="*50)
    print("👇 COPIÁ DESDE LA SIGUIENTE LÍNEA HASTA EL FINAL 👇")
    print("fecha,precio,distancia")
    for i, row in espejo.iterrows():
        # Formato simple para que GitHub lo entienda
        print(f"{int(row[0])},{row[1]},{row['dist']:.2f}")
    print("👆 FIN DEL ADN 👆")
    print("="*50)

if __name__ == "__main__":
    mostrar_adn_para_copiar()
