import pickle, sys, glob
sys.path.insert(0, 'src')
import numpy as np
import river
print("river", river.__version__)
for f in sorted(glob.glob('/tmp/ck_*.pkl')):
    try:
        m = pickle.load(open(f, 'rb'))
        x = np.ones(5)
        print(f.split('ck_')[1][:-4], "LOAD_OK", round(float(m.predict(x)), 4))
    except Exception as e:
        print(f.split('ck_')[1][:-4], "LOAD_FAIL", type(e).__name__, str(e)[:80])
