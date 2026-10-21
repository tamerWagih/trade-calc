# Walk-forward ML forecast of the next 4h return, 1h bars, 20 coins, long AND short.
from load import *
import warnings; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
H={s:load(s).resample('1h').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna() for s in SYMS}
C=pd.DataFrame({s:H[s].c for s in SYMS}); O=pd.DataFrame({s:H[s].o for s in SYMS})
Hh=pd.DataFrame({s:H[s].h for s in SYMS}); Ll=pd.DataFrame({s:H[s].l for s in SYMS})
lc=np.log(C); r1=lc.diff(); vol=r1.rolling(24*7).std()
F={}
for k in [1,2,4,12,24,72,168]: F[f'r{k}']=(lc-lc.shift(k)).div(vol*np.sqrt(k))
for k in [1,4,24]: F[f'btc{k}']=pd.DataFrame({s:(lc['BTCUSDT']-lc['BTCUSDT'].shift(k))/(vol['BTCUSDT']*np.sqrt(k)) for s in SYMS})
F['rel24']=(lc-lc.shift(24)).sub(lc['BTCUSDT']-lc['BTCUSDT'].shift(24),axis=0).div(vol*np.sqrt(24))
for k in [24,168]: F[f'pos{k}']=(C-Ll.rolling(k).min())/(Hh.rolling(k).max()-Ll.rolling(k).min())
F['volratio']=r1.rolling(24).std()/vol
F['body']=(C-O)/(Hh-Ll).replace(0,np.nan); F['uwick']=(Hh-np.maximum(C,O))/(Hh-Ll).replace(0,np.nan)
F['ema50']=(lc-np.log(C.ewm(span=50).mean()))/vol; F['ema200']=(lc-np.log(C.ewm(span=200).mean()))/vol
F['xsrank']=(lc-lc.shift(24)).rank(axis=1,pct=True)
F['hour']=pd.DataFrame({s:C.index.hour for s in SYMS},index=C.index); F['dow']=pd.DataFrame({s:C.index.dayofweek for s in SYMS},index=C.index)
HZ=4
fwd=(lc.shift(-HZ)-lc)               # next 4h log return (entry at this close)
y=fwd.div(vol)
X=pd.concat({k:v.stack() for k,v in F.items()},axis=1); X['y']=y.stack(); X['fwd']=fwd.stack()
X=X.dropna(); X.index.names=['t','sym']
t=X.index.get_level_values('t')
feats=[c for c in X.columns if c not in('y','fwd')]
preds=[]
qs=pd.date_range('2023-01-01','2026-10-01',freq='QS')
for q0,q1 in zip(qs,list(qs[1:])+[pd.Timestamp('2026-12-31')]):
    tr=X[t<q0-pd.Timedelta(hours=HZ)]; te=X[(t>=q0)&(t<q1)]
    if len(te)==0: continue
    tr=tr.iloc[::3]   # thin for speed
    m=HistGradientBoostingRegressor(max_iter=200,learning_rate=0.05,max_leaf_nodes=31,min_samples_leaf=500,l2_regularization=1.0)
    m.fit(tr[feats],tr.y.clip(-5,5))
    ptr=m.predict(tr[feats]); thr=np.quantile(np.abs(ptr),0.9)   # top 10% strongest training forecasts
    p=pd.Series(m.predict(te[feats]),index=te.index)
    preds.append(pd.DataFrame({'pred':p,'thr':thr,'fwd':te.fwd}))
    print(q0.date(),"trained on",len(tr),"rows", flush=True)
P=pd.concat(preds); P.to_pickle('ml_preds.pkl')
