# 03 — Drift scenarios

All generators live in `bench/online_learning_v1/py/scenarios.py` (T=4000, D=8, burn-in 500, `numpy.random.default_rng([seed, f(name)])`). `wA ⟂ wB` (unit vectors), so a stale model is maximally wrong.
Regret is measured against the *true* generating probability / mean, so no scenario needs a "hindsight" label.

| # | scenario | what changes | change points | feedback | question it answers |
|---|---|---|---|---|---|
| 1 | `stationary` | nothing | – | immediate | do adaptive methods pay a variance tax when nothing moves? (control) |
| 2 | `abrupt` | w: A→B | t=2000 | immediate | detection + relearning speed |
| 3 | `gradual` | w: slerp A→B over 1500–2500 | t=1500 | immediate | tracking a moving target (detectors fire late/oddly) |
| 4 | `recurring` | A(0–1000) B(1000–2000) A(2000–3000) B(3000–4000) | 1000,2000,3000 | immediate | does the method get *cheaper* the second time a regime appears (memory)? |
| 5 | `shock` | B for 100 steps then back to A | 2000, 2100 | immediate | over-reaction: how much damage does a 100-step blip do? |
| 6 | `false_drift` | features ×3 and noise ×3 on 2000–2400; **concept unchanged** | (2000) | immediate | error-based detectors and SGD stability under variance shock |
| 7 | `random_walk` | w diffuses (σ=0.01/step/coord) | – | immediate | Kalman-natural case; no discrete change |
| 8 | `abrupt_missing` | as 2, but 70 % of labels after t=2000 never arrive | 2000 | missing | drift with scarce feedback |
| 9 | `abrupt_delayed` | as 2, labels arrive 100 steps late (whole run) | 2000 | delayed | detection lag vs delay |
| 10 | `abrupt_nonlinear` | interaction concept `1.5·x0·x1 + 0.5·x2` → `−1.5·x0·x1 + 0.5·x3` | 2000 | immediate | fairness to trees (linear models cannot represent the concept) |

Design notes (INFERENCE, not measured on markets):
* Orthogonal concepts make the frozen model's post-change regret ≈ `|wA|²+|wB|²` — a deliberately harsh upper bound on the cost of ignoring drift. Real market drift is usually partial; the *gain* from adaptation reported here is therefore an **upper-end** estimate.
* Missing feedback is *permanent* random loss; it is not the same as a delayed batch of labels.
* Track R is not defined as "direction of returns"; it is a generic linear-Gaussian regression so that RLS/Kalman are tested on their home ground.
