"""Genetic-programming feature construction (gplearn) with complexity/parameter penalty in selection."""
import warnings
import numpy as np
from gplearn.genetic import SymbolicRegressor
from gplearn.functions import make_function
from . import expr as E

_tanh = make_function(function=np.tanh, name="tanh", arity=1)


def gp_programs(X, y, names, seed, pop=300, gens=10, parsimony=0.004, top=8, max_len=15):
    est = SymbolicRegressor(population_size=pop, generations=gens, tournament_size=15,
                            function_set=("add", "sub", "mul", "div", "abs", "neg", "max", "min", _tanh),
                            metric="pearson", parsimony_coefficient=parsimony, init_depth=(2, 4),
                            const_range=(-1.0, 1.0), max_samples=0.7, feature_names=list(names),
                            p_crossover=0.65, p_subtree_mutation=0.1, p_hoist_mutation=0.05,
                            p_point_mutation=0.1, random_state=int(seed), n_jobs=1, verbose=0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        est.fit(X, y)
    progs = [p for p in est._programs[-1] if p is not None and p.length_ <= max_len]
    progs.sort(key=lambda p: -p.raw_fitness_)
    out, seen = [], set()
    for p in progs:
        s = str(p)
        try:
            c = E.canonical(s)
        except Exception:
            continue
        if c in seen or not E.variables(E.parse(s)):
            continue
        seen.add(c); out.append(s)
        if len(out) >= top:
            break
    return out
