import os, time
from binance.client import Client

def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap_ini = 31.09 # Capital tras el acierto en BTC
cap_actual = cap_ini

# st ahora guarda un historial 'h' para el reporte
st = {m: {'n': 0.0, 'o': 0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False, 'h': []} for m in ms}

def ni(k1, k2):
    o, h, l, c_ = float(k1[1]), float(k1[2]), float(k1[3]), float(k1[4])
    cp = abs(c_ - o) if abs(c_ - o) > 0 else 0.001
    mi, ms_ = min(o, c_) - l, h - max(o, c_)
    cl_p, op_p = float(k2[4]), float(k2[1])
    cp_p = abs(cl_p - op_p)
    # GATILLO 2.5x
    if mi > (cp * 2.5) and ms_ < (cp * 0.8): return "🔨"
    if c_ > o and cl_p < op_p and cp > (cp_p * 1.1): return "V"
    if ms_ > (cp * 2.5) and mi < (cp * 0.8): return "☄️"
    if c_ < o and cl_p > op_p and cp > (cp_p * 1.1): return "R"
    return "."

print(f"🔱 AMETRALLADORA ON | CAP: ${cap_actual:.2f} | REPORTE CADA 5")

while True:
    try:
        for m in ms:
            s = st[m]
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            k = cl.get_klines(symbol=m, interval='1m', limit=3)
            ptr = ni(k[-1], k[-2])
            cr = float(k[-1][4])

            if not s['e']:
                print(f"{m[:2]}:{ptr}", end=' ')
                if (("🔨" in ptr or "V" in ptr) and px > cr) or (("☄️" in ptr or "R" in ptr) and px < cr):
                    s['t'] = "LONG" if "V" in ptr or "🔨" in ptr else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 IN {m} (${cap_actual:.2f})")
            else:
                df = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                if roi >= 0.12: s['b'] = True 
                
                if (s['b'] and roi <= 0.0) or (s['m'] >= 0.35 and roi <= (s['m'] - 0.10)) or roi <= -0.50:
                    ganancia_op = (cap_actual * (roi / 100))
                    cap_actual += ganancia_op 
                    s['o'] += 1
                    s['e'] = False
                    
                    # Guardamos en el historial con emoji
                    icono = "✅" if roi > 0 else "❌"
                    s['h'].append(f"{icono} {s['t']} {roi:.2f}%")
                    
                    print(f"\n{icono} CIERRE {m}: {roi:.2f}%")
                    
                    # REPORTE DE 5 OPERACIONES (Como el de antes)
                    if s['o'] % 5 == 0:
                        print(f"\n╔{'═'*30}╗")
                        print(f"║ 📊 RESUMEN 5 OPS - {m[:3]} ║")
                        for line in s['h']:
                            print(f"║ {line.ljust(26)} ║")
                        print(f"╠{'═'*30}╣")
                        print(f"║ NETO SESIÓN: ${cap_actual - cap_ini:.4f} ║")
                        print(f"║ CAP TOTAL: ${cap_actual:.2f}   ║")
                        print(f"╚{'═'*30}╝\n")
                        s['h'] = [] # Limpiamos para las próximas 5

        time.sleep(15) 
    except Exception as e:
        time.sleep(10); cl = c()
