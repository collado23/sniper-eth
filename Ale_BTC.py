import os, time, threading
from binance.client import Client
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- 🌐 1. SERVER DE SALUD (Para que Railway no lo baje) ---
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
def s_h():
    try: HTTPServer(("0.0.0.0", int(os.getenv("PORT", 8080))), H).serve_forever()
    except: pass

def bot():
    threading.Thread(target=s_h, daemon=True).start()
    
    # --- CONFIGURACIÓN DEL SIMULADOR ---
    c = Client() # No necesita llaves para leer precios
    cap_simulado = 15.77  # Tu capital inicial de prueba
    ops = []
    monedas = ['SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT', 'LINKUSDT', 'PEPEUSDT']

    print(f"🧪 INICIANDO SIMULADOR V173")
    print(f"💰 Capital Inicial: ${cap_simulado} | Modo: Bidireccional 6x->15x")
    print(f"🚫 NOTA: Este bot NO realiza operaciones reales.")

    while True:
        try:
            # --- 1. SEGUIMIENTO DE OPERACIONES SIMULADAS ---
            for o in ops[:]:
                p_a = float(c.get_symbol_ticker(symbol=o['s'])['price'])
                
                # Cálculo de ganancia según si es LONG o SHORT
                if o['l'] == "LONG":
                    diff = (p_a - o['p']) / o['p']
                else:
                    diff = (o['p'] - p_a) / o['p']
                
                # ROI Neto (restando comisiones simuladas de 0.1% * palanca)
                roi_neto = (diff * 100 * o['x']) - (0.1 * o['x'])
                
                # Simulación de Salto a 15x
                if roi_neto > 0.25 and o['x'] == 6:
                    o['x'] = 15
                    print(f"🔥 [SIM] SALTO A 15X: {o['s']} ({o['l']})")

                # Cierre Simulado (Take Profit 2.5% o Stop Loss -1.3%)
                if roi_neto >= 2.5 or roi_neto <= -1.3:
                    ganancia_usd = cap_simulado * (roi_neto / 100)
                    cap_simulado += ganancia_usd
                    ops.remove(o)
                    estado = "PROFIT ✅" if roi_neto > 0 else "STOP ❌"
                    print(f"{estado} Cerrado {o['s']} | Neto: {roi_neto:.2f}% | Nuevo Cap: ${cap_simulado:.2f}")

            # --- 2. BUSCAR ENTRADAS (Simuladas) ---
            if len(ops) < 1:
                for m in monedas:
                    k = c.get_klines(symbol=m, interval='1m', limit=30)
                    cl = [float(x[4]) for x in k]
                    op = [float(x[1]) for x in k]
                    e9, e27 = sum(cl[-9:])/9, sum(cl[-27:])/27
                    
                    v, o_v = cl[-2], op[-2]
                    tipo = None
                    
                    # Lógica Bidireccional
                    if v > o_v and v > e9 and e9 > e27: tipo = "LONG"
                    elif v < o_v and v < e9 and e9 < e27: tipo = "SHORT"

                    if tipo:
                        precio_entrada = float(c.get_symbol_ticker(symbol=m)['price'])
                        ops.append({'s': m, 'l': tipo, 'p': precio_entrada, 'x': 6})
                        print(f"🎯 [SIM] ENTRADA {tipo} 6X: {m} a {precio_entrada}")
                        break

            print(f"📊 [SIM] Billetera: ${cap_simulado:.2f} | Ops Activas: {len(ops)}", end='\r')

        except Exception as e:
            print(f"⚠️ Error Simulador: {e}")
            time.sleep(10)
        
        time.sleep(10)

if __name__ == "__main__":
    bot() 
