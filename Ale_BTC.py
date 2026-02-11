import os, time
from binance.client import Client

def c():
    try:
        return Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
    except:
        return None

cl = c()
ms = ['LINKUSDT', 'ADAUSDT', 'XRPUSDT']
cap = 31.09 
st = {m: {'n': 0.0, 'e': False, 'p': 0, 't': '', 'm': -9.0, 'b': False} for m in ms}

def ni(k):
    o, h, l, c_ = float(k[1]), float(k[2]), float(k[3]), float(k[4])
    cp = abs(c_ - o) if abs(c_ - o) > 0 else 0.001
    mi, ms_ = min(o, c_) - l, h - max(o, c_)
    if mi > (cp * 2.5): return "🔨"
    if ms_ > (cp * 2.5): return "☄️"
    if c_ > o: return "V"
    if c_ < o: return "R"
    return "."

print(f"ON ${cap}")

while True:
    try:
        if cl is None: cl = c()
        for m in ms:
            s = st[m]
            px = float(cl.get_symbol_ticker(symbol=m)['price'])
            k = cl.get_klines(symbol=m, interval='1m', limit=2)
            p = ni(k[-1])

            if not s['e']:
                print(f"{m[0]}:{p}", end=' ')
                if (p == "🔨" or p == "V") or (p == "☄️" or p == "R"):
                    s['t'] = "LONG" if p in ["🔨", "V"] else "SHORT"
                    s['p'], s['e'], s['m'], s['b'] = px, True, -9.0, False
                    print(f"\nIN {m}")
            else:
                df = (px - s['p']) / s['p'] if s['t'] == "LONG" else (s['p'] - px) / s['p']
                roi = (df * 100 * 10) - 0.22 
                if roi > s['m']: s['m'] = roi
                if roi >= 0.12: s['b'] = True 
                if (s['b'] and roi <= 0.0) or (s['m'] >= 0.35 and roi <= (s['m'] - 0.10)) or roi <= -0.45:
                    cap += (cap * (roi / 100))
                    s['e'] = False
                    print(f"\nOUT {m} {roi:.2f}% | ${cap:.2f}")
        time.sleep(15)
    except:
        time.sleep(10); cl = c()
