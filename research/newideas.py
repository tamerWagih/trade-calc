from load import *
import warnings; warnings.filterwarnings('ignore')
print("== IDEA 1: intraday momentum (rules from Shen/Urquhart/Wang + Gao et al.)")
rows=[]
for s in SYMS:
    df=load(s); c=df.c; lr=np.log(c).diff()
    day=lr.index.normalize(); d=pd.DataFrame({'r':lr,'day':day,'hm':lr.index.hour*60+lr.index.minute})
    g=lambda a,b: d[(d.hm>=a)&(d.hm<b)].groupby('day').r.sum()
    # bar label = open time; 15m bars
    first=g(0,30); rest=g(0,23*60+30); last=g(23*60+30,24*60)
    us_open=g(13*60+30,14*60); us_last=g(19*60+30,20*60)   # US stock-market open / close
    for name,sig,tgt in [('first 30min -> last 30min (UTC day)',first,last),('first 23.5h -> last 30min',rest,last),('US open 30min -> US close 30min',us_open,us_last)]:
        x=pd.concat([sig,tgt],axis=1).dropna(); x.columns=['s','t']
        pnl=np.sign(x.s)*x.t; rows.append(dict(idea=name,sym=s,per=np.where(x.index<'2024','21-23','24-26'),pnl=pnl.values))
out=[]
for name in dict.fromkeys(r['idea'] for r in rows):
    P=np.concatenate([r['pnl'] for r in rows if r['idea']==name]); per=np.concatenate([r['per'] for r in rows if r['idea']==name])
    for p in ['21-23','24-26']:
        x=P[per==p]; out.append((name,p,len(x),f"{(x>0).mean()*100:.0f}%",f"{x.mean()*1e4:+.1f}",f"{x.mean()*1e4-10:+.1f}"))
print(pd.DataFrame(out,columns=['rule','period','trades','win','avg bp before fees','avg bp after 0.1% fees']).to_string(index=False))

print("\n== IDEA 2: trend ensemble + BTC filter (alts only when BTC trend says long)")
exec(open('trend.py').read().split("w=w.where((w-w.shift(1))")[0].split("sig=sum(")[0])
sig=sum(model(n) for n in LBS)/len(LBS)
vol=R.rolling(60).std()*np.sqrt(365)
def bt(sig,label):
    w=((sig*(0.25/vol)).clip(upper=1)/len(SYMS)).fillna(0)
    prev=0*w.iloc[0]; rws=[]
    for t,row in w.iterrows():
        chg=(row-prev).abs(); upd=(chg>0.1/len(SYMS))|((row==0)&(prev!=0))|((row>0)&(prev==0))
        prev=prev.where(~upd,row); rws.append(prev.copy())
    p=pd.DataFrame(rws,index=w.index).shift(1).fillna(0)
    net=(p*R).sum(axis=1)-p.diff().abs().sum(axis=1)*0.0005; net=net[net.index>='2022-01-01']
    k=0.25/max(p[p.index>='2022'].sum(axis=1).mean(),1e-9)   # scale so avg 25% of capital invested, for fair comparison
    n3=net*k; eq=(1+n3).cumprod()
    yr=(n3.groupby(n3.index.year).apply(lambda r:(1+r).prod()-1)*100).round(0).astype(int).tolist()
    print(f"{label:38s} yearly {(eq.iloc[-1]**(365/len(n3))-1)*100:5.1f}%  sharpe {n3.mean()/n3.std()*np.sqrt(365):4.2f}  worst drop {((eq/eq.cummax())-1).min()*100:5.0f}%  by year 22-26 {yr}")
bt(sig,"Trend ensemble (from before)")
btcon=(sig['BTCUSDT']>=0.5)
bt(sig.mul(btcon.astype(float),axis=0), "+ BTC filter (BTC >=5 of 9 long)")
rk=sig.rank(axis=1,ascending=False,method='first')
bt(sig.where(rk<=5,0).mul(btcon.astype(float),axis=0),"+ BTC filter + only 5 strongest coins")
