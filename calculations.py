import pandas as pd
import numpy as np
from app import app,UPLOAD_FOLDER,RESULT_FOLDER

def getValues():
    df=pd.read_excel(RESULT_FOLDER+'data.xlsx')
    filt=df["ADX"]>0
    df=df.loc[filt]

    df['Time']=df.iloc[:,:1]
    df['Time']=pd.to_datetime(df["Time"],format='%Y-%m-%d %H:%M:%S')

    df['Date']=df['Time'].dt.date

    tempDF=df.groupby('Date').mean()[['+DI','-DI','ADX']]

    df2=pd.DataFrame()
    df2['Date']=pd.date_range(start =df['Date'].min(), 
            end =df['Date'].max(), freq ='1d')
    df2.set_index('Date',inplace=True)

    df2=df2.join(tempDF)

    df2=df2.fillna(df2.mean()).reset_index().round(2)

    df=df2
    return {
        'date':[str(x) for x in df2['Date'].dt.date.values],
        'adx': [float(x) for x in df['ADX'].values], 
        "pdi": [float(x) for x in df['+DI'].values],
        "ndi": [float(x) for x in df['-DI'].values],
        "ADX_MEAN": round(df2['ADX'].mean(), 2)
    }

def calculateTR(df):
    temp=pd.DataFrame()
    temp['H-L']=df["High"]-df['Low']
    temp["L-PC"]=df['Low']-df["Close"].shift(1)
    temp["H-PC"]=df["High"]-df["Close"].shift(1)
    temp["TR"]=temp.max(axis=1)
    temp["TR"].iloc[0:1]=np.nan
    df["TR"]=temp["TR"].copy(deep=True)
    del temp

def calculateDM(df):
    df["+DM"]=df["High"]
    df["+DM"]=df["+DM"].copy(deep=True).diff()
    filt=df["+DM"]<0
    df["+DM"].loc[filt]=0
    
    df["-DM"]=df["Low"]
    df["-DM"]=(df["-DM"].diff()*(-1))
    filt=df["-DM"]<=0
    df["-DM"].loc[filt]=0

def calculateSmoothed(df):
    tr=[float(x) for x in df["TR"].fillna(0).values]
    prev=sum(tr[0:15])
    tr14=[prev]
    for t in tr[15:]:
        prev=prev-(prev/14)+t
        tr14.append(prev)
        
    p_dm=[float(x) for x in df["+DM"].fillna(0).values]
    prev=sum(p_dm[0:15])
    p_dm14=[prev]
    for t in p_dm[15:]:
        prev=prev-(prev/14)+t
        p_dm14.append(prev)
    
    n_dm=[float(x) for x in df["-DM"].fillna(0).values]
    prev=sum(n_dm[0:15])
    n_dm14=[prev]
    for t in n_dm[15:]:
        prev=prev-(prev/14)+t
        n_dm14.append(prev)
    return [tr14,p_dm14,n_dm14]

def calculateDX(df2):
    df2["+DI"]=(df2['+DM14']/df2["TR14"])*100
    df2["-DI"]=(df2['-DM14']/df2["TR14"])*100
    df2["DI-SUM"]=df2["-DI"]+df2["+DI"]
    df2["DI-DIFF"]=(df2["-DI"]-df2["+DI"]).abs()
    df2["DX"]=(df2["DI-DIFF"]/df2["DI-SUM"])*100

def calculateADX(df2):
    dx=[float(x) for x in df2["DX"].fillna(0).values]
    prev=sum(dx[0:14])/14
    adx=[]
    for i in range(13):
        adx.append(np.nan)
    adx.append(prev)
    for t in dx[14:]:
        prev=((prev*13)+t)/14
        adx.append(prev)
    return adx

def calculate():
    df=pd.read_csv(UPLOAD_FOLDER+"data.csv")
    calculateTR(df)
    calculateDM(df)
    tr14,p_dm14,n_dm14=calculateSmoothed(df)
    df2=df[14:].copy(deep=True)
    df2["TR14"]=tr14
    df2["+DM14"]=p_dm14
    df2["-DM14"]=n_dm14
    calculateDX(df2)
    adx=calculateADX(df2)
    df2["ADX"]=adx
    df2=df2.round(2)
    
    final_df=df.join(df2.loc[:,"TR14":])
    final_df=final_df.round(2)
    result_address=RESULT_FOLDER+'data.xlsx'
    final_df.to_excel(result_address,index=False)
