import os, time
import pandas as pd
from binance.client import Client

# Conexión con tus llaves seguras
def c(): return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
cl = c(); ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']

# Neto real de tus últimos logs
cap_actual = 20.50 
MIN_LOT = 15.0 # Mínimo de Binance para que no te rebote la orden

st = {m: {'e': False, 'p': 0, 't': '', 'm': -9.0} for m in ms}

def analizar_fisica_ale(df):
    # Ejes de tu dibujo
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()   # Sensor (Sigue la vela)
    df['ema_27'] = df['close'].ewm(span=27, adjust=False).mean() # Eje central i
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean() # El Muro (Resistencia/Soporte)
    
    e9 = df['ema_9'].iloc[-1]; e27 = df['ema_27'].iloc[-1]
    e9_p = df['ema_9'].iloc[-2]; e27_p = df['ema_27'].iloc[-2]
    
    # ENTRADA: Cruce exacto (Funciona para Subida y Bajada)
    if e9 < e27 and e9_p >= e27_p: return "🟥" # SHORT (Baja)
    if e9 > e27 and e9_p <= e27_p: return "🟩" # LONG (Suba)
    return "."

print(f"🔱 IA QUANTUM | MODO ANTICIPACIÓN 200 | NETO: ${cap_actual}")

while True:
    try:
        op_activas = sum(1 for m in ms if st[m]['e'])
        
        for m in ms:
            s = st[m]
            # Usamos 200 velas para que la EMA 200 sea exacta
            k = cl.get_klines(symbol=m, interval='1m', limit=200)
            df = pd.DataFrame(k, columns=['t','open','high','low','close','v','ct','qv','nt','tb','tq','i'])
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            px = df['close'].iloc[-1]
            
            if not s['e']:
                if op_activas < 1: 
                    senal = analizar_fisica_ale(df)
                    if senal != ".":
                        s['t'] = "LONG" if senal == "🟩" else "SHORT"
                        s['p'], s['e'], s['m'] = px, True, -9.0
                        op_activas += 1
                        print(f"\n🎯 DISPARO EN {m} ({s['t']}) | Usando $15 | Buscando la 200...")
            else:
                # ROI con x10 (Binance)
                roi = (((px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']) * 100 * 10) - 0.22
                if roi > s['m']: s['m'] = roi 
                
                # CÁLCULO DE LA PARED (EMA 200)
                ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
                ema_27 = df['close'].ewm(span=27, adjust=False).mean().iloc[-1]
                distancia_a_200 = abs(px - ema_200) / ema_200
                
                # --- LÓGICA DE SALIDA ANTICIPADA (TU PATRÓN) ---
                # 1. Salida por Rechazo en la 200 (Vender en verde/Comprar en rojo antes del choque)
                rechazo = False
                if distancia_a_200 < 0.0015: # Si está muy cerca de la 200
                    high = df['high'].iloc[-1]; low = df['low'].iloc[-1]; op = df['open'].iloc[-1]
                    if s['t'] == "LONG" and (high - px) > (px - op): rechazo = True # Mecha arriba (Lápida)
                    if s['t'] == "SHORT" and (px - low) > (op - px): rechazo = True # Mecha abajo (Martillo)

                # 2. Salida por Eje 27 (Tu dibujo original)
                toca_27 = (s['t'] == "LONG" and px <= ema_27) or (s['t'] == "SHORT" and px >= ema_27)
                
                # 3. Trailing Stop de seguridad (1.8%)
                trail = (s['m'] >= 1.8 and roi <= (s['m'] - 0.4))

                if rechazo or toca_27 or trail or roi <= -1.2:
                    ganancia_usd = (MIN_LOT * (roi / 100))
                    cap_actual += ganancia_usd
                    s['e'] = False
                    op_activas -= 1
                    motivo = "RECHAZO 200" if rechazo else ("EJE 27" if toca_27 else "TRAILING")
                    print(f"⏱️ SALIDA {m} por {motivo} | ROI: {roi:.2f}% | NETO: ${cap_actual:.2f}")

        time.sleep(15) # Respetamos los 15s de Binance
    except:
        time.sleep(10); cl = c()
