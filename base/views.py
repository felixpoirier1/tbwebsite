from readline import set_completion_display_matches_hook
from sys import set_asyncgen_hooks
from telnetlib import STATUS
from django.shortcuts import render
from urllib3 import HTTPResponse
from .IBAPI.main import *
from .IBAPI.learn import *
from .IBAPI.connection import *
#from .IBAPI.stream_manager import *
from pandas.tseries.holiday import USFederalHolidayCalendar as calendar

tz = pytz.timezone('US/Eastern')
        
def trading_bot():
    while True:
        if exit_event.is_set() or get_status() == "not connected":
            time.sleep(2)
            pass
        
        else:
            ## write TB here!!! ###
            print('1')
            time.sleep(2)

    now = tz.localize(dt.datetime.now())
    if now.time() > dt.time(16):
        with open('base/IBAPI/Data/lasttradingday.txt', 'w') as text_file:
            text_file.write(now.date().strftime('%Y-%m-%d'))
            text_file.close()



global bot_thread
bot_thread = threading.Thread(target=trading_bot, args=(), daemon=False)

def traidingDayCond():
        # standardize to eastern timezone to prevent issues
        tz = pytz.timezone('US/Eastern')
        now = tz.localize(dt.datetime.now())
        return now.time() >= dt.time(9,30) and now.time() < dt.time(15, 59) and now.weekday() < 5 #and now.date() not in holidays

connect()

def home(request):
    # list of all the stock names (to be displayed to front end)
    tickers_chosen = []
    context = {}
    print("\n")

    context['stock_names'] = tickers
    # to notify user if he has selected any stocks
    tickers_is_empty = True if len(tickers_chosen)==0 else False

    stoploss = '0%'
    # dataframe of positions handled by TradeApp object
    app.reqPositions()
    #  dataframe of account summary
    reqAccountSumm(app, 1)
    print("HIEWFF")

    summ = []
    #summ = json.loads(json_summ)
    context['summ'] = summ

    # reads the status.txt file to establish wether we are connected or running
    # this may need some improvement as we affirm "connected" regardless of the
    # true connection status

    # whenever a button is pressed (either to start or stop the bot)
    if request.method == "POST":
        #this triggers the learning algorithm
        if 'learn' in request.POST:
            learnNewModel()     # from learn.py 
        # if the trading bot is running (we will stop it)
        if get_status() == 'running':
            # change the status in status.txt from "running" to "connected"
            set_status('connected')
            
            exit_event.set()

            if 'sellall' in request.POST:
                print('-'*15)
            # this sets an event which activates the flag "exit_event"
            # this triggers an if statement in the "trading_bot" function
            # which stops the bot until the flag is deactivated

        elif get_status() == 'not connected':
            connect()
            exit_event.set()
        # if the program is connected (we will start the trading bot)
        elif get_status() == 'connected':
            # change the status in status.txt from "connected" to "running"
            set_status('running')

            # fetches the list of stock selected from the front end
            stocks = request.POST.getlist('stocks')
            context['stocks_selected'] = stocks
            # converts them into tickers_chosen (formatted for IBKR)
            tickers_chosen = [stocks_dict[name] for name in stocks]
            context['tickers'] = tickers_chosen
            # if no tickers_chosen were selected (this will throw a warning on the front-end)
            # should be changed (it makes no sense to start bot with no stocks)
            tickers_is_empty = True if len(tickers_chosen)==0 else False
            context['tickers_is_empty'] = tickers_is_empty
            # creates sql table if there are none for the specific ticker
            #managesql(tickers_chosen)

            # gets the stop loss (must be converted into a float)
            stoploss = request.POST.get('stoploss')
            context['stoploss'] = stoploss

            # either "bot_thread" was not started or a flag was set
            # this handles both exceptions
            try:
                # if the bot was never started
                bot_thread.start()
            except:
                # if the "exit_event" flag was set (this clears it)
                exit_event.clear()

    # to let the front end know wether we're "connected" or "running"
    print(2)
    status = get_status()
    print(3)
    context["status"] = status

    return render(request, 'home.html', context)
