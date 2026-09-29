
### Policy B: 45 configurations, errors 0

Chosen: `B|g0.9995|S25|M4` — spec `{"kind": "B", "gamma": 0.9995, "S": 25, "M": 4}`; TRAIN J = 0.692, VALIDATION J = 0.632 (generalisation gap +0.059). References on the same objective — A: train 0.526 / val 0.453; round-robin: train 0.527 / val 0.458.

| top-3 by TRAIN J | TRAIN J | VALIDATION J |
|---|---|---|
| `B|g0.9995|S25|M4` | 0.692 | 0.632 |
| `B|g0.9995|S25|M16` | 0.692 | 0.632 |
| `B|g0.998|S25|M4` | 0.680 | 0.608 |

TRAIN J across the whole grid: min 0.418, median 0.588, max 0.692; configs with TRAIN J ≥ round-robin (0.527): 35/45.

### Policy C: 21 configurations, errors 0

Chosen: `C|eps_ew|f0.1|e0.2` — spec `{"kind": "C", "algo": "eps_ew", "fading": 0.1, "eps": 0.2}`; TRAIN J = 0.561, VALIDATION J = 0.514 (generalisation gap +0.047). References on the same objective — A: train 0.526 / val 0.453; round-robin: train 0.527 / val 0.458.

| top-3 by TRAIN J | TRAIN J | VALIDATION J |
|---|---|---|
| `C|eps_ew|f0.3|e0.2` | 0.580 | 0.511 |
| `C|eps_ew|f0.1|e0.2` | 0.561 | 0.514 |
| `C|eps_ew|f0.05|e0.2` | 0.530 | 0.492 |

TRAIN J across the whole grid: min 0.018, median 0.355, max 0.580; configs with TRAIN J ≥ round-robin (0.527): 3/21.

### Policy C2: 27 configurations, errors 0

Chosen: `C2|eps_ew|f0.1|e0.2|S50|M4` — spec `{"kind": "C2", "algo": "eps_ew", "fading": 0.1, "eps": 0.2, "guard": [50, 4]}`; TRAIN J = 0.742, VALIDATION J = 0.750 (generalisation gap -0.008). References on the same objective — A: train 0.526 / val 0.453; round-robin: train 0.527 / val 0.458.

| top-3 by TRAIN J | TRAIN J | VALIDATION J |
|---|---|---|
| `C2|eps_ew|f0.1|e0.2|S50|M4` | 0.742 | 0.750 |
| `C2|eps_ew|f0.1|e0.2|S50|M16` | 0.742 | 0.750 |
| `C2|eps_ew|f0.1|e0.2|S25|M4` | 0.734 | 0.691 |

TRAIN J across the whole grid: min 0.583, median 0.711, max 0.742; configs with TRAIN J ≥ round-robin (0.527): 27/27.

### Policy D: 30 configurations, errors 0

Chosen: `D|eps|e0.2|lr0.05|grp0` — spec `{"kind": "D", "algo": "eps", "expl": 0.2, "lr": 0.05, "use_group": false}`; TRAIN J = 0.645, VALIDATION J = 0.573 (generalisation gap +0.072). References on the same objective — A: train 0.526 / val 0.453; round-robin: train 0.527 / val 0.458.

| top-3 by TRAIN J | TRAIN J | VALIDATION J |
|---|---|---|
| `D|eps|e0.2|lr0.05|grp0` | 0.645 | 0.573 |
| `D|eps|e0.2|lr0.05|grp1` | 0.636 | 0.567 |
| `D|eps|e0.2|lr0.2|grp0` | 0.632 | 0.573 |

TRAIN J across the whole grid: min 0.330, median 0.557, max 0.645; configs with TRAIN J ≥ round-robin (0.527): 22/30.