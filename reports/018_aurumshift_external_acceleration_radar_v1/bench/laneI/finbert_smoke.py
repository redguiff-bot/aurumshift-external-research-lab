"""laneI — smoke FinBERT (ProsusAI/finbert) CPU : téléchargement, latence par titre, déterminisme (2 passes)."""
import time, json, hashlib, torch, transformers
from transformers import AutoTokenizer, AutoModelForSequenceClassification
torch.manual_seed(0); torch.set_num_threads(4)
import os; t0=time.time(); M=os.environ.get("FINBERT_PATH","ProsusAI/finbert")
tok=AutoTokenizer.from_pretrained(M); mod=AutoModelForSequenceClassification.from_pretrained(M).eval()
load=time.time()-t0
H=["Fed holds rates steady, signals no cuts this year",
   "Bitcoin ETF sees record outflows as investors flee risk assets",
   "US payrolls beat expectations, unemployment falls to 3.9%",
   "ECB cuts deposit rate by 25 basis points",
   "Dogecoin rallies 12% after exchange listing announcement",
   "Inflation came in hotter than expected in September",
   "Crypto exchange hacked, $200 million drained",
   "Treasury yields unchanged ahead of FOMC minutes"]*4
def run():
    out=[]; t=time.time()
    with torch.no_grad():
        for h in H:
            p=torch.softmax(mod(**tok(h,return_tensors="pt")).logits,-1)[0].tolist(); out.append(p)
    return out,(time.time()-t)/len(H)*1000
a,lat1=run(); b,lat2=run()
lab=mod.config.id2label
res=dict(transformers=transformers.__version__,torch=torch.__version__,load_s=round(load,1),ms_per_headline=[round(lat1,1),round(lat2,1)],
 deterministic_bitwise=a==b, hash=hashlib.sha256(json.dumps(a).encode()).hexdigest()[:16],
 preds=[(h,lab[max(range(3),key=lambda i:p[i])],round(max(p),3)) for h,p in zip(H[:8],a[:8])])
open("results/finbert_smoke.json","w").write(json.dumps(res,indent=1)); print(json.dumps(res,indent=1))
