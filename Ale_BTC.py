import os, time, pandas as pd, numpy as np
import yfinance as yf
from binance.client import Client

# --- CONFIGURACIÓN ---
client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
archivo_memoria = "espejo_cuantico.txt"

def calcular_adx_manual(df, n=14):
    df = df.copy()
    df['up'] = df[2] - df[2].shift(1)
    df['down'] = df[3].shift(1) - df[3]
    df['+DM'] = np.where((df['up'] > df['down']) & (df['up'] > 0), df['up'], 0)
    df['-DM'] = np.where((df['down'] > df['up']) & (df['down'] > 0), df['down'], 0)
    tr = pd.concat([df[2]-df[3], abs(df[2]-df[4].shift(1)), abs(df[3]-df[4].shift(1))], axis=1).max(axis=1)
    atr = tr.rolling(n).mean()
    p_di = 100 * (df['+DM'].rolling(n).mean() / atr)
    m_di = 100 * (df['-DM'].rolling(n).mean() / atr)
    dx = 100 * abs(p_di - m_di) / (p_di + m_di)
    return dx.rolling(n).mean().iloc[-1]

def analizar_adn_inicial():
    print("📡 Sincronizando 4 años de historia...")
    data = yf.download("SOL-USD", period="5y", interval="1d", progress=False)
    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
    df = data.copy()
    df['ema'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['elast'] = ((df['Close'] - df['ema']) / df['ema']) * 100
    return df[abs(df['elast']) > 2.5][['Close', 'elast']].copy()

MEMORIA_ADN = analizar_adn_inicial()

def ejecutar_v12_3():
    print("🔱 GLADIADOR V12.3 ACTIVADO | MODO PRUEBA 0.1 SOL")
    p_entrada = 0
    en_operacion = False
    max_roi = 0
    elast_entrada = 0
    operaciones_totales = 0

    while True:
        try:
            # 1. Obtener Datos
            k = client.futures_klines(symbol="SOLUSDT", interval='1m', limit=200)
            df = pd.DataFrame(k).astype(float)
            p_actual = df[4].iloc[-1]
            ema_actual = df[4].ewm(span=200, adjust=False).mean().iloc[-1]
            dist_actual = ((p_actual - ema_actual) / ema_actual) * 100
            adx_actual = calcular_adx_manual(df)
            
            # 2. Análisis de Patrones
            coincidencias = len(MEMORIA_ADN[abs(MEMORIA_ADN['elast'] - dist_actual) < 0.2])

            # --- TABLERO DE CONTROL (PANTALLA) ---
            print(f"\n" + "="*45)
            print(f"💰 SOL: {p_actual:.2f} | 📊 TRADES: {operaciones_totales}")
            print(f"🧲 ELÁSTICO: {dist_actual:+.2f}% | 📉 ADX: {adx_actual:.2f}")
            print(f"🧠 COINCIDENCIAS HISTÓRICAS: {coincidencias}")
            
            if en_operacion:
                roi_actual = ((p_entrada - p_actual) / p_entrada) * 100 if elast_entrada > 0 else ((p_actual - p_entrada) / p_entrada) * 100
                if roi_actual > max_roi: max_roi = roi_actual
                print(f"📈 ROI EN VIVO: {roi_actual:+.2f}% | 🎯 MÁX: {max_roi:+.2f}%")
            print("="*45)

            # 3. Disparo (Prueba 0.1 SOL)
            if not en_operacion and abs(dist_actual) >= 2.5 and coincidencias > 0:
                p_entrada = p_actual
                elast_entrada = dist_actual
                en_operacion = True
                max_roi = 0
                operaciones_totales += 1
                side = 'SELL' if dist_actual > 0 else 'BUY'
                # EJECUCIÓN REAL (0.1 SOL)
                client.futures_create_order(symbol="SOLUSDT", side=side, type='MARKET', quantity=0.1)
                print(f"🚀 ENTRADA REAL: {side} @ {p_entrada}")

            # 4. Trailing de 0.6%
            if en_operacion:
                if max_roi > 1.0 and roi_actual < (max_roi - 0.6):
                    print(f"💰 CIERRE: Ganancia {roi_actual:.2f}%")
                    # Registrar en espejo_cuantico.txt
                    with open(archivo_memoria, "a") as f:
                        f.write(f"{int(time.time())},{elast_entrada:.2f},{roi_actual:.2f}\n")
                    en_operacion = False
                    max_roi = 0

            time.sleep(15) 

        except Exception as e:
            print(f"⚠️ Alerta: {e}"); time.sleep(20)

if __name__ == "__main__":
    ejecutar_v12_3()
