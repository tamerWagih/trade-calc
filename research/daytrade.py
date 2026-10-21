# Day trading WITH a daily trend bias, both directions. Rules fixed before running.
# Bias (from yesterday's daily close): LONG day if coin long-score>=5/9 and BTC long-score>=5/9,
#   SHORT day if coin short-score>=5/9 and BTC short-score>=5/9 (mirror Donchian: short on N-day low, cover above mid). Else no trade.
# A "prior-day break": stop order at yesterday's high (long) / low (short). Stop = 0.5 x daily ATR14. Exit at stop or 00:00 UTC.
# B "first-hour break": range of 00:00-01:00 UTC; after 01:00 break in bias direction. Stop = other side of range. Exit at stop or day end.
# C "bias only": enter at 00:00 open in bias direction, stop 0.5 ATR, exit day end.   (all: 0.05% fee per side, stop beats target if same bar)
from load import *
import warnings; warnings.filterwarnings('ignore')
LBS=[5,10,20,30,60,90,150,250,360]; FEE=0.0005
def scores(d):
    L=0;S=0
    for n in LBS:
        up=d.h.rolling(n).max().shift(1); dn=d.l.rolling(n).min().shift(1); mid=(up+dn)/2
        a=pd.Series(np.nan,index=d.index); a[d.c>up]=1; a[d.c<mid]=0; L=L+a.ffill().fillna(0)
        b=pd.Series(np.nan,index=d.index); b[d.c<dn]=1; b[d.c>mid]=0; S=S+b.ffill().fillna(0)
    return L,S
M={s:load(s) for s in SYMS}
DD={s:M[s].resample('1D').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna() for s in SYMS}
bL,bS=scores(DD['BTCUSDT'])
res=[]
for s in SYMS:
    d=DD[s]; L,S=scores(d)
    tr=pd.concat([d.h-d.l,(d.h-d.c.shift()).abs(),(d.l-d.c.shift()).abs()],axis=1).max(axis=1); atr=tr.rolling(14).mean()
    bias=pd.Series(0,index=d.index); bias[(L>=5)&(bL.reindex(d.index)>=5)]=1; bias[(S>=5)&(bS.reindex(d.index)>=5)]=-1
    # values known at yesterday's close, used today
    B=bias.shift(1); PH=d.h.shift(1); PL=d.l.shift(1); A=atr.shift(1)
    m=M[s]; days=m.index.normalize()
    for day,x in m.groupby(days):
        if day<pd.Timestamp('2022-01-01') or day not in B.index: continue
        b=B[day]
        if b not in (1,-1) or np.isnan(A[day]): continue
        o,h,l,c=x.o.values,x.h.values,x.l.values,x.c.values
        def sim(i0,entry,stop):
            # from bar i0 on, entry already filled at 'entry'
            for j in range(i0,len(c)):
                if b==1 and l[j]<=stop: return min(stop,o[j]) if j>i0 else stop
                if b==-1 and h[j]>=stop: return max(stop,o[j]) if j>i0 else stop
            return c[-1]
        def rec(name,entry,stop,ex):
            risk=abs(entry-stop)/entry
            if risk<=0: return
            ret=(ex/entry-1)*b-2*FEE; res.append((name,s,day,b,ret/risk,risk))
        # A prior-day break
        lvl=PH[day] if b==1 else PL[day]
        hit=np.where(h>=lvl)[0] if b==1 else np.where(l<=lvl)[0]
        if len(hit):
            i=hit[0]; e=max(lvl,o[i]) if b==1 else min(lvl,o[i]); st=e-b*0.5*A[day]
            rec('A prior-day break',e,st,sim(i,e,st))
        # B first-hour break
        rh,rl=h[:4].max(),l[:4].min(); lvl=rh if b==1 else rl
        hit=(np.where(h[4:]>=lvl)[0] if b==1 else np.where(l[4:]<=lvl)[0])
        if len(hit):
            i=hit[0]+4; e=max(lvl,o[i]) if b==1 else min(lvl,o[i]); st=rl if b==1 else rh
            rec('B first-hour break',e,st,sim(i,e,st))
        # C bias only
        e=o[0]; st=e-b*0.5*A[day]; rec('C bias only (enter 00:00)',e,st,sim(0,e,st))
T=pd.DataFrame(res,columns=['rule','sym','day','dir','R','risk']); T.to_csv('daytrade_trades.csv',index=False)
T['period']=np.where(T.day<'2024-07-01','2022-mid24','mid24-2026')
g=T.groupby(['rule','period','dir']).R.agg(['count','mean','std'])
g['95%±']=1.96*g['std']/np.sqrt(g['count']); g['win%']=T.groupby(['rule','period','dir']).R.apply(lambda r:(r>0).mean()*100)
print(g[['count','win%','mean','95%±']].round(3).to_string())
print("\nmedian stop size:",T.groupby('rule').risk.median().mul(100).round(2).to_dict())
