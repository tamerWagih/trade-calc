import pandas as pd, numpy as np, os
P=pd.read_pickle('ml_preds.pkl')
base=(np.exp(P.fwd)-1)
print(f"random long 4h trade, same period: avg {base.mean()*1e4:+.1f}bp before fees -> {base.mean()*1e4-10:+.1f}bp after")
exec(open('ml1h.py').read().split("HZ=4")[0])   # rebuild features
Xf=pd.concat({k:v.stack() for k,v in F.items()},axis=1); Xf.index.names=['t','sym']
J=P.join(Xf,how='left')
strong_long=J[J.pred>J.thr*1.5]; strong_short=J[J.pred<-J.thr*1.5]
cols=['r1','r4','r24','r168','btc4','pos24','pos168','volratio','ema200','xsrank','hour']
print(pd.DataFrame({'all hours (median)':J[cols].median(),'strong LONG signals':strong_long[cols].median(),'strong SHORT signals':strong_short[cols].median()}).round(2).to_string())
print("\nhour-of-day share of strong long signals (top 6):",(strong_long.hour.value_counts(normalize=True)*100).round(1).head(6).to_dict())
