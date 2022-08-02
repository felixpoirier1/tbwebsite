#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 11:53:19 2022

@author: felix
"""

import pandas as pd
import os
import numpy as np
from math import log

class Portfolio(object):
    all = []
    def __init__(self, stocks: list, directory='', dict_data=None, local=True):
        
        self.stocks = [stock.replace('.csv','').upper() for stock in stocks]
        
        if dict_data != None and local == False:
            self.data = dict_data
        else:
            self.data =  {stock: pd.DataFrame() for stock in self.stocks}
            
        self.directory = directory
        self.local = local
        
        Portfolio.all.append(self)
        # if files are stored locally (this is in anticipation that further down I will implement an option that gets data from a data provider)
        if local is True:
            try:
                initial_path = os.getcwd()
                
                os.chdir(directory)
            
            # to catch errors when os can't find the specific folder
            except FileNotFoundError:
                raise FileNotFoundError(f"The folder '{self.directory}' could not be found")
            
            self.ver_stocks = os.listdir()  # list of files stored in the specified directory
            self.file_stocks = []           # list that will copy values from 'stocks' but with formatting to match with "ver_stocks"
            
            for i, stock in enumerate(self.stocks):
                self.file_stocks.append(stock)
                self.file_stocks[i] = stock + '.csv'
                
            
                if self.file_stocks[i] in self.ver_stocks:
                    self.data[stock] = pd.read_csv(self.file_stocks[i], sep=',')
                
                # when the stock doesn't exist or its poorly typed
                else:
                    raise FileNotFoundError(f"The file '{self.file_stocks[i]}' could not be found")
                    
            os.chdir(initial_path)
        
        # do nothing file already provided
        elif local is False:
            pass
        
        else:
            raise ValueError(f"value for local must be a boolean, {local} is not a boolean")
        
                # function that returns day to day yields
        def calcYield(df):
            df['daily_return'] = (df['Close'] / df['Close'].shift(1))-1
            return df  
            
        # function that returns cumulative yields
        def calcCumulYield(df):
            df['cum_return'] = (1+df['daily_return']).cumprod()
            return df
            
        for i in self.data:
            self.data[i] = calcYield(self.data[i])
            self.data[i] = calcCumulYield(self.data[i])
    
    def __repr__(self):
        return f"Portfolio({self.stocks}, {self.directory}, local = {self.local})"
    

        
        
    
    def optimize(self, tick_ret = 0.000001):
        def createCovMat(dict_stocks):
            # première opérations consiste à soustraire de chaque rendement la moyenne des rendements
            df_var = pd.DataFrame()
        
            for i in dict_stocks:
                # soustractions avec conditions try pour éviter les érreurs
                try:
                    df_var[i] = dict_stocks[i].loc[:]['daily_return'] - dict_stocks[i].loc[:]['daily_return'].mean()
                except:
                    pass
                
            # le rendement de la première journée ne peux être calculé donc ces valeurs sont ignorées
            df_var = df_var.iloc[1:]
        
            # utilisation des arrays de numpy qui permettent de faire des calculs matriciels
            mat_var = df_var.to_numpy()
        
            mat_covar = 1/len(mat_var)*np.matmul(np.transpose(mat_var),mat_var)
            
            return mat_covar
        
        def createVectorR(dict_stocks):
            r = []
            for i in dict_stocks:
                # soustractions avec conditions try pour éviter les érreurs
                try:
                    # itération dans les DataFrames pour trouver le rendement moyen de chaque action
                    # puis on le rajoute à la liste r (ne pas utiliser les index 0 puisque == NaN)
                    r.append(dict_stocks[i].iloc[1:]['daily_return'].mean())
                except:
                    pass
        
            # transformation de la liste r en numpy array (vecteur)
            vectorR = np.array([r])
            
            return vectorR
        
        # liste des rendements
        def createMatCovarAug(covMatrix, vectorR, dict_stocks):
        
            # création d'une liste contenant n fois 1 (n étant le nombre d'actions)
            e = [1 for i in range(len(covMatrix))]
        
            # transformation de la liste e en numpy array (vecteur)
            vec_e = np.array(e)
        
            # concatenation entre la matrice des covariances et les vecteurs r et e transposé
            # axis = 1 dit à numpy de de rajouter "r" et "e" en tant que colonnes (à la fin)
            mat_covar_aug = np.concatenate((covMatrix, np.transpose(vectorR)), axis = 1)
            
            mat_covar_aug = np.concatenate((mat_covar_aug, np.transpose([vec_e])), axis = 1)
        
        
            # ceci permet de savoir combien de 0 il faut rajouter aux deux vecteurs r et e
            # comme pour le côté inférieur droit de la matrice des covariances augmentés (voir image en haut)
            zero_to_append = len(mat_covar_aug[0])-len(dict_stocks)
        
            vec_r_aug = vectorR
            vec_e_aug = vec_e
        
            # itération de "zero_to_append" et rajout des "0" aux deux vecteurs
            for i in range(zero_to_append):
                vec_r_aug = np.append(vec_r_aug,0)
                vec_e_aug = np.append(vec_e_aug,0)
        
            # concatenation entre la matrice des covariances et les vecteurs r et e
            # axis = 0 dit à numpy de de rajouter "r" et "e" en tant que lignes (à la fin)
            mat_covar_aug = np.concatenate((mat_covar_aug, [vec_r_aug]), axis = 0)
            mat_covar_aug = np.concatenate((mat_covar_aug, [vec_e_aug]), axis = 0)
            
            return mat_covar_aug
        
        def createCondVec(length, tick_ret=tick_ret):
            continuousYield = log(1+tick_ret)
    
            # création du vecteur des valeurs des conditions de la même taille de les vecteurs r et e
            cond = [0 for i in range(length-2)]
    
            # rajout des valeurs des deux contraintes "rpf" et 1
            cond.extend([continuousYield, 1])
        
            # transformation en numpy.array
            vectorConditions = np.array([cond])
        
            return vectorConditions
        
        def createWeightVector(matCovarAug, vectorConditions):
            # calcul de l'inverse de la matrice des covariances augmentée
            matCovarAugInv = np.linalg.inv(matCovarAug)
        
            # multiplication entre l'inverse de la matrice des covariances augmentée
            # et le vecteur des conditions (ceci retourne le vecteur recherché)
            vectorWeight = np.matmul(matCovarAugInv,np.transpose(vectorConditions))
        
            # le vecteur recherché contient des valeurs pour chaque condition 
            # (celle-ci ne sont pas importantes) nous voulons seulement les poids
            vectorWeight = np.transpose(vectorWeight[:-2])
            
            weightList = [i for i in vectorWeight[0]]
            
            weightDf = pd.DataFrame(weightList, columns = ["pct"], index=self.stocks).transpose()
            
            return weightDf
        
        
        self.covMatrix = createCovMat(self.data)
        self.vectorR = createVectorR(self.data)
        self.matCovarAug = createMatCovarAug(self.covMatrix, self.vectorR, self.data)
        self.vectorConditions = createCondVec(len(self.matCovarAug))
        self.vectorWeight = createWeightVector(self.matCovarAug, self.vectorConditions)
        
        return self.vectorWeight