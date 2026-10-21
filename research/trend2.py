exec(open('trend.py').read().split("w=w.where((w-w.shift(1))")[0])
# rebalance: daily, but skip tiny changes; always act when going to/from zero
prev=0*w.iloc[0]; rows=[]
for t,row in w.iterrows():
    chg=(row-prev).abs()
    upd=(chg>0.1/len(SYMS))|((row==0)&(prev!=0))|((row>0)&(prev==0))
    prev=prev.where(~upd,row); rows.append(prev.copy())
w=pd.DataFrame(rows,index=w.index)
p=w.shift(1).fillna(0); net=(p*R).sum(axis=1)-(p.diff().abs().sum(axis=1)*0.0005)
bh=R.mean(axis=1); btc=R['BTCUSDT']; start='2022-01-01'
def stats(x):
    x=x[x.index>=start]; eq=(1+x).cumprod(); dd=(eq/eq.cummax()-1).min()
    yrs=len(x)/365; cagr=eq.iloc[-1]**(1/yrs)-1; sh=x.mean()/x.std()*np.sqrt(365)
    return f"yearly {cagr*100:6.1f}%  sharpe {sh:5.2f}  worst drop {dd*100:6.1f}%"
yr=lambda x:(x[x.index>=start].groupby(x[x.index>=start].index.year).apply(lambda r:(1+r).prod()-1)*100).round(0).astype(int).tolist()
print("TREND ENSEMBLE   ",stats(net),"| by year 2022-26",yr(net))
ex=p[p.index>=start].sum(axis=1).mean(); print("avg exposure",round(ex*100),"%")
for k in [2,3]:
    print(f"same at {k}x size    ",stats(net*k),"| by year",yr(net*k))
print("B&H 20 coins     ",stats(bh),"| by year",yr(bh)); print("B&H BTC          ",stats(btc),"| by year",yr(btc))
pd.DataFrame({'trend':(1+net[net.index>=start]).cumprod(),'trend_3x':(1+3*net[net.index>=start]).cumprod(),'bh20':(1+bh[bh.index>=start]).cumprod(),'btc':(1+btc[btc.index>=start]).cumprod()}).to_csv('trend_equity.csv')
