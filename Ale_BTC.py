import os, time, pandas as pd, numpy as np
import yfinance as yf
from binance.client import Client

# --- CONFIGURACIÓN ---
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
archivo_memoria = "espejo_cuantico.txt"

def registrar_en_espejo(elasticidad, roi):
    """ Guarda el patrón exitoso para que el bot aprenda de la inercia """
    try:
        with open(archivo_memoria, "a") as f:
            f.write(f"{int(time.time())},{elasticidad:.2f},{roi:.2f}\n")
        print(f"📝 Patrón guardado: Elástico {elasticidad}% -> Ganancia {roi}%")
    except Exception as e:
        print(f"⚠️ Error al escribir memoria: {e}")

def analizar_adn_inicial():
    print("📡 Sincronizando 4 años de historia (Yahoo Finance)...")
    data = yf.download("SOL-USD", period="5y", interval="1d", progress=False)
    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
    df = data.copy()
    df['ema'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['elast'] = ((df['Close'] - df['ema']) / df['ema']) * 100
    picos = df[abs(df['elast']) > 2.5][['Close', 'elast']].copy()
    print(f"✅ ADN cargado: {len(picos)} patrones de alta elasticidad listos.")
    return picos

MEMORIA_ADN = analizar_adn_inicial()

def ejecutar_v12_2():
    print("🔱 GLADIADOR V12.2: RITMO 15s | TRAILING 0.6% | AUTO-MEMORIA")
    p_entrada = 0
    en_operacion = False
    max_roi = 0
    elast_entrada = 0

    while True:
        try:
            # 1. Pulso del mercado (Velas 1m)
            k = client.futures_klines(symbol="SOLUSDT", interval='1m', limit=200)
            df = pd.DataFrame(k).astype(float)
            p_actual = df[4].iloc[-1]
            ema_actual = df[4].ewm(span=200, adjust=False).mean().iloc[-1]
            elast_actual = ((p_actual - ema_actual) / ema_actual) * 100
            
            # 2. Monitor de Control
            print(f"📊 SOL: {p_actual:.2f} | 🧲 Elástico: {elast_actual:+.2f}%")

            # 3. Disparo por Tensión Histórica
            if not en_operacion and abs(elast_actual) >= 2.5:
                coincidencias = MEMORIA_ADN[abs(MEMORIA_ADN['elast'] - elast_actual) < 0.2]
                if not coincidencias.empty:
                    p_entrada = p_actual
                    elast_entrada = elast_actual
                    en_operacion = True
                    max_roi = 0
                    print(f"🚀 ¡REFLEJO ACTIVADO! Entrando en el pico de {elast_actual:.2f}%")

            # 4. Trailing Stop de 0.6% (Protección de Inercia)
            if en_operacion:
                # ROI según dirección
                roi_actual = ((p_entrada - p_actual) / p_entrada) * 100 if elast_entrada > 0 else ((p_actual - p_entrada) / p_entrada) * 100
                if roi_actual > max_roi: max_roi = roi_actual
                
                print(f"📈 ROI Actual: {roi_actual:+.2f}% | 🎯 Máximo Alcanzado: {max_roi:+.2f}%")

                # CIERRE INTELIGENTE: Si el ROI cae 0.6% desde su punto más alto (después de ganar al menos 1%)
                if max_roi > 1.0 and roi_actual < (max_roi - 0.6):
                    print(f"💰 CIERRE ESTRATÉGICO: Ganancia Final {roi_actual:.2f}%")
                    registrar_en_espejo(elast_entrada, roi_actual)
                    en_operacion = False
                    max_roi = 0

            # 5. Pausa de 15 segundos para estabilidad
            time.sleep(15) 

        except Exception as e:
            print(f"⚠️ Error: {e}"); time.sleep(20)

if __name__ == "__main__":
    ejecutar_v12_2()
