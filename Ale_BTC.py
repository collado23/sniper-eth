import os, time, redis, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from binance.client import Client

# --- SERVIDOR DE SALUD ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

# --- MOTOR V146.1 "LECTOR REAL" ---
def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # Buscamos tus variables APY
    ak = os.getenv("BINANCE_APY_KEY")
    as_ = os.getenv("BINANCE_APY_SECRET")
    
    print(f"🚀 INICIANDO COCODRILO V146.1")
    
    try:
        c = Client(ak, as_)
        # Verificamos conexión inmediata
        c.get_account_status()
        print("✅ CONEXIÓN EXITOSA CON BINANCE")
    except Exception as e:
        print(f"❌ ERROR CRÍTICO DE CONEXIÓN: {e}")
        return

    ops = []

    while True:
        try:
            # 🔍 ESTO ES LO QUE IMPORTA: Leer saldo real de la billetera de FUTUROS
            bal = c.futures_account_balance()
            cap = 0.0
            for b in bal:
                if b['asset'] == 'USDT':
                    cap = float(b['balance'])
                    break
            
            if cap == 0:
                print("⚠️ ATENCIÓN: Saldo 0.0 o no se pudo leer la billetera de Futuros.")
            
            # --- LÓGICA DE MONITOREO ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                diff = (p_a - o['p'])/o['p'] if o['l']=="LONG" else (o['p'] - p_a)/o['p']
                roi = diff * 100 * o['x']
                
                if roi > 0.2 and o['x'] == 5:
                    o['x'] = 15; o['be'] = True
                    c.futures_change_leverage(symbol=o['s'], leverage=15)

                if (o['be'] and roi <= 0.05) or roi >= 1.5 or roi <= -0.9:
                    side = "SELL" if o['l'] == "LONG" else "BUY"
                    c.futures_create_order(symbol=o['s'], side=side, type='MARKET', quantity=o['q'])
                    ops.remove(o)
                    print(f"✅ CIERRE REAL REALIZADO")

            # --- BUSCADOR DE ENTRADAS ---
            if len(ops) < 2 and cap > 5: # Solo opera si tenés más de $5 reales
                for m in ['PEPEUSDT', 'DOGEUSDT', 'SOLUSDT']:
                    if any(x['s'] == m for x in ops): continue
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    if cl[-2] > e9 and e9 > e27: # Señal Long Simple
                        qty = round((cap * 0.9 * 5) / cl[-1], 0)
                        c.futures_change_leverage(symbol=m, leverage=5)
                        c.futures_create_order(symbol=m, side='BUY', type='MARKET', quantity=qty)
                        ops.append({'s':m,'l':'LONG','p':cl[-1],'x':5,'q':qty,'be':False})
                        break

            print(f"💰 SALDO EN BINANCE: ${cap:.2f} | Activas: {len(ops)}", end='\r')

        except Exception as e:
            print(f"⚠️ Error en ciclo: {e}")
            time.sleep(10)
        
        time.sleep(10)

if __name__ == "__main__":
    bot()
