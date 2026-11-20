import csv, random, subprocess, sys, tempfile, os, re
from datetime import datetime
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P1 = os.path.join(ROOT, "p2-550260-522170", "parte-1")
P2 = os.path.join(ROOT, "p2-550260-522170", "parte-2")
random.seed(2026)

edges = list(csv.DictReader(open(os.path.join(ROOT, "data", "edges.csv"), encoding="utf-8")))
airports = sorted({r["origin"] for r in edges} | {r["destination"] for r in edges})
for r in csv.DictReader(open(os.path.join(ROOT, "data", "vertices.csv"), encoding="utf-8")):
    if r["acronym"] not in airports:
        airports.append(r["acronym"])
airports.sort()

def run(script, cwd, lines, tmp, name):
    inp = os.path.join(tmp, name + ".in"); out = os.path.join(tmp, name + ".out")
    open(inp, "w").write("\n".join(lines) + "\n")
    if os.path.exists(out): os.remove(out)
    p = subprocess.run([sys.executable, script, inp, out], cwd=cwd, capture_output=True, text=True, timeout=300)
    fo = open(out).read() if os.path.exists(out) else None
    return p.stdout, fo, p.returncode, p.stderr

fails = []
# ---------------- Parte 1 ----------------
arc = {}
for r in edges:
    a, b = r["origin"], r["destination"]
    c = round(float(r["haversine_km"]) * 1000)
    # multiples filas: el arco existe; guardo el minimo (mas permisivo para detectar sobrecoste)
    # y el conjunto de costes posibles
    arc.setdefault((a, b), set()).add(c)
arcmin = {k: min(v) for k, v in arc.items()}
arclist = [(a, b, c) for (a, b), c in arcmin.items()]
multi = sum(1 for v in arc.values() if len(v) > 1)

def bf(src):
    INF = float("inf"); d = {src: 0}
    changed = True
    while changed:
        changed = False
        for a, b, c in arclist:
            if a in d and d[a] + c < d.get(b, INF):
                d[b] = d[a] + c; changed = True
    return d

n1 = ok1 = 0
with tempfile.TemporaryDirectory() as tmp:
    sc = os.path.join(P1, "sol-1.py")
    origins = random.sample(airports, 15)
    for o in origins:
        d = bf(o)
        reach = [x for x in airports if x in d and x != o]
        unr = [x for x in airports if x not in d]
        dests = random.sample(reach, min(15, len(reach))) + random.sample(unr, min(4, len(unr))) + [o]
        for t in dests:
            n1 += 1
            so, fo, rc, er = run(sc, P1, [o, t], tmp, "p1")
            prob = []
            if so != fo: prob.append("stdout!=fichero")
            lines = (so or "").strip("\n").split("\n")
            if t not in d:
                if lines != ["No existe solucion"]: prob.append("debia ser No existe solucion")
            elif len(lines) != 2:
                prob.append("formato: %r" % so)
            else:
                path = [x.strip() for x in lines[1].split(" - ")]
                if path[0] != o or path[-1] != t: prob.append("extremos")
                tot = 0; okp = True
                for a, b in zip(path, path[1:]):
                    if (a, b) not in arc: okp = False; prob.append("arco inexistente %s-%s" % (a, b)); break
                    tot += arcmin[(a, b)]
                if okp:
                    if "%.2f" % (tot / 1000) != lines[0]: prob.append("suma %.2f != linea1 %s" % (tot / 1000, lines[0]))
                    if tot != d[t]: prob.append("no optimo: %d vs ref %d (m)" % (tot, d[t]))
            if prob: fails.append(("P1", [o, t], so, prob))
            else: ok1 += 1
print("Parte 1: %d/%d OK (pares con costes distintos entre filas multiples: %d)" % (ok1, n1, multi))

# ---------------- Parte 2 ----------------
def ts(s): return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
flights = []
for r in edges:
    if r["origin"] == r["destination"]: continue
    d, a = ts(r["departure_time_utc"]), ts(r["arrival_time_utc"])
    dep = d.hour * 3600 + d.minute * 60 + d.second
    dur = int((a - d).total_seconds())
    flights.append((r["origin"], r["destination"], dep, dur, r["callsign"]))
cand = defaultdict(list)
for f in flights:
    cand[(f[0], f[1], f[4], f[2] // 60, ((f[2] + f[3]) % 86400) // 60)].append(f)

def nextdep(avail, dep):
    day = max(0, -(-(avail - dep) // 86400))
    return day * 86400 + dep

def ref(o, t, start, hold):
    INF = float("inf"); lab = {o: start}  # lab = disponibilidad para despegar
    changed = True
    while changed:
        changed = False
        for a, b, dep, dur, cs in flights:
            if a not in lab: continue
            arr = nextdep(lab[a], dep) + dur
            av = arr + hold
            if b == o: av = min(av, start)  # origen siempre disponible en start
            if b != o and av < lab.get(b, INF):
                lab[b] = av; changed = True
    # llegada real al destino = disp - hold
    return None if (t not in lab or t == o) else lab[t] - hold

n2 = ok2 = 0; reach2 = 0
holds = [0, 15, 30, 45, 60, 90, 120, 180, 300, 720, 1500]
with tempfile.TemporaryDirectory() as tmp:
    sc = os.path.join(P2, "sol-2.py")
    for i in range(150):
        o, t = random.sample(airports, 2)
        if i % 30 == 0: t = o
        h, m = random.randrange(24), random.randrange(60); hold = random.choice(holds)
        start = h * 3600 + m * 60
        inp = [o, t, "%02d:%02d" % (h, m), str(hold)]
        n2 += 1
        so, fo, rc, er = run(sc, P2, inp, tmp, "p2")
        prob = []
        if so != fo: prob.append("stdout!=fichero")
        if t == o:
            if (so or "").strip(): prob.append("origen==destino debia ser vacio")
        else:
            exp = ref(o, t, start, hold * 60)
            ls = [l for l in (so or "").split("\n") if l.strip()]
            if exp is None:
                if ls != ["No existe solucion"]: prob.append("debia ser No existe solucion")
            elif ls == ["No existe solucion"] or not ls:
                reach2 += 1
                prob.append("dijo no existe pero hay ruta (ref llegada=%d s)" % exp)
            else:
                reach2 += 1
                cur, avail, first, arr = o, start, True, None
                for l in ls:
                    mm = re.fullmatch(r"(\w+) - (\w+) (\S+) (\d\d):(\d\d) - (\d\d):(\d\d)", l.strip())
                    if not mm: prob.append("formato linea %r" % l); break
                    a, b, cs, h1, m1, h2, m2 = mm.groups()
                    if a != cur: prob.append("encadenamiento %s != %s" % (a, cur)); break
                    cs_ = cand.get((a, b, cs, int(h1) * 60 + int(m1), int(h2) * 60 + int(m2)))
                    if not cs_: prob.append("vuelo inexistente: %s" % l); break
                    best = min(nextdep(avail, f[2]) + f[3] for f in cs_)
                    arr = best; cur = b; avail = arr + hold * 60
                else:
                    if cur != t: prob.append("no acaba en destino")
                    elif arr != exp: prob.append("llegada sim=%d ref=%d (s)" % (arr, exp))
        if prob: fails.append(("P2", inp, so, prob))
        else: ok2 += 1
print("Parte 2: %d/%d OK (con ruta: %d)" % (ok2, n2, reach2))
for f in fails: print("FALLO", f[0], f[1], repr((f[2] or "")[:300]), f[3])
