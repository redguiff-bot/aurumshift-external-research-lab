| target | id | expression | kind | nodes | seed freq | IC val | IC held-out | IC 90% CI | markets IC>0 | unseen IC>0 | p_Holm | STABLE | partial IC vs raw-ridge | p_Holm partial | NON-REDUNDANT | evidence class |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| y_ret | C01 | `mul(ret_24h, wknd)` | interaction | 3 | 0.6 | +0.0301 | +0.0120 | [-0.0038, +0.0277] | 1.00 | 5/5 | 0.107 | no | +0.0079 | 0.431 | no | NONE |
| y_vol | C01 | `mul(ret_72h, sgn(mag_168))` | interaction | 4 | 1.0 | +0.1227 | +0.1043 | [+0.0729, +0.1364] | 1.00 | 5/5 | 0.001 | yes | -0.0349 | 0.959 | no | PREDICTIVE |
