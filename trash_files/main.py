# Import libraries
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd
import threading
import time
import sqlite3
import datetime as dt
global tickers
with open('nasdaq_stocks.csv', 'r') as csv_file:
    content = csv_file.readlines()
    data = [pair.strip().split(';') for pair in content[1:]]
    stocks_dict = {stock[0]: stock[1] for stock in data}
    stock_names = stocks_dict.keys()
    tickers = [stocks_dict[x] for x in stocks_dict]    
    csv_file.close()
print(tickers)
def strtime_to_timestamp(value):
    year = (value[0:4])
    month = (value[4:6])
    day = (value[6:8])
    hour = (value[-8:-6])
    minute = (value[-5:-3])
    return f"{year}-{month}-{day} {hour}:{minute}:00.000"

class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self) 
        self.data = {}
        
    def historicalData(self, reqId, bar):
        print(f"{bar.date}  {bar.close}  {bar.volume}")
        c=db.cursor()
        vals = [strtime_to_timestamp(bar.date),bar.close, bar.volume]
        print(strtime_to_timestamp(bar.date))
        c.execute("INSERT INTO TICKER_{}(time,price,volume) VALUES ('{}',{},{})".format(tickers[reqId], vals[0], vals[1], vals[2]))

        try:
            db.commit()
        except:
            db.rollback()


def usTechStk(symbol,sec_type="STK",currency="USD",exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

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
    
def websocket_con(tickers):
    global db
    db = sqlite3.connect("/Volumes/SSD/Dev/IBKR_Trading_Bots/tbwebsite/base/IBAPI/ticks.db")
    c=db.cursor()
    for i in range(len(tickers)):
        c.execute("CREATE TABLE IF NOT EXISTS TICKER_{} (time datetime primary key,price real(15,5), volume integer)".format(i))
    try:
        db.commit()
    except:
        db.rollback()
    app.run()

app = TradeApp()
app.connect(host='127.0.0.1', port=4001, clientId=23) #port 4002 for ib gateway paper trading/7497 for TWS paper trading
con_thread = threading.Thread(target=websocket_con, args=(tickers,), daemon=True)
con_thread.start()

###################storing trade app object in dataframe#######################
def dataDataframe(TradeApp_obj,symbols):
    "returns extracted historical data in dataframe format"
    df_data = {}
    for symbol in symbols:
        df_data[symbol] = pd.DataFrame(TradeApp_obj.data[symbols.index(symbol)])
        df_data[symbol].set_index("Date",inplace=True)
    TradeApp_obj.data = {}
    return df_data


#extract and store historical data in dataframe repetitively
for ticker in tickers:
    histData(tickers.index(ticker),usTechStk(ticker),'6 M', '1 hour')
    time.sleep(4)