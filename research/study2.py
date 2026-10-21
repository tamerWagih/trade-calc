import study as S
from study import *
S.COST=0.0
print("== gross, no costs")
pos=pd.DataFrame({s:np.sign(b) for s in alts}); S.report("lead-lag alts follow BTC 1h (gross)",pos,R[alts])
S.report("fade |z|>3 hold 4h (gross)",(-np.sign(z)*(z.abs()>3)).replace(0,np.nan).ffill(limit=4).fillna(0))
S.COST=0.001
print("== slow trend, robustness across lookbacks, vol-scaled, rebalance weekly")
vol=R.rolling(24*30).std()
for lb in [30,45,60,90,120,180]:
    sig=np.sign(C.pct_change(lb*24))
    w=(sig/vol); w=w.div(w.abs().sum(axis=1),axis=0)
    w=w[(w.index.hour==0)&(w.index.dayofweek==0)].reindex(w.index).ffill()
    S.report(f"TS trend {lb}d L/S vol-scaled weekly",w*20)
print("== same, by calendar year (60d)")
sig=np.sign(C.pct_change(60*24)); w=(sig/vol); w=w.div(w.abs().sum(axis=1),axis=0)
w=w[(w.index.hour==0)&(w.index.dayofweek==0)].reindex(w.index).ffill()
p=w.shift(1).fillna(0); net=(p*R).sum(axis=1)-p.diff().abs().sum(axis=1)*0.0005
print((net.groupby(net.index.year).sum()*100).round(1).to_dict())
