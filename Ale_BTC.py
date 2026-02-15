import os, time, redis, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from binance.client import Client

# --- SERVER DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- MEMORIA SOLO PARA PROGRESO REAL ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def guardar_progreso(nuevo_cap):
    if r:
        try: r.set("cap_v147_real", str(nuevo_cap))
        except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # Buscador de llaves (APY o API)
    ak = os.getenv("BINANCE_APY_KEY") or os.getenv("BINANCE_API_KEY")
    as_ = os.getenv("BINANCE_APY_SECRET") or os.getenv("BINANCE_API_SECRET")

    print(f"🚀 INICIANDO V147 - BASE REAL: $15.00")
    
    c = None
    if ak and as_:
        try:
            c = Client(ak, as_)
            print("✅ CLIENTE CONECTADO")
        except:
            print("❌ ERROR DE LLAVES")

    ops = []
    cap = 15.00 # Empezamos de cero con tu capital real

    while True:
        try:
            if c:
                # Intentamos actualizar el saldo con la realidad de Binance
                try:
                    bal = c.futures_account_balance()
                    for b in bal:
                        if b['asset'] == 'USDT':
                            cap = float(b['balance'])
                            guardar_progreso(cap) # Solo guarda si es un saldo real
                            break
                except:
                    pass

            # --- LÓGICA DE TRADING ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = diff * 100 * o['x']
                
                # Cierres
                if roi >= 1.5 or roi <= -0.9:
                    side = "SELL" if o['l'] == "LONG" else "BUY"
                    c.futures_create_order(symbol=o['s'], side=side, type='MARKET', quantity=o['q'])
                    ops.remove(o)
                    print(f"✅ POSICIÓN CERRADA")

            # --- ENTRADAS (90% de los $15 reales) ---
            if len(ops) < 2 and cap >= 10:
                for m in ['PEPEUSDT', 'DOGEUSDT', 'SOLUSDT']:
                    if any(x['s'] == m for x in ops): continue
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    if cl[-2] > e9 and e9 > e27:
                        precio = cl[-1]
                        # Calcula la cantidad para que entre justa en tus $15
                        qty = round((cap * 0.9 * 5) / precio, 0)
                        if qty > 0:
                            c.futures_change_leverage(symbol=m, leverage=5)
                            c.futures_create_order(symbol=m, side='BUY', type='MARKET', quantity=qty)
                            ops.append({'s':m,'l':'LONG','p':precio,'x':5,'q':qty})
                            print(f"🎯 COMPRA REAL EN {m}")
                            break

            print(f"💰 CAPITAL ACTUAL: ${cap:.2f} | Activas: {len(ops)}", end='\r')

        except Exception as e:
            print(f"⚠️ Log: {e}")
            time.sleep(10)
        
        time.sleep(10)

if __name__ == "__main__":
    bot()
