"""Fail-soft probes (OBSERVED behaviours of installed versions). Run from a directory that does not contain a 'river'/'mabwiser' folder."""
import warnings; warnings.filterwarnings("ignore")
from river import bandit
from mabwiser.mab import MAB, LearningPolicy
def probe(label, f):
    try: print(f"{label} -> {f()}")
    except Exception as e: print(f"{label} -> EXC {type(e).__name__}: {str(e)[:80]}")
p = bandit.UCB(delta=1.0, seed=1)
probe("river pull([])", lambda: p.pull([]))
probe("river update never-pulled arm", lambda: p.update("zzz", 1.0))
probe("river update None", lambda: p.update("a", None))
q = bandit.UCB(delta=1.0, seed=1); q.update("a", float("nan")); q.update("b", 1.0)
probe("river UCB pull AFTER a NaN reward was ingested", lambda: q.pull(["a", "b"]))
m = MAB(arms=["a", "b"], learning_policy=LearningPolicy.UCB1(alpha=1.0), seed=1)
probe("mabwiser predict before fit", lambda: m.predict())
probe("mabwiser fit NaN reward", lambda: m.fit(["a"], [float("nan")]))
probe("mabwiser fit unknown arm", lambda: m.fit(["zzz"], [1]))
