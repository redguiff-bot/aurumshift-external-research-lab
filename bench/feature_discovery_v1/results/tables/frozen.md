| target | id | expression | kind | nodes | constants | seed freq | IC train | IC val (mean 4 mkts) | val boot p | val partial IC vs mains-ridge | sign fixed on train | family |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| y_ret | C01 | `mul(ret_24h, wknd)` | interaction | 3 | 0 | 0.6 | -0.0422 | +0.0301 | 0.003 | +0.0158 | -1.0 | 3 members |
| y_vol | C01 | `mul(ret_72h, sgn(mag_168))` | interaction | 4 | 0 | 1.0 | -0.0777 | +0.1227 | 0.003 | -0.0665 | -1.0 | 5 members |
