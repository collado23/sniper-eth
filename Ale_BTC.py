import os, time, redis, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from binance.client import Client

# --- 🌐 1. SERVER DE SALUD (Para que el hosting no lo mate) ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK") 
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- 🧠 2. MEMORIA REDIS (Para arrancar con tus $35 virtuales o reales) ---
r = redis.from_url(os.getenv("REDIS_URL")) if os.getenv("REDIS_URL") else None
def g_m(leer=False, d=None):
    c_i = 35.00  # Tu nuevo punto de partida
    if not r: return c_i
    try:
        if leer:
            h = r.get("cap_v145_real")
            return float(h) if h else c_i
        else: r.set("cap_v145_real", str(d))
    except: return c_i

# --- 🚀 3. MOTOR V145 (OPERACIÓN REAL EN BINANCE) ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    # Conexión real con tus llaves de Binance
    c = Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))
    cap = g_m(leer=True)
    ops = []
    
    print(f"🦁 V145 ACTIVADA | FUEGO REAL | Iniciando con: ${cap}")

    while True:
        t_l = time.time()
        try:
            # GESTIÓN DE POSICIONES ABIERTAS
            for o in ops[:]:
                # Consultar precio actual en Binance
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = diff * 100 * o['x']
                
                # Escalada de X Real (5x -> 15x)
                if roi > 0.2 and o['x'] == 5: 
                    o['x'] = 15; o['be'] = True
                    print(f"🔥 SUBIENDO A 15X REAL EN {o['s']}")
                    try: c.futures_change_leverage(symbol=o['s'], leverage=15)
                    except: pass

                # Cierre de Posición Real (Take Profit o Stop Loss)
                if (o['be'] and roi <= 0.05) or roi >= 1.5 or roi <= -0.9:
                    lado_cierre = "SELL" if o['l'] == "LONG" else "BUY"
                    # Orden de cierre a precio de mercado
                    c.futures_create_order(symbol=o['s'], side=lado_cierre, type='MARKET', quantity=o['q'])
                    
                    n_c = cap * (1 + (roi/100))
                    g_m(d=n_c); ops.remove(o); cap = n_c
                    print(f"✅ POSICIÓN CERRADA EN BINANCE | ROI: {roi:.2f}% | NUEVO CAP: ${n_c:.2f}")

            # BUSCAR NUEVA ENTRADA (Cazador Único o hasta 2 monedas)
            if len(ops) < 2:
                for m in ['PEPEUSDT', 'SOLUSDT', 'DOGEUSDT', 'ETHUSDT', 'BTCUSDT']:
                    if any(x['s'] == m for x in ops): continue
                    
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    op = [float(x[1]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    v, o_v = cl[-2], op[-2]

                    # Estrategia validada
                    if v > o_v and v > e9 and e9 > e27:
                        # Entrar LONG
                        precio = cl[-1]
                        qty = round((cap * 0.9 * 5) / precio, 0) # Usa el 90% del cap a 5x
                        
                        c.futures_change_leverage(symbol=m, leverage=5)
                        c.futures_create_order(symbol=m, side='BUY', type='MARKET', quantity=qty)
                        
                        ops.append({'s':m,'l':'LONG','p':precio,'x':5,'q':qty,'be':False})
                        print(f"🎯 COMPRA REAL: {m} (5x)")
                        break
                        
                    if v < o_v and v < e9 and e9 < e27:
                        # Entrar SHORT
                        precio = cl[-1]
                        qty = round((cap * 0.9 * 5) / precio, 0)
                        
                        c.futures_change_leverage(symbol=m, leverage=5)
                        c.futures_create_order(symbol=m, side='SELL', type='MARKET', quantity=qty)
                        
                        ops.append({'s':m,'l':'SHORT','p':precio,'x':5,'q':qty,'be':False})
                        print(f"🎯 VENTA CORTA REAL: {m} (5x)")
                        break

            print(f"💰 REAL: ${cap:.2f} | {time.strftime('%H:%M:%S')} | Activas: {len(ops)}", end='\r')

        except Exception as e:
            print(f"⚠️ Error en Binance: {e}")
            time.sleep(10)
        
        time.sleep(max(1, 10 - (time.time() - t_l)))

if __name__ == "__main__": bot()
