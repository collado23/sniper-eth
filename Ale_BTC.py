import os, time
from binance.client import Client

# CONEXIÓN MÍNIMA
def c():
    return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))

cl = c()
# TRIDENTE LINK, ADA, XRP
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
# CAPITAL CON EL PROFIT DE BTC SUMADO
cap = 31.09 
st = {m: {'n': 0.0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False} for m in ms}

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

print(f"🔱 TRIDENTE ON | CAP: ${cap}")

while True:
    try:
        for m in ms:
            s = st[m]
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            k = cl.get_klines(symbol=m, interval='1m', limit=3)
            p = ni(k[-1], k[-2])
            cr = float(k[-1][4])

            if not s['e']:
                print(f"{m[:2]}:{p}", end=' ')
                if (("🔨" in p or "V" in p) and px > cr) or (("☄️" in p or "R" in p) and px < cr):
                    s['t'] = "LONG" if "V" in p or "🔨" in p else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\n🎯 IN {m} ${cap:.2f}")
            else:
                df = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                if roi >= 0.12: s['b'] = True 
                
                if (s['b'] and roi <= 0.0) or (s['m'] >= 0.35 and roi <= (s['m'] - 0.10)) or roi <= -0.45:
                    g = (cap * (roi / 100))
                    cap += g
                    s['e'] = False
                    print(f"\n✅ {m} {roi:.2f}% | CAP: ${cap:.2f}")

        time.sleep(15) # REGLA DE 15 SEGUNDOS
    except:
        time.sleep(10); cl = c()
