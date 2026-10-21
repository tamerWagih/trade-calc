exec(open('discrete.py').read().split("M={s:load(s)")[0])
M={s:load(s) for s in SYMS}
D={s:M[s].resample('4h').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna() for s in SYMS}
btc=pd.Series(score(D['BTCUSDT']),index=D['BTCUSDT'].index)
rows=[]
for s in SYMS:
    d=D[s]; sp=pd.DataFrame(run(d,btc.reindex(d.index).values,5,3,None,None),columns=['t','ret','risk']); sp=sp[sp.t>='2022-01-01']
    a=sp[sp.t<'2024-05-01']; b=sp[sp.t>='2024-05-01']
    e=(1+sp.ret).cumprod()
    rows.append(dict(coin=s[:-4],first_half=f"{((1+a.ret).prod()-1)*100:+.0f}%",second_half=f"{((1+b.ret).prod()-1)*100:+.0f}%",
                     total_1000_to=round(1000*e.iloc[-1]),worst_drop=f"{(e/e.cummax()-1).min()*100:.0f}%",both_pos=((1+a.ret).prod()>1)&((1+b.ret).prod()>1),
                     avg_win=f"{sp.ret[sp.ret>0].mean()*100:.1f}%",avg_loss=f"{sp.ret[sp.ret<=0].mean()*100:.1f}%"))
T=pd.DataFrame(rows).sort_values('total_1000_to',ascending=False); print(T.to_string(index=False))
