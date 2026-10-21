# Donchian-ensemble trend following, long-only, vol-targeted. Rules fixed before running.
from load import *
D={s:load(s).resample('1D').agg({'h':'max','l':'min','c':'last'}) for s in SYMS}
C=pd.DataFrame({s:D[s].c for s in SYMS}); H=pd.DataFrame({s:D[s].h for s in SYMS}); L=pd.DataFrame({s:D[s].l for s in SYMS})
R=C.pct_change().fillna(0)
LBS=[5,10,20,30,60,90,150,250,360]
def model(n):
    up=H.rolling(n).max().shift(1); dn=L.rolling(n).min().shift(1); mid=(up+dn)/2
    st=pd.DataFrame(np.nan,index=C.index,columns=C.columns)
    st[C>up]=1; st[C<mid]=0          # enter on new N-day high, exit when price falls below channel middle
    return st.ffill().fillna(0)
sig=sum(model(n) for n in LBS)/len(LBS)            # 0..1: how many of the 9 models are long
vol=R.rolling(60).std()*np.sqrt(365)
w=(sig*(0.25/vol)).clip(upper=1.0)/len(SYMS)       # 25% yearly vol target per coin, max 1x, equal capital per coin
w=w.where(C.notna(),0).fillna(0)
w=w.where((w-w.shift(1)).abs()>0.2/len(SYMS)).ffill().fillna(0)  # rebalance only on meaningful changes (cuts fees)
p=w.shift(1).fillna(0)
net=(p*R).sum(axis=1)-(p.diff().abs().sum(axis=1)*0.0005)
bh=R.mean(axis=1); btc=R['BTCUSDT']
start='2022-01-01'   # first year is warm-up for the 360-day lookback
def stats(x):
    x=x[x.index>=start]; eq=(1+x).cumprod(); dd=(eq/eq.cummax()-1).min()
    yrs=len(x)/365; cagr=eq.iloc[-1]**(1/yrs)-1; sh=x.mean()/x.std()*np.sqrt(365)
    return f"yearly {cagr*100:6.1f}%  sharpe {sh:5.2f}  worst drop {dd*100:6.1f}%"
print("TREND ENSEMBLE  ",stats(net)); print("Buy&hold 20 coins",stats(bh)); print("Buy&hold BTC    ",stats(btc))
print("avg exposure", round(p[p.index>=start].sum(axis=1).mean()*100),"% of capital")
yr=lambda x:(x[x.index>=start].groupby(x[x.index>=start].index.year).apply(lambda r:(1+r).prod()-1)*100).round(0).astype(int).tolist()
print("by year 2022..2026  trend:",yr(net)," B&H:",yr(bh)," BTC:",yr(btc))
# robustness: drop half the lookbacks
for sub in [[5,20,60,150,360],[10,30,90,250]]:
    s2=sum(model(n) for n in sub)/len(sub); w2=((s2*(0.25/vol)).clip(upper=1)/len(SYMS)).fillna(0)
    p2=w2.shift(1).fillna(0); n2=(p2*R).sum(axis=1)-p2.diff().abs().sum(axis=1)*0.0005
    print("lookbacks",sub,stats(n2))
