import os, time, threading
from binance.client import Client

def bot():
    # ... (Parte del servidor de salud igual que antes) ...
    
    ak = os.getenv("BINANCE_APY_KEY") or os.getenv("BINANCE_API_KEY")
    as_ = os.getenv("BINANCE_APY_SECRET") or os.getenv("BINANCE_API_SECRET")
    c = Client(ak, as_)
    ops = []
    
    # 🕵️‍♂️ LISTA CHEQUEADA: Estas 4 no fallan nunca en Futuros
    monedas_reales = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT', 'SOLUSDT']

    print(f"🚀 V150 - MONEDAS VERIFICADAS")

    while True:
        try:
            bal = c.futures_account_balance()
            cap = next((float(b['balance']) for b in bal if b['asset'] == 'USDT'), 0.0)

            # --- GESTIÓN DE ENTRADAS ---
            if len(ops) < 2 and cap >= 10:
                for m in monedas_reales:
                    if any(x['s'] == m for x in ops): continue
                    
                    # Pedimos los datos a Binance
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    if cl[-2] > e9 and e9 > e27:
                        precio = float(c.get_symbol_ticker(symbol=m)['price'])
                        
                        # USAMOS EL 65% PARA QUE SOBRE PLATA SÍ O SÍ
                        qty_raw = (cap * 0.65 * 5) / precio
                        
                        # Ajuste de decimales según la moneda (BTC/ETH usan 3, SOL 2, DOGE 1)
                        if 'BTC' in m or 'ETH' in m: qty = round(qty_raw, 3)
                        elif 'SOL' in m: qty = round(qty_raw, 2)
                        else: qty = round(qty_raw, 0)
                        
                        if qty > 0:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side='BUY', type='MARKET', quantity=qty)
                            ops.append({'s':m,'l':'LONG','p':precio,'x':5,'q':qty})
                            print(f"🎯 ADENTRO: {m} | Cant: {qty}")
                            break

            print(f"💰 CAPITAL: ${cap:.2f} | Activas: {len(ops)}", end='\r')

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(10)
        time.sleep(10)
