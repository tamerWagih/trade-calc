exec(open('discrete.py').read().split("M={s:load(s)")[0])
M={s:load(s) for s in SYMS}
D={s:M[s].resample('4h').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna() for s in SYMS}
btc=pd.Series(score(D['BTCUSDT']),index=D['BTCUSDT'].index)
rows=[]
for s in SYMS:
    d=D[s]; b=btc.reindex(d.index).values
    sp=pd.DataFrame(run(d,b,5,3,None,None),columns=['t','ret','risk']); sp=sp[sp.t>='2022-01-01']
    fu=pd.DataFrame(run(d,b,5,3,5,None),columns=['t','ret','risk']); fu=fu[fu.t>='2022-01-01']
    eqs=(1+sp.ret).cumprod(); eqf=(1+0.01*fu.ret/fu.risk).cumprod()
    bh=d.c[d.index>='2022-01-01']
    rows.append(dict(coin=s[:-4],spot_trades=len(sp),spot_win=f"{(sp.ret>0).mean()*100:.0f}%",spot_1000_to=round(1000*eqs.iloc[-1]),spot_worst=f"{(eqs/eqs.cummax()-1).min()*100:.0f}%",
        fut_trades=len(fu),fut_win=f"{(fu.ret>0).mean()*100:.0f}%",fut_1000_to=round(1000*eqf.iloc[-1]),fut_worst=f"{(eqf/eqf.cummax()-1).min()*100:.0f}%",buyhold_1000_to=round(1000*bh.iloc[-1]/bh.iloc[0])))
T=pd.DataFrame(rows); print(T.to_string(index=False))
print("spot >1000:",(T.spot_1000_to>1000).sum(),"/20 median",int(T.spot_1000_to.median()),"| futures >1000:",(T.fut_1000_to>1000).sum(),"/20 median",int(T.fut_1000_to.median()),"| B&H median",int(T.buyhold_1000_to.median()))
