"""Tiny expression language shared by interactions and GP output. Strings like
add(mul(lvol_1, ret_4h), 0.5). Protected division as in gplearn. Evaluated on dict-of-columns."""
import re, numpy as np

_TOK = re.compile(r"\s*([A-Za-z_][A-Za-z_0-9]*|-?\d+\.?\d*(?:e-?\d+)?|\(|\)|,)")


def parse(s):
    toks = _TOK.findall(s)
    pos = 0

    def node():
        nonlocal pos
        t = toks[pos]; pos += 1
        if pos < len(toks) and toks[pos] == "(":
            pos += 1; args = []
            while True:
                args.append(node())
                if toks[pos] == ",":
                    pos += 1; continue
                assert toks[pos] == ")"; pos += 1; break
            return (t, args)
        try:
            return float(t)
        except ValueError:
            return t
    return node()


def _div(a, b):
    with np.errstate(all="ignore"):
        return np.where(np.abs(b) > 0.001, a / np.where(np.abs(b) > 0.001, b, 1.0), 1.0)

FUN = {"add": np.add, "sub": np.subtract, "mul": np.multiply, "div": _div, "neg": np.negative,
       "abs": np.abs, "max": np.maximum, "min": np.minimum, "tanh": np.tanh,
       "sgn": np.sign, "relu": lambda a: np.maximum(a, 0.0)}


def ev(t, cols):
    if isinstance(t, float):
        return np.full(len(next(iter(cols.values()))), t)
    if isinstance(t, str):
        return cols[t]
    f, args = t
    return FUN[f](*[ev(a, cols) for a in args])


def evaluate(s, cols):
    return np.clip(np.nan_to_num(ev(parse(s), cols), nan=0.0, posinf=1e6, neginf=-1e6), -1e6, 1e6)


def size(t):
    if not isinstance(t, tuple):
        return 1
    return 1 + sum(size(a) for a in t[1])


def consts(t):
    if isinstance(t, float):
        return 1
    if isinstance(t, tuple):
        return sum(consts(a) for a in t[1])
    return 0


def variables(t, acc=None):
    acc = set() if acc is None else acc
    if isinstance(t, str):
        acc.add(t)
    elif isinstance(t, tuple):
        for a in t[1]:
            variables(a, acc)
    return acc


def to_infix(t):
    if isinstance(t, float):
        return f"{t:.4g}"
    if isinstance(t, str):
        return t
    f, a = t
    ops = {"add": "+", "sub": "-", "mul": "*"}
    if f in ops:
        return f"({to_infix(a[0])} {ops[f]} {to_infix(a[1])})"
    if f == "div":
        return f"({to_infix(a[0])} / {to_infix(a[1])})"
    return f"{f}(" + ", ".join(to_infix(x) for x in a) + ")"


def canonical(s):
    """Structural canonical form: sort commutative args, simplify x-x, x/x not attempted."""
    def c(t):
        if not isinstance(t, tuple):
            return t
        f, a = t; a = [c(x) for x in a]
        if f in ("add", "mul", "max", "min"):
            a = sorted(a, key=lambda x: repr(x))
        return (f, a)
    return repr(c(parse(s)))


def tostr(t):
    if isinstance(t, float):
        return repr(t)
    if isinstance(t, str):
        return t
    return f"{t[0]}(" + ", ".join(tostr(a) for a in t[1]) + ")"


def variants(t):
    """All trees obtained by replacing one subtree by one of its children or by the constant 0.0."""
    if not isinstance(t, tuple):
        return
    f, args = t
    for a in args:
        yield a
    yield 0.0
    for i, a in enumerate(args):
        for v in variants(a):
            yield (f, args[:i] + [v] + args[i + 1:])
