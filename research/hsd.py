# Python port of "HSD Align Strategy" (Pine v6) – same defaults.
from load import *
import sys
FEE=0.0005
def ema(x,n): return pd.Series(x).ewm(span=n,adjust=False).mean().values
def rma(x,n): return pd.Series(x).ewm(alpha=1/n,adjust=False).mean().values
def supertrend(h,l,c,f=3.0,n=10):
    pc=np.r_[np.nan,c[:-1]]; tr=np.nanmax(np.c_[h-l,np.abs(h-pc),np.abs(l-pc)],axis=1); tr[0]=h[0]-l[0]
    atr=rma(tr,n); src=(h+l)/2; up=src-f*atr; dn=src+f*atr
    N=len(c); lo=np.empty(N); hi=np.empty(N); d=np.empty(N); st=np.empty(N)
    lo[0]=up[0]; hi[0]=dn[0]; d[0]=1; st[0]=hi[0]
    for i in range(1,N):
        lo[i]=up[i] if (up[i]>lo[i-1] or c[i-1]<lo[i-1]) else lo[i-1]
        hi[i]=dn[i] if (dn[i]<hi[i-1] or c[i-1]>hi[i-1]) else hi[i-1]
        if st[i-1]==hi[i-1]: d[i]=-1 if c[i]>hi[i] else 1
        else: d[i]=1 if c[i]<lo[i] else -1
        st[i]=lo[i] if d[i]==-1 else hi[i]
    return st,d
def run(df,exit_rr=2.0,hl=70,dlen=20):
    o,h,l,c=[df[k].values for k in 'ohlc']
    hull=ema(2*ema(c,hl//2)-ema(c,hl),round(np.sqrt(hl)))
    hu=np.r_[False,False,hull[2:]>hull[:-2]]; hd=np.r_[False,False,hull[2:]<hull[:-2]]
    st,d=supertrend(h,l,c); su=d<0; sd=d>0
    hh=pd.Series(h).rolling(dlen).max().shift(1).values; ll=pd.Series(l).rolling(dlen).min().shift(1).values
    dt=np.zeros(len(c)); 
    for i in range(1,len(c)): dt[i]=1 if c[i]>hh[i] else (-1 if c[i]<ll[i] else dt[i-1])
    bull=hu&su&(dt==1); bear=hd&sd&(dt==-1)
    trades=[]; pos=0; last=0; t0=df.index
    for i in range(80,len(c)):
        # 1) exits intrabar on this bar for an open position (stop before target if both touched)
        if pos!=0:
            ex=None
            if pos==1:
                if l[i]<=sl: ex=min(o[i],sl)
                elif tp is not None and h[i]>=tp: ex=max(o[i],tp)
            else:
                if h[i]>=sl: ex=max(o[i],sl)
                elif tp is not None and l[i]<=tp: ex=min(o[i],tp)
            if ex is not None:
                trades.append((t0[ent_i],pos,(ex/ep-1)*pos-2*FEE,risk)); pos=0
        # 2) signals at close
        rl=bull[i] and not bull[i-1] and last!=1; rs=bear[i] and not bear[i-1] and last!=-1
        if rl: last=1
        if rs: last=-1
        for go,dirn in ((rl,1),(rs,-1)):
            if not go: continue
            dist=(c[i]-st[i])*dirn
            if dist<=0: continue
            if pos!=0:   # reverse at close
                trades.append((t0[ent_i],pos,(c[i]/ep-1)*pos-2*FEE,risk)); pos=0
            pos=dirn; ep=c[i]; sl=st[i]; ent_i=i; risk=dist/c[i]
            tp=None if exit_rr is None else c[i]+dirn*dist*exit_rr
        # 3) trail stop (applies from next bar)
        if pos==1 and not rl and su[i] and st[i]>sl: sl=st[i]
        if pos==-1 and not rs and sd[i] and st[i]<sl: sl=st[i]
    t=pd.DataFrame(trades,columns=['t','dir','ret','risk']); t['R']=t.ret/t.risk
    return t
if __name__=='__main__':
    out=[]
    for tf in ['15min','1h','4h']:
        for mode in [2.0,None]:
            allt=[]
            for s in SYMS:
                df=load(s)
                if tf!='15min': df=df.resample(tf).agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
                t=run(df,mode); t['sym']=s; allt.append(t)
            T=pd.concat(allt); T.to_csv(f"hsd_trades_{tf}_{'rr2' if mode else 'ride'}.csv",index=False)
            for lab,m in [('2021-23',T.t<'2024'),('2024-26',T.t>='2024')]:
                x=T[m]; yrs=3 if lab=='2021-23' else 2.75
                gross=(x.ret+2*FEE)/x.risk
                out.append(dict(tf=tf,exit='TP 2R' if mode else 'ride',period=lab,trades=len(x),trades_per_coin_month=round(len(x)/20/yrs/12,1),
                    win=f"{(x.R>0).mean()*100:.0f}%",avgR_after_fees=round(x.R.mean(),3),avgR_before_fees=round(gross.mean(),3),
                    median_stop=f"{x.risk.median()*100:.2f}%",fee_cost_in_R=round((gross-x.R).mean(),3)))
    print(pd.DataFrame(out).to_string(index=False))
