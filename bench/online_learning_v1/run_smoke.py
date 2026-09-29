import sys, time; sys.path.insert(0,'src')
import runner, registry as REG
t=time.time()
for n,v in REG.R.items():
    t0=time.time(); r=runner.one((n,v['default'],'abrupt',0,2.0))
    print(f"{n:24s} overall={r['overall']:.4f} rec={r['cps'][0]['rec']:4d} first100={r['cps'][0]['first100']:.3f} st={r['state'][3999]:8d} {time.time()-t0:5.1f}s resets={r['meta']['n_resets']}")
