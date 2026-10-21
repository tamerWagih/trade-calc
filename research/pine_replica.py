# Same logic as pine/trend-ensemble-btc-filter.pine, one coin = one chart with 1000 USDT, defaults.
from load import *
LBS=[5,10,20,30,60,90,150,250,360]
def daily(s): return load(s).resample('1D').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
def score(d):
    tot=0
    for n in LBS:
        up=d.h.rolling(n).max().shift(1); dn=d.l.rolling(n).min().shift(1); mid=(up+dn)/2
        st=pd.Series(np.nan,index=d.index); st[d.c>up]=1; st[d.c<mid]=0; tot=tot+st.ffill().fillna(0)
    return tot
btc=score(daily('BTCUSDT'))
def sim(s,use_btc=True,tv=50,maxe=1.0,reb=0.10,fee=0.0005):
    d=daily(s); sc=score(d); on=(btc.reindex(d.index)>=5) if use_btc else pd.Series(True,index=d.index)
    vol=(d.c.pct_change().rolling(60).std()*np.sqrt(365)*100)
    frac=((sc/9)*np.minimum(1,tv/vol)).where(on,0).fillna(0).clip(upper=maxe)
    eq=1000.0; q=0.0; curve=[]; ntr=0
    o=d.o.values; c=d.c.values; f=frac.values
    pend=None
    for i in range(len(d)):
        if pend is not None:                         # fill at this bar's open (TradingView default)
            eq-=abs(pend)*o[i]*fee; q+=pend; pend=None; ntr+=1
        eqm=eq+q*(c[i]-(c[i-1] if i else c[i]))
        if i: eq=eq+q*(c[i]-c[i-1])
        tgt=eq*f[i]/c[i]; diff=tgt-q
        if q>0 and tgt==0: pend=-q
        elif tgt>0 and (q==0 or abs(diff)*c[i]>eq*reb): pend=diff if diff>0 else -min(-diff,q)
        curve.append(eq)
    e=pd.Series(curve,index=d.index); e=e[e.index>='2022-01-01']; e=e/e.iloc[0]*1000
    yrs=len(e)/365; dd=(e/e.cummax()-1).min()
    bh=d.c[d.index>='2022-01-01']; bh=bh/bh.iloc[0]
    return dict(coin=s.replace('USDT',''),final=round(e.iloc[-1]),yearly=f"{((e.iloc[-1]/1000)**(1/yrs)-1)*100:+.0f}%",worst_drop=f"{dd*100:.0f}%",
                orders=ntr,buy_hold_final=round(bh.iloc[-1]*1000),buy_hold_drop=f"{(bh/bh.cummax()-1).min()*100:.0f}%")
rows=[sim(s) for s in SYMS]; T=pd.DataFrame(rows)
print("Pine defaults (BTC filter 5/9, target vol 50%, no leverage), 1000 USDT from 2022-01-01 to 2026-10-02")
print(T.to_string(index=False))
print("coins finishing above 1000:",(T.final>1000).sum(),"/20 | strategy median final",int(T.final.median()),"| buy&hold median final",int(T.buy_hold_final.median()))
nob=pd.DataFrame([sim(s,use_btc=False) for s in SYMS])
print("WITHOUT BTC filter: coins above 1000:",(nob.final>1000).sum(),"/20 | median final",int(nob.final.median()))
T.to_csv('pine_expected.csv',index=False)
