import time, sys, scenarios as S, harness as H
from models import GRID
sc = sys.argv[1] if len(sys.argv) > 1 else "abrupt"
for (name, kind), grid in GRID.items():
    st = S.make(sc, 1); t0 = time.time(); r = H.run(st, kind, name, grid[0]); d = H.summarise(st, kind, r)
    print(f"{kind} {name:14s} regret={d['regret']:.4f} post={[round(x,3) for x in d['post_regret']]} adapt={d['adapt_steps']} {time.time()-t0:5.1f}s size={d['size4000']}")
