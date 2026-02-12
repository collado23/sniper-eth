import os, time
import pandas as pd
from binance.client import Client

# Conexión Segura
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')) 
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Estado inicial
cap_actual = 20.50 
MIN_LOT = 15.0 # Operamos con $15 fijos como pediste
st = {m: {'e': False, 'p': 0, 't': '', 'm': -9.0} for m in ms}

def analizar_fisica_ale(df):
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   # Amarilla (Vela)
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() # Azul (Eje)
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean() # El Muro
    
    e9 = df['ema_9'].iloc[-1]; e27 = df['ema_27'].iloc[-1]
    e9_p = df['ema_9'].iloc[-2]; e27_p = df['ema_27'].iloc[-2]
    
    if e9 > e27 and e9_p <= e27_p: return "LONG"   # Cruce hacia arriba
    if e9 < e27 and e9_p >= e27_p: return "SHORT"  # Cruce hacia abajo
    return None

print(f"🔱 IA QUANTUM ACTIVADA | NETO: ${cap_actual} | MODO GIRO TOTAL")

while True:
    try:
        for m in ms:
            s = st[m]
            k = cl.get_klines(symbol=m, interval='1m', limit=200)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px = df['close'].iloc[-1]
            
            nueva_senal = analizar_fisica_ale(df)

            if not s['e']:
                # SI NO HAY OPERACIÓN: Buscamos el primer cruce
                if nueva_senal:
                    s['t'], s['p'], s['e'] = nueva_senal, px, True
                    print(f"🚀 ENTRADA en {m}: {s['t']} a {px} (Iniciando Panza)")
            
            else:
                # SI HAY OPERACIÓN: Calculamos ROI con x10
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                
                # REGLA DE GIRO: Si hay señal contraria, cerramos y abrimos la otra al toque
                if (s['t'] == "LONG" and nueva_senal == "SHORT") or (s['t'] == "SHORT" and nueva_senal == "LONG"):
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    print(f"🔄 GIRO DETECTADO en {m}: Cerrando {s['t']} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")
                    
                    # Abrimos la posición opuesta inmediatamente
                    s['t'], s['p'], s['e'] = nueva_senal, px, True
                    print(f"🚀 NUEVA ENTRADA (Giro): {s['t']} a {px}")

                # REGLA DE CHOQUE (Salida por toque de líneas sin esperar cruce completo)
                ema_27 = df['ema_27'].iloc[-1]
                toca_eje = (s['t'] == "LONG" and px <= ema_27) or (s['t'] == "SHORT" and px >= ema_27)
                
                if toca_eje and not nueva_senal:
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    print(f"⏱️ CIERRE POR CHOQUE en {m} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(15)
    except Exception as e:
        time.sleep(10); cl = c()
