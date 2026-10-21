# Ensemble both ways: weight = (longScore - shortScore)/9, longs need BTC long>=5, shorts need BTC short>=5. Vol-scaled.
from load import *
import warnings; warnings.filterwarnings('ignore')
LBS=[5,10,20,30,60,90,150,250,360]
def sc(H,L,C):
    a=0;b=0
    for n in LBS:
        up=H.rolling(n).max().shift(1); dn=L.rolling(n).min().shift(1); mid=(up+dn)/2
        x=pd.DataFrame(np.nan,index=C.index,columns=C.columns); x[C>up]=1; x[C<mid]=0; a=a+x.ffill().fillna(0)
        y=pd.DataFrame(np.nan,index=C.index,columns=C.columns); y[C<dn]=1; y[C>mid]=0; b=b+y.ffill().fillna(0)
    return a,b
M={s:load(s) for s in SYMS}
for tf,bpy in [('1D',365),('4h',365*6),('1h',365*24)]:
    D={s:M[s].resample(tf).agg({'h':'max','l':'min','c':'last'}) for s in SYMS}
    C=pd.DataFrame({s:D[s].c for s in SYMS}); H=pd.DataFrame({s:D[s].h for s in SYMS}); L=pd.DataFrame({s:D[s].l for s in SYMS})
    R=C.pct_change().fillna(0); A,Bs=sc(H,L,C)
    vol=R.rolling(60).std()*np.sqrt(bpy)
    lon=(A/9).mul((A['BTCUSDT']>=5).astype(float),axis=0); sho=(Bs/9).mul((Bs['BTCUSDT']>=5).astype(float),axis=0)
    for name,sig in [('long only',lon),('short only',-sho),('both ways',lon-sho)]:
        w=(sig*(0.25/vol).clip(upper=1/0.25*0+4)).clip(-1,1)/20
        p=w.shift(1).fillna(0); net=(p*R).sum(axis=1)-p.diff().abs().sum(axis=1)*0.0005
        net=net[net.index>='2022-01-01']; pe=p[p.index>='2022-01-01'].abs().sum(axis=1).mean()
        n=net*(0.25/pe); dly=n.resample('1D').sum(); eq=(1+dly).cumprod()
        yr=(dly.groupby(dly.index.year).apply(lambda r:(1+r).prod()-1)*100).round(0).astype(int).tolist()
        trades=(p.diff().abs()>0).sum().sum()/len(SYMS)/ (len(p)/bpy) 
        print(f"{tf:3s} {name:11s} yearly {(eq.iloc[-1]**(365/len(dly))-1)*100:6.1f}%  sharpe {dly.mean()/dly.std()*np.sqrt(365):5.2f}  worst drop {((eq/eq.cummax())-1).min()*100:5.0f}%  by year 22-26 {yr}  size changes/coin/yr {trades:.0f}")
