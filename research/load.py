import json, numpy as np, pandas as pd
import os, sys
LIB=os.environ.get('LIB', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'trainer-lib'))+'/'
def load(sym):
    c=json.load(open(LIB+sym+'.json')); d=np.array(c['d'],dtype=np.int64).reshape(-1,4)
    C=c['c0']+np.cumsum(d[:,0]); 
    df=pd.DataFrame({'o':C+d[:,1],'h':C+d[:,2],'l':C+d[:,3],'c':C},dtype=float)
    df.index=pd.to_datetime(c['t0']+np.arange(len(df))*900000,unit='ms')
    return df
SYMS=json.load(open(LIB+'index.json'))
