#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 11:49:04 2022

@author: felix
"""

# Import libraries
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import datetime as dt
import pytz as pytz
import threading
import sqlite3
import pandas as pd
import time
from pandas.tseries.holiday import USFederalHolidayCalendar as calendar
#from optimizer import Portfolio
import os
import yahoo_fin.stock_info as si

# will need to be added to global.py later
global stocks_dict
global stocks_names
path = os.getcwd()

models_path = path 

def fetchTickers():
    stocks = si.tickers_nasdaq()
    pd.DataFrame(stocks).to_csv("base/IBAPI/stocks_data.csv", ",", index_label=False)



global tickers
fetchTickers()
tickers = pd.read_csv("base/IBAPI/stocks_data.csv")
print(tickers.iloc[0:5])
tickers = tickers["0"].to_list()

#tickers = ["META","INTC","AMZN", 'FTNT', 'MSFT', 'GOOGL', 'TSLA', 'JNJ', 'UNH', 'META', 'SHOP']
global holidays
holidays = calendar().holidays(start='2022-01-01')
holidays = [holiday.date() for holiday in holidays]

global exit_event
exit_event = threading.Event()

############################# EWrapper functions ##############################

class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self)
        self.data = {}
        self.pos_df = pd.DataFrame(columns = ["Account","Symbol","SecType",
                                               "Currency","Position","Avg cost"])
        self.summary_df = pd.DataFrame(columns = ["ReqId","Account","Tag","Value","Currency"])
        
    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)

    def accountSummary(self, reqId, account, tag, value, currency):
        super().accountSummary(reqId, account, tag, value, currency)
        dictionary = {"ReqId":reqId, "Account": account, "Tag": tag, "Value": value, "Currency": currency}
        self.summary_df = self.summary_df.append(dictionary, ignore_index=True)

    def position(self, account, contract, position, avgCost):
        super().position(account, contract, position, avgCost)
        dictionary = {"Account":account, "Symbol": contract.symbol, "SecType": contract.secType,
                      "Currency": contract.currency, "Position": position, "Avg_cost": avgCost}
        self.pos_df = self.pos_df.append(dictionary, ignore_index=True)

    def historicalData(self, reqId, bar):
        stocks = si.tickers_nasdaq()
        print(f'Time: {bar.date}, Close: {bar.close}, Volume {bar.volume}')
        c=db.cursor()

        if reqId not in self.data:
            self.data[reqId] = [{"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume}]
            vals = [dt.datetime.fromtimestamp(bar.date).strftime("%Y-%m-%d %H:%M:%S"),bar.close, bar.volume]
            query = "INSERT INTO TICKER_{}(time,price,volume) VALUES (?,?,?)".format(tickers[reqId])
            c.execute(query,vals)
            
        else:
            self.data[reqId].append({"Date":bar.date,"Open":bar.open,"High":bar.high,"Low":bar.low,"Close":bar.close,"Volume":bar.volume})
    
    # calls tickByTickAllLast() and sends data to SQL database
    def tickByTickAllLast(self, reqId, tickType, time, price, size, tickAtrribLast, exchange, specialConditions):
        super().tickByTickAllLast(reqId, tickType, time, price, size, tickAtrribLast, exchange, specialConditions)
        if tickType == 1:
            pass
        else:
            c=db.cursor()
            for ms in range(100):
                try:
                    print(" ReqId:", reqId, "Time:", (dt.datetime.fromtimestamp(time)+dt.timedelta(milliseconds=ms)).strftime("%Y%m%d %H:%M:%S.%f"), "Price:", price, "Size:", size)
                    vals = [(dt.datetime.fromtimestamp(time)+dt.timedelta(milliseconds=ms)).strftime("%Y-%m-%d %H:%M:%S.%f"),price, size]
                    query = "INSERT INTO TICKER_{}(time,price,volume) VALUES (?,?,?)".format(tickers[reqId])
                    c.execute(query,vals)
                    break
                except Exception as e:
                    #print(e)
                    pass
                    
        try:
            db.commit()
        except:
            db.rollback()
        
############################### IBAPI functions ###############################
# formalizes contract (stock) objects for IBAPI to understand
def usTechStk(symbol,sec_type="STK",currency="USD",exchange="NASDAQ"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

# handles the requirements for requesting historical data
def histData(req_num,contract,duration,candle_size):
    """extracts historical data"""
    app.reqHistoricalData(reqId=req_num, 
                          contract=contract,
                          endDateTime='',
                          durationStr=duration,
                          barSizeSetting=candle_size,
                          whatToShow='ADJUSTED_LAST',
                          useRTH=1,
                          formatDate=1,
                          keepUpToDate=0,
                          chartOptions=[])	 # EClient function to request contract details

# handles the requirements for requesting streaming data
def streamData(app, req_num, contract):
    """stream tick leve data"""
    app.reqTickByTickData(reqId=req_num, 
                          contract=contract,
                          tickType="AllLast",
                          numberOfTicks=0,
                          ignoreSize=True)

############################ Function (SQL & API) #############################    
def websocket_con(app):

    app.run()

global db
db = sqlite3.connect(os.getcwd()+'/base/IBAPI/ticks.db')

global app
app = TradeApp()

############################# Handling functions ##############################     
def dataDataframe(TradeApp_obj,symbols):
    "returns extracted historical data in dataframe format"
    df_ohlc = {}
    df_data = {}
    for symbol in symbols:
        df_ohlc[symbol] = pd.DataFrame(TradeApp_obj.data[symbols.index(symbol)])
        df_ohlc[symbol].set_index("Date",inplace=True)
        # mean of high and low for every tick
        df_data[symbol] = pd.DataFrame((df_ohlc[symbol].iloc[:]['High']+df_ohlc[symbol].iloc[:]['Low'])/2,
                                       index = df_ohlc[symbol].index,
                                       columns=['Close'])
        
    TradeApp_obj.data = {}
    return df_data

def histToSqlite(TradeApp_obj,symbols, db):
    "returns extracted historical data in dataframe format"
    df_ohlc = {}
    df_data = {}
    for symbol in symbols:
        df_ohlc[symbol] = pd.DataFrame(TradeApp_obj.data[symbols.index(symbol)])
        df_ohlc[symbol].set_index("Date",inplace=True)
        # mean of high and low for every tick
        df_data[symbol] = pd.DataFrame((df_ohlc[symbol].iloc[:]['High']+df_ohlc[symbol].iloc[:]['Low'])/2,
                                       index = df_ohlc[symbol].index,
                                       columns=['Close'])

def get_hist_30sec(ticker, db, start_date):
    data = pd.read_sql('''SELECT * FROM TICKER_{} WHERE time >= '{}';'''.format(ticker, start_date), con=db)                
    data = data.set_index(['time'])
    data.index = pd.to_datetime(data.index)
    price_ohlc= data.loc[:, ['price']].resample('30S').ohlc().dropna()
    price_ohlc.columns = ['open','high','low','close']
    return price_ohlc

'''# removes n oldest data in dataframe and adds n new data to dataframe from sql
def rollDataframe(symbol, df, sql):
    # 1. take latest date (df.index[-1]) and convert it to SQL datetime
    year = df.index[-1][0:4]
    month = df.index[-1][4:6]
    day = df.index[-1][6:8]
    hour = df.index[-1][-8:-6]
    minute = df.index[-1][-5:-3]
    seconds = df.index[-1][-2:]

    sql_time = f'{year}-{month}-{day} {hour}:{minute}:{seconds}'

    # 2. retrieve data from db, query from latest date (df.index[-1])
    new_df = get_hist_30sec(ticker = symbol, db=db, start_date = sql_time)
    
    
    # 3. format retrieved data (mean of every 30 seconds)
    # 4. add new_df to df
    # 5. make sure len(df) == 780
    return None'''

################################ Main function ################################
# creates Portfolio object, and equalizes the weights based on 1 min data
def main():
    tz = pytz.timezone('US/Eastern')
    now = tz.localize(dt.datetime.now())
    
    print('main test 1 satisfied')
    
    if now.hour >= 10 and now.minute >= 30:
        pass
    return None



################################### Program ################################### 


if __name__ == "__main__":
    tz = pytz.timezone('US/Eastern')
    now = tz.localize(dt.datetime.now())
    
    # trading hours condition
    def traidingDayCond():
        tz = pytz.timezone('US/Eastern')
        now = tz.localize(dt.datetime.now())
        return now.time() >= dt.time(9,30) and now.time() < dt.time(15, 59) and now.weekday() < 5 and now.date() not in holidays
    
    print('program test 1 satisfied')
    
    # to be executed only once
    switch_only_once = True
    
    # to manage sql database storage
    switch_deleted = False
    
    # ensures markets are open and that it is not a holiday
    while traidingDayCond():
################################# Connection ##################################
        # will only be executed once
        if switch_only_once is True:
            app = TradeApp()
            app.connect(host='127.0.0.1', port=7497, clientId=23) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
            con_thread = threading.Thread(target=websocket_con, args=(tickers,), daemon=True)
            con_thread.start()
            time.sleep(1)
            
            
            with open('headers/lasttradingday.txt', 'r') as text_file:
                last_trading_day = text_file.read()     
                text_file.close()
                
############################### Pulling data ##################################
            for ticker in tickers:
                # activates streamData function which activates tick by tick data wrapper function
                streamData(tickers.index(ticker),usTechStk(ticker))
                print(f'streaming data for {ticker}')

                time.sleep(1)
                
            switch_only_once = False
        

            
        
        
        
        
        if now.time() > dt.time(16):
            with open('lasttradingday.txt', 'w') as text_file:
                text_file.write(now.date().strftime('%Y-%m-%d'))
                text_file.close()
            break
        
        # will be executed as long as while statement is True
        #main()
     

