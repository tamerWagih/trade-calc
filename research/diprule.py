exec(open('ml1h.py').read().split("HZ=4")[0])
fwd4=(C.shift(-4)/C-1)
def test(name,cond,hours=None):
    c=cond.copy()
    if hours is not None: c=c & pd.DataFrame({s:C.index.hour.isin(hours) for s in SYMS},index=C.index)
    rows=[]
    for s in SYMS:
        idx=c.index[c[s].fillna(False).values]; last=None
        for t in idx:
            if last is not None and t<last+pd.Timedelta(hours=4): continue
            last=t; rows.append((t,s,fwd4.at[t,s]))
    T=pd.DataFrame(rows,columns=['t','s','g']).dropna(); T['n']=T.g-0.001
    out=[]
    for lab,m in [('2021-22 (unseen)',T.t<'2023'),('2023-26',T.t>='2023')]:
        x=T[m]; out.append(f"{lab}: n={len(x):5d} win {(x.n>0).mean()*100:3.0f}% avg {x.n.mean()*1e4:+6.1f}bp ±{1.96*x.n.std()/np.sqrt(max(len(x),1))*1e4:4.1f}")
    print(f"{name:44s}"," | ".join(out))
dip=(F['r24']<-1)&(F['btc4']<-0.5)&(F['volratio']>1.1)&(F['ema200']<-3)
test("LONG panic dip (all hours)",dip)
test("LONG panic dip, 18-23 UTC",dip,range(18,24))
test("LONG panic dip, other hours",dip,list(range(0,18)))
test("LONG simpler: r24<-1 & btc4<-0.5",(F['r24']<-1)&(F['btc4']<-0.5))
test("LONG simplest: r24 < -1.5",F['r24']<-1.5)
spike=(F['r24']>1)&(F['btc4']>0.5)&(F['volratio']>1.1)&(F['ema200']>3)
fwd4n=-fwd4; fwd4,_b=fwd4n,fwd4
test("SHORT mirror: euphoric spike",spike)
fwd4=_b
