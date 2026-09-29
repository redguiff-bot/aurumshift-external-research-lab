import requests, time, json
UA={"User-Agent":"aurumshift-external-research-lab/altdata-probe (research; contact via repo)"}
def get(url, params=None, timeout=40, headers=None, **kw):
    h=dict(UA); h.update(headers or {})
    t=time.time()
    try:
        r=requests.get(url,params=params,headers=h,timeout=timeout,**kw)
        return r, round((time.time()-t)*1000)
    except Exception as e:
        class R: status_code=0; content=b""; text=repr(e)[:200]; headers={}
        return R(), round((time.time()-t)*1000)
