from load import *
import warnings; warnings.filterwarnings('ignore')
H={s:load(s).resample('1h').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna() for s in SYMS}
C=pd.DataFrame({s:H[s].c for s in SYMS}); Hh=pd.DataFrame({s:H[s].h for s in SYMS}); Ll=pd.DataFrame({s:H[s].l for s in SYMS})
R=np.log(C).diff()
COST=0.001  # round trip, taker both sides
SPLIT='2024-01-01'
def report(name,pos,hold_ret=R):
    # pos: positions decided at close of bar t, earn return of bar t+1
    p=pos.shift(1).fillna(0); gross=(p*hold_ret)
    turn=p.diff().abs().fillna(0)*COST/2
    net=(gross-turn).sum(axis=1)/max(1,1)
    nb=p.abs().sum(axis=1).replace(0,np.nan)
    net=((gross-turn).sum(axis=1)/nb).fillna(0)  # per unit gross exposure
    out=[]
    for lab,m in [('IS 21-23',net.index<SPLIT),('OOS 24-26',net.index>=SPLIT)]:
        x=net[m]; yrs=len(x)/8760
        sh=x.mean()/x.std()*np.sqrt(8760) if x.std()>0 else 0
        out.append(f"{lab}: ann {x.sum()/yrs*100:6.1f}%  sharpe {sh:5.2f}")
    print(f"{name:42s}", ' | '.join(out), f" turnover/yr {p.diff().abs().sum(axis=1).sum()/ (len(p)/8760)/nb.mean():.0f}x")

ew=R.mean(axis=1)
print("== baseline")
report("buy&hold equal-weight", pd.DataFrame(1,index=R.index,columns=R.columns))

print("== 1. cross-sectional momentum/reversal (rank vs other coins), rebalanced daily")
for lb in [24,72,168,336,720]:
    sc=C.pct_change(lb); rk=sc.rank(axis=1,pct=True)
    pos=((rk>0.75).astype(float)-(rk<=0.25).astype(float))
    pos=pos[pos.index.hour==0].reindex(pos.index).ffill()
    report(f"XS mom lookback {lb}h (long top5/short bot5)",pos)

print("== 2. time-series trend (each coin vs its own past), daily rebalance")
for lb in [168,720,1440]:
    pos=np.sign(C.pct_change(lb)); pos=pos[pos.index.hour==0].reindex(pos.index).ffill()
    report(f"TS mom {lb}h long/short",pos)
    report(f"TS mom {lb}h long-only",pos.clip(lower=0))

print("== 3. BTC lead-lag: alts follow BTC's last hour?")
b=R['BTCUSDT']; alts=[s for s in SYMS if s!='BTCUSDT']
resid=R[alts].sub(b,axis=0)
pos=pd.DataFrame({s:np.sign(b) for s in alts})
report("alts long if BTC up last 1h",pos,R[alts])

print("== 4. hour-of-day seasonality (learned in-sample, tested OOS)")
hr=ew.groupby(ew.index.hour)
is_=ew[ew.index<SPLIT]; oos=ew[ew.index>=SPLIT]
a=is_.groupby(is_.index.hour).mean()*1e4; bb=oos.groupby(oos.index.hour).mean()*1e4
print(pd.DataFrame({'IS bp':a.round(1),'OOS bp':bb.round(1)}).T.to_string())
print("corr IS vs OOS hourly means:",round(np.corrcoef(a,bb)[0,1],2))
dw_is=is_.groupby(is_.index.dayofweek).mean()*1e4*24; dw_o=oos.groupby(oos.index.dayofweek).mean()*1e4*24
print("day-of-week daily bp IS ",dw_is.round(0).tolist()); print("day-of-week daily bp OOS",dw_o.round(0).tolist())

print("== 5. volatility compression -> breakout (each coin)")
atr=(Hh-Ll).rolling(24).mean(); atrl=(Hh-Ll).rolling(24*20).mean()
sq=(atr/atrl)<0.6
hi=Hh.rolling(24).max().shift(1); lo=Ll.rolling(24).min().shift(1)
sig=pd.DataFrame(0.0,index=C.index,columns=C.columns)
sig[(C>hi)&sq.shift(1)]=1; sig[(C<lo)&sq.shift(1)]=-1
pos=sig.replace(0,np.nan).ffill(limit=24).fillna(0)
report("squeeze breakout, hold 24h",pos)
sig2=sig.copy(); sig2[(C>hi)]=1; sig2[(C<lo)]=-1
report("plain 24h breakout (no squeeze), hold 24h",sig2.replace(0,np.nan).ffill(limit=24).fillna(0))

print("== 6. short-term reversal after extreme hourly move (z>3)")
z=R/R.rolling(24*7).std()
for lim in [3,4]:
    s=(-np.sign(z)*(z.abs()>lim)).replace(0,np.nan).ffill(limit=4).fillna(0)
    report(f"fade |z|>{lim}, hold 4h",s)
    report(f"follow |z|>{lim}, hold 4h",-s)

print("== 7. residual (vs BTC) reversal, daily")
for lb in [24,72]:
    beta_res=R[alts].sub(b,axis=0).rolling(lb).sum(); rk=beta_res.rank(axis=1,pct=True)
    pos=(rk<=0.25).astype(float)-(rk>0.75).astype(float); pos=pos[pos.index.hour==0].reindex(pos.index).ffill()
    report(f"residual reversal {lb}h (vs BTC)",pos,R[alts])
