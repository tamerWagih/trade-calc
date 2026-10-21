# Discrete version of the ensemble, long-only. Per coin, one trade at a time.
# Entry: at bar close when coin score >= ENTER and BTC score >= 5. (re-entry allowed after exit)
# Exit signal: coin score < EXIT_LT or BTC score < 5 -> exit at that close.
# Futures stop: trailing ATR stop (k x ATR14 below highest close since entry, only tightens), checked intrabar.
# TP: none (ride) or R-multiple. Fees 0.05%/side. R = net return / initial stop distance.
from load import *
import warnings; warnings.filterwarnings('ignore')
LBS=[5,10,20,30,60,90,150,250,360]; FEE=0.0005
def score(d):
    t=0
    for n in LBS:
        up=d.h.rolling(n).max().shift(1); dn=d.l.rolling(n).min().shift(1); mid=(up+dn)/2
        a=pd.Series(np.nan,index=d.index); a[d.c>up]=1; a[d.c<mid]=0; t=t+a.ffill().fillna(0)
    return t.values
def run(d,btc,ent,exl,k,tp):
    s=score(d); o,h,l,c=[d[x].values for x in 'ohlc']
    tr=np.maximum(h-l,np.maximum(abs(h-np.r_[c[0],c[:-1]]),abs(l-np.r_[c[0],c[:-1]]))); atr=pd.Series(tr).rolling(14).mean().values
    out=[]; pos=False
    for i in range(1,len(c)):
        if pos:
            ex=None
            if k and l[i]<=sl: ex=min(o[i],sl)
            elif tp and h[i]>=tgt: ex=max(o[i],tgt)
            elif s[i]<exl or btc[i]<5: ex=c[i]
            if ex is not None:
                out.append((d.index[ei],(ex/ep-1)-2*FEE,risk)); pos=False; continue
            if k: sl=max(sl,c[i]-k*atr[i])
        if not pos and s[i]>=ent and btc[i]>=5 and not np.isnan(atr[i]):
            pos=True; ep=c[i]; ei=i
            sl=c[i]-(k or 3)*atr[i]; risk=(c[i]-sl)/c[i]; tgt=c[i]*(1+tp*risk) if tp else None
    return out
M={s:load(s) for s in SYMS}
rows=[]
for tf in ['4h','1D']:
    D={s:M[s].resample(tf).agg({'o':'first','h':'max','l':'min','c':'last'}).dropna() for s in SYMS}
    btc=pd.Series(score(D['BTCUSDT']),index=D['BTCUSDT'].index)
    for ent,exl in [(5,5),(5,3),(7,4)]:
        for k in [None,3,5]:
            for tp in [None,3]:
                if k is None and tp: continue
                T=[]
                for s in SYMS:
                    d=D[s]; T+= [(s,)+x for x in run(d,btc.reindex(d.index).values,ent,exl,k,tp)]
                T=pd.DataFrame(T,columns=['sym','t','ret','risk']); T=T[T.t>='2022-01-01']; T['R']=T.ret/T.risk
                a=T[T.t<'2024-07-01'];b=T[T.t>='2024-07-01']
                yrs=4.75
                rows.append(dict(tf=tf,enter=f">={ent}",exit=f"<{exl}",stop=f"{k}xATR trail" if k else "none (spot)",tp=f"{tp}R" if tp else "ride",
                    trades_per_coin_month=round(len(T)/20/yrs/12,1),win=f"{(T.R>0).mean()*100:.0f}%",
                    avgR_22_mid24=round(a.R.mean(),2),avgR_mid24_26=round(b.R.mean(),2),
                    avg_trade_pct=f"{T.ret.mean()*100:+.2f}%",coins_pos=(T.groupby('sym').ret.sum()>0).sum()))
print(pd.DataFrame(rows).to_string(index=False))
