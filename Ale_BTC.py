import os, time, redis, threading
from binance.client import Client
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- MEMORIA LIMPIA ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    if not r: return None
    try:
        if leer:
            v = r.get("memoria_v153_limpia")
            return eval(v) if v else None
        else: r.set("memoria_v153_limpia", str(d))
    except: return None

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # Llaves
    ak = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_APY_KEY")
    as_ = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_APY_SECRET")
    c = Client(ak, as_)
    
    # Recuperar memoria limpia
    datos = g_m(leer=True) or {"ops": []}
    ops = datos["ops"]
    
    # SOLO ESTAS 3 - PROHIBIDO CUALQUIER OTRA
    monedas_ok = ['BTCUSDT', 'DOGEUSDT', 'SOLUSDT']

    print(f"🚀 V153 - LIMPIEZA TOTAL - MEMORIA NUEVA")

    while True:
        try:
            # Saldo Real
            bal = c.futures_account_balance()
            cap = next((float(b['balance']) for b in bal if b['asset'] == 'USDT'), 0.0)
            g_m(d={"ops": ops})

            # --- CIERRES ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = diff * 100 * 5
                if roi >= 1.5 or roi <= -0.8:
                    c.futures_create_order(symbol=o['s'], side=("SELL" if o['l']=="LONG" else "BUY"), type='MARKET', quantity=o['q'])
                    ops.remove(o)
                    print(f"✅ CIERRE REALIZADO")
                    break

            # --- ENTRADAS (Al 60% para que no falle el margen) ---
            if len(ops) < 2 and cap >= 10:
                for m in monedas_ok:
                    if any(x['s'] == m for x in ops): continue
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    if cl[-2] > e9 and e9 > e27:
                        precio = float(c.get_symbol_ticker(symbol=m)['price'])
                        # Cantidad ajustada para tus $15
                        qty = round((cap * 0.60 * 5) / precio, 3 if 'BTC' in m else 1)
                        
                        if qty > 0:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side='BUY', type='MARKET', quantity=qty)
                            ops.append({'s':m,'l':'LONG','p':precio,'q':qty})
                            print(f"🎯 COMPRA EXITOSA EN {m}")
                            break

            print(f"💰 REAL: ${cap:.2f} | Activas: {len(ops)}", end='\r')

        except Exception as e:
            print(f"⚠️ Log: {e}")
            time.sleep(10)
        time.sleep(10)

if __name__ == "__main__":
    bot()
