import pandas as pd
import datetime as dt
import os
import pandas_datareader as web
from sklearn.model_selection import train_test_split
import datetime as dt
import time
import numpy as np
from joblib import dump
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer 
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor


def strtime_to_timestamp(value):
    year = int(value[0:4])
    month = int(value[4:6])
    day = int(value[6:8])
    hour = int(value[-8:-6])
    minute = int(value[-5:-3])
    return pd.Timestamp(year=year, month=month, day=day,hour=hour, minute=minute)

def extractStockData():
    pass

def extractFedData(start, end):
        # "var_indep_dict" est le dictionnaire stockant les variables explicative. Les clefs correspondent aux codes des données et
    # les valeurs sont des dataframes
    var_exp_dict = {}

    var_exp_df = pd.DataFrame()

    var_exp = ['dhhngsp','dcoilwtico','dcoilbrenteu', 'will5000prfc','dpropanembtx','dhoilnyh','willresipr',
            'vixcls','gvzcls','ovxcls','vxvcls', 'dexuseu', 'dexusuk', 'dexchus', 'dexjpus', 'dexkous',
            'dexmxus', 'dexinus', 'dexbzus', 'dexszus', 'IHLCHG10740', "IHLCHG10420", "IHLCHG28940", 
            "IHLCHG44060", "DTWEXEMEGS"]

    for i in var_exp:
        # téléchargement sur la fed américaine à l'aide de pandas datareader
        var_exp_dict[i] = web.DataReader(i.upper(), 'fred', start, end)
        if var_exp_df.empty:
            var_exp_df = var_exp_dict[i]
        else:
            var_exp_df = var_exp_df.join(var_exp_dict[i])
    
    return var_exp_df

def learnNewModel():
    ###will be replaced in sql soon###
    path = "/Volumes/SSD/Data/Tick"

    dir_list = os.listdir(path)

    data_dict = {stock.replace('data.csv',''): None for stock in dir_list if stock != '.DS_Store'}
    for stock in data_dict:
        data_dict[stock] = pd.read_csv(path+f'/{stock}data.csv')
    stocks = data_dict.keys()
    ###will be replaced in sql soon###

    df_open = pd.DataFrame()

    for ticker, data in enumerate(data_dict):
        df_open[ticker] = data

    # 'start' et "end" correspondent à la date de début et la date de fin des séries de donnés que nous allons importer
    start = df_open.index.tolist()[0].to_pydatetime()
    end = df_open.index.tolist()[-1].to_pydatetime()

    var_exp = extractFedData(start, end)

    df = pd.merge_asof(df_open, var_exp, on="Date").set_index('Date')

    num_pipeline = Pipeline([
            ('imputer', IterativeImputer()), # imputs median for NaN values
            ('std_scaler', StandardScaler()), # scales data (transformer)
        ])

    dump(num_pipeline, "pipeline.pkl")

    for stock in stocks:
        y_variables = [i for i in stocks if i != stock]
        y_variables += var_exp.columns

        X_train = df[y_variables]
        y_train = df[stock]


        X_train = num_pipeline.fit_transform(X_train)
        X_train = pd.DataFrame(X_train)

        forest_reg = RandomForestRegressor()
        forest_reg.fit(X_train, y_train)

        path = os.getcwd()
        models_path = path + "/models"
        os.chdir(models_path)
        dump(forest_reg, f'{stock}.pkl')
        os.chdir(path)



        






