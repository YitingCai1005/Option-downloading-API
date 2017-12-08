from __future__ import division
import pandas as pd
import numpy as np
from scipy import stats
from scipy.optimize import brentq
from math import log, sqrt, exp

def expiration (df):
    df['Quote_Time']=pd.to_datetime(df['Quote_Time'])
    df['Expiry'] = pd.to_datetime(df['Expiry'])
    Expiration =( (360 *(df['Expiry'].dt.year -df['Quote_Time'].dt.year)
         + 30*(df['Expiry'].dt.month-df['Quote_Time'].dt.month))
    + (df['Expiry'].dt.day-df['Quote_Time'].dt.day))/360
    df = df.assign(Expiration = Expiration.values)
    return df

def func(sigma,S, K, T, r,type,cStar):
    d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    if type.lower()=="call":
        N_d1 = stats.norm.cdf(d1, 0.0, 1.0)
        N_d2 = stats.norm.cdf(d2, 0.0, 1.0)
        price = (S * N_d1 - K * exp(-r * T) * N_d2)
    elif type.lower()=="put":
        N_n_d1 = stats.norm.cdf(-d1, 0.0, 1.0)
        N_n_d2 = stats.norm.cdf(-d2, 0.0, 1.0)
        price = K * exp(-r * T) * N_n_d2 - S * N_n_d1
    return price-cStar

def find_all_european(f, a, b, iv,pars=(), cutoff=0.005):
    try:
        root = brentq(f, a, b, pars)
        if np.abs(root-iv)<cutoff:
            return 'European'
        else:
            return 'Others'
    except ValueError:
        return 'Others'

def clean(raw_output):
    raw_output=raw_output.reset_index()
    raw_output=expiration(raw_output)
    raw_ouput_dropna = raw_output.dropna()
    # number_of_na = raw_output.__len__() - raw_ouput_dropna.__len__() #print
    clean_data= raw_ouput_dropna
    # number_of_outliers =raw_ouput_dropna.__len__() -  clean_data.__len__()
    #europe
    r=0.03
    Europ_index= clean_data.apply(lambda row:find_all_european(func,-0.999,0.999,row['IV'],
        pars=(row['Underlying_Price'],row['Strike'],row['Expiration'],r,row['Type'],row['Last'])),axis=1)

    EO= clean_data.loc[Europ_index == 'European',:]
    NEO= clean_data.loc[Europ_index!='European',:]
    EO.index = range(0, EO.shape[0])
    NEO.index = range(0, NEO.shape[0])
    # number_of_eu = EO.__len__()
    # number_of_neu = NEO.__len__()

    # columns = ['IsNonstandard','Underlying','Symbol']
    # EO = EO.drop(columns, axis=1)
    return EO

