from .main import *

def get_status():
    with open('base/IBAPI/Data/status.txt', 'r') as status_file:
        status = status_file.read()
        status_file.close()
    if app.isConnected() and status != 'running':
        set_status("connected")    
    return status

def set_status(arg=None):
    print(f"###{app.isConnected()}###")
    if app.isConnected():
        if arg == "connected":
            with open('base/IBAPI/Data/status.txt', 'w') as status_file:
                    status_file.write('connected')
                    status_file.close()
        
        elif arg == "running":
            with open('base/IBAPI/Data/status.txt', 'w') as status_file:
                    status_file.write('running')
                    status_file.close()
    else:
        with open('base/IBAPI/Data/status.txt', 'w') as status_file:
                    status_file.write('not connected')
                    status_file.close()
    

def connect(port_num = 7497):
    app.connect(host='127.0.0.1', port=port_num, clientId=23) #port 4002 for ib gateway paper trading/7497 for TWS paper trading

    if (app.isConnected()):
        set_status("connected")
        # start of the connection thread||
        con_thread = threading.Thread(target=websocket_con, args=(app,), daemon=True)
        con_thread.start()
        time.sleep(1)