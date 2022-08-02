#from .main import *
import sqlite3
import pandas as pd
import os

db = sqlite3.connect(os.getcwd()+'/ticks.db')
tickers = ["AAPL", "META"]
oldest_date = {}
latest_date = {}
for ticker in tickers:
    c= db.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS TICKER_{} (time datetime primary key, price real(15,5), volume integer)".format(ticker))
    oldest_date[ticker] = c.execute("SELECT time FROM TICKER_{} ORDER BY time DESC LIMIT 1".format(ticker)).fetchall()[0][0]
    latest_date[ticker] = c.execute("SELECT time FROM TICKER_{} ORDER BY time ASC LIMIT 1".format(ticker)).fetchall()[0][0]

print(oldest_date)
print(latest_date)


    
def managesql(tickers):
    c=db.cursor()
    
    # initializing database to store streaming data
    for ticker in tickers:
        c.execute("CREATE TABLE IF NOT EXISTS TICKER_{} (time datetime primary key, price real(15,5), volume integer)".format(ticker))
        pd.read_sql("SELECT time FROM TICKER_{} ORDER BY time ASC".format(ticker), con=db)
    

    try:
        db.commit()
    except:
        db.rollback()

