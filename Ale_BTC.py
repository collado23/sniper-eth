import os, time, pandas as pd, numpy as np
from binance.client import Client
from datetime import datetime

# --- CONFIGURACIÓN ---
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

symbol_sol = "SOLUSDT"
symbol_btc = "BTCUSDT"
cantidad_prueba = 0.1  
archivo_memoria = "memoria_gladiador.txt"

def descargar_y_registrar_historia():
    """Descarga los últimos años disponibles y los guarda en el TXT como base de conocimiento"""
    print("⏳ Iniciando descarga de 4 años (o máximo disponible) de SOL...")
    try:
        # Pedimos velas de 1 hora para procesar años rápidamente sin bloquear la API
        # '1 Jan, 2021' es el punto de partida ideal para SOL en Futuros
        historico = client.futures_historical_klines(symbol_sol, '1h', '1 Jan, 2021')
        
        df = pd.DataFrame(historico, columns=['t','o','h','l','c','v','ct','q','n','tb','tq','i'])
        df['c'] = df['c'].astype(float)
        ema = df['c'].ewm(span=200, adjust=False).mean()
        df['dist'] = ((df['c'] - ema) / ema) * 100
        
        # Guardamos un resumen en el TXT para que el bot tenga el 'Mapa Espejo'
        with open(archivo_memoria, "a") as f:
            f.write(f"\n--- BASE DE DATOS HISTÓRICA CARGADA EL {datetime.now()} ---\n")
            # Registramos solo los puntos de alta tensión (elásticos estirados) del pasado
            puntos_criticos = df[abs(df['dist']) > 2.0]
            for index, row in puntos_criticos.tail(100).iterrows(): # Guardamos los últimos 100 hitos
                f.write(f"HISTORIA | Precio: {row['c']} | Distancia: {row['dist']:.2f}%\n")
        
        limite_sugerido = round(df['dist'].abs().quantile(0.95), 2)
        print(f"✅ Historia registrada. Límite espejo sugerido: {limite_sugerido}%")
        return limite_sugerido
    except Exception as e:
        print(f"⚠️ Error en descarga histórica: {e}")
        return 2.45 # Valor seguro por defecto si falla la descarga

# --- INICIO DEL CEREBRO ---
LIMITE_DINAMICO = descargar_y_registrar_historia()

def guardar_log(precio, dist, pnl, motivo, adx, btc_dist):
    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
    log = (f"[{fecha}] SOL: {precio:.2f} (Dist: {dist:.2f}%) | BTC_Dist: {btc_dist:.2f}% | "
           f"ADX: {adx:.1f} | ROI: {pnl:.2f}% | MOTIVO: {motivo}\n")
    with open(archivo_memoria, "a") as f:
        f.write(log)

def calcular_adx(df, period=14):
    df = df.copy()
    df['h-l'] = df['high'] - df['low']; df['h-pc'] = abs(df['high'] - df['close'].shift(1))
    df['l-pc'] = abs(df['low'] - df['close'].shift(1)); df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
    df['up'] = df['high'] - df['high'].shift(1); df['dn'] = df['low'].shift(1) - df['low']
    df['+dm'] = np.where((df['up'] > df['dn']) & (df['up'] > 0), df['up'], 0)
    df['-dm'] = np.where((df['dn'] > df['up']) & (df['dn'] > 0), df['dn'], 0)
    tr_s = df['tr'].rolling(window=period).sum(); dp_s = df['+dm'].rolling(window=period).sum(); dm_s = df['-dm'].rolling(window=period).sum()
    df['+di'] = 100 * (dp_s / tr_s); df['-di'] = 100 * (dm_s / tr_s)
    df['dx'] = 100 * abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])
    return df['dx'].rolling(window=period).mean().iloc[-1]

def ejecutar_v8():
    print(f"🔱 GLADIADOR V8: MODO ESPEJO Y OPERACIÓN ACTIVA")
    precio_max = 0
    
    while True:
        try:
            # Datos actuales
            k_s = client.futures_klines(symbol=symbol_sol, interval='1m', limit=100)
            k_b = client.futures_klines(symbol=symbol_btc, interval='1m', limit=100)
            df_s = pd.DataFrame(k_s, columns=['t','open','high','low','close','v','ct','q','n','tb','tq','i']).astype(float)
            df_b = pd.DataFrame(k_b).astype(float)
            
            p_s = df_s['close'].iloc[-1]; p_b = df_b[4].iloc[-1]
            ema_s = df_s['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            ema_b = df_b[4].ewm(span=200, adjust=False).mean().iloc[-1]
            
            dist_s = ((p_s - ema_s) / ema_s) * 100
            dist_b = ((p_b - ema_b) / ema_b) * 100
            adx_v = calcular_adx(df_s)

            # Análisis de Velas (El "Espejo" del patrón)
            v = df_s.iloc[-1]
            es_giro = (v['high'] - max(v['open'], v['close'])) > abs(v['close'] - v['open']) or \
                       (min(v['open'], v['close']) - v['low']) > abs(v['close'] - v['open'])

            # Revisar Posición
            pos = client.futures_position_information(symbol=symbol_sol)
            amt = float(next(p for p in pos if p['symbol'] == symbol_sol)['positionAmt'])

            # Lógica de Entrada
            if amt == 0:
                # Dispara si la distancia actual coincide con el 'Espejo Histórico' y hay vela de giro
                if abs(dist_s) >= LIMITE_DINAMICO and abs(dist_b) >= 1.0 and es_giro:
                    side = 'SELL' if dist_s > 0 else 'BUY'
                    client.futures_create_order(symbol=symbol_sol, side=side, type='MARKET', quantity=cantidad_prueba)
                    guardar_log(p_s, dist_s, 0, f"🚀 ENTRADA ESPEJO {side}", adx_v, dist_b)

            # Lógica de Cierre
            else:
                ent = float(next(p for p in pos if p['symbol'] == symbol_sol)['entryPrice'])
                pnl = ((p_s - ent) / ent * 100) if amt > 0 else ((ent - p_s) / ent * 100)
                if abs(dist_s) < 0.2 or pnl < -1.5: # Cierre por retorno a EMA o Stop Loss
                    client.futures_create_order(symbol=symbol_sol, side='SELL' if amt > 0 else 'BUY', type='MARKET', quantity=abs(amt))
                    guardar_log(p_s, dist_s, pnl, "🎯 CIERRE DE OPERACIÓN", adx_v, dist_b)

            print(f"📊 SOL: {p_s:.2f} ({dist_s:.2f}%) | Límite Histórico: {LIMITE_DINAMICO}% | ADX: {adx_v:.1f}")
            time.sleep(20)
        except Exception as e:
            print(f"⚠️ Error: {e}"); time.sleep(30)

if __name__ == "__main__":
    ejecutar_v8()
