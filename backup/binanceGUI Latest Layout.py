import PySimpleGUI as sg
import threading
from binance import Client
from binance.exceptions import BinanceAPIException
import json
import sys
import time
import pandas as pd

#key_settings=json.load(open("keys.conf","rt"))
#api_key=key_settings.pop("APIKey")
#api_secret=key_settings.pop("APISecret")

#client = Client(api_key,api_secret) #, testnet=key_settings.pop("testnet"),**key_settings)

api_key="aIiba3UUYLiElcsMaJwQBPcbXig8YtrEJPBYCAvrlGUEWKr0cHXL85uIRtJuU5QL"
api_secret="cjU3D8ZF1LxwN0ZLpyYqqw5id332fSZ9XFt0Cb6DPDRF1br1kBViqZy8afUX9lyJ"

client = Client(api_key, api_secret)

try:
    conf_dict= json.load(open("conf.json"))
    conf_dict["symbol"]=conf_dict["symbol"].upper()+"USDT"
except:
    conf_dict={
        'APIKey': '',
        'APISecret': '',
        'leverage': 20,
        'Isolated': False,
        'reduce': True,
        'symbol': "BTCUSDT",
        'qnty1': 2,
        'radio1': True,
        'radio2': False,
        'price': '',
        'radio3': False,
        'price_tp': '',
        'TLS': False,
        'activation_price': '',
        'callback_rate': 0.8,
        'sec_rate' : True,
        'rate' : 1,
               }


all_symbols_return = client.futures_exchange_info()
all_symbols = [s["symbol"] for s in all_symbols_return["symbols"] if s["symbol"][-4:]=="USDT"]

try:
    df = pd.read_csv("orders.csv", index_col=0)
except FileNotFoundError:
    df = pd.DataFrame()

try:
    df_trades = pd.read_csv("trade_history.csv", index_col=0)
except FileNotFoundError:
    df_trades = pd.DataFrame()


if len(df)>0:
    a = client.futures_account_trades()
    trade_df = pd.DataFrame.from_dict(a)
    if len(trade_df)>0:
        trade_df = trade_df.astype({"price": "float", "qty": "float", "commission": "float"})
        trade_df = trade_df.loc[trade_df["symbol"].eq(conf_dict["symbol"]), :]
        trade_df["PNL"] = trade_df["price"] * trade_df["qty"] + trade_df["commission"]
        trade_df["Trade"] = "Close"

        trade_df = trade_df.loc[trade_df["side"].eq("BUY"), :]
        trade_df = trade_df.merge(df, on="orderId", how="inner", suffixes=("","_r"))
        data_values = trade_df.loc[:,["symbol","side","qty","price","commission" ,"price","PNL","Trade"]].values.tolist()
    else:
        data_values = []
else:
    data_values = []

data_values = []
data_headings = ['Symbol', 'Side', 'Amount', 'Entry Price', "Fee", "Mark Price","Exit Fee", "PNL", "Trade", "orderId"]
visible_column_map = [True, True, True, True, True, True, True, True, True, False]

currencies = ['ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT', 'DOTUSDT', 'UNIUSDT']
currenciess = ['ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT', 'DOTUSDT', 'UNIUSDT']

menu_def = [['&File', ['&API Settings',"&Exit and Save"]],
 ]

###sg.theme('DarkAmber')

layout = [
    [sg.Menu(menu_def)],
    [sg.pin(sg.Frame("API settings",[
        [sg.Text("API key",size=(10,1)),sg.Input(size=(70,1), key="apikey")],
        [sg.Text("API Secret",size=(10,1)),sg.Input(size=(70,1), key="apisecret")],
        [sg.Checkbox("Testnet", key="testnet")],
        [sg.Button("Save keys",key="-saveapi-"), sg.Button("Hide Frame", key="-hideapi-")]
    ],visible=False, key="apiframe"
    ), shrink=True
    )
    ],
    [sg.Column([
    [sg.Text("BALANCE:"), sg.Text("",key="balance",size=(13,1)), sg.Text(" Liquidation Price:"), sg.Text("", key="liquidationPrice", size=(10, 1))],
    [sg.Text("Margin Balance:"), sg.Text("",key="margin",size=(10,1)), sg.Text("Maintence Margin:"), sg.Text("",key="maintence",size=(10,1))],
    [sg.Text("Unrealized PNL:"), sg.Text("",key="PNL",size=(15,1))],  
    [sg.Text("Symbol: "),sg.In(default_text=conf_dict["symbol"][:-4], key="symbol", size=(10,1)), sg.Checkbox('Symbol Lock', default=False,key="symbol_lock"), sg.Button("Change",key="-symbol-"),],
    [sg.Radio('Crossed', 'margin', default=(not conf_dict["Isolated"]), size=(7, 1)),
     sg.Radio('Isolated', 'margin', key="Isolated", default=conf_dict["Isolated"], size=(7, 1))],

    #[sg.Text('Leverage: ', size=(15, 1)), sg.Spin(values=[i for i in range(1, 126)], key="leverage",initial_value=conf_dict["leverage"], size=(6, 1))],
    #[sg.Text('Margin-type: '),sg.Radio('Isolated', 'margin',key="Isolated", default=conf_dict["Isolated"], size=(12, 1)), sg.Radio('Crossed', 'margin', default=(not conf_dict["Isolated"]), size=(12, 1))],

    [sg.Text("Reduce-only"), sg.Checkbox("", size=(1, 1), default=conf_dict["reduce"],key="reduce"), 
      sg.Text('Leverage: ', size=(7, 1)), sg.Spin(values=[i for i in range(1, 126)], key="leverage", initial_value=conf_dict["leverage"], size=(6, 1))],
    [sg.Radio('Market', "RADIO1", default=conf_dict["radio1"], size=(6,1),key="radio1"), sg.Checkbox('Market Lock', default=False,key="market_lock")],
      #sg.Radio('Take Profit', "RADIO1", key="radio3", default=conf_dict["radio3"], size=(8,1))],
     [sg.Radio('Amount ', "RADIO2", default=True, key="amount_value"), sg.Radio('Exact Price ', "RADIO2", key="price_value"), sg.Radio('Percentage ', "RADIO2", key="percentage_value")], 
    [sg.Button('Long',key='-long2-', size=(8, 1)), ##sg.Button('Short',key='-short2-', size=(8, 1)), 
    sg.Text("Percentage") , sg.Spin(values=[i/10 for i in range(1,51)], key="callback_rate",initial_value=conf_dict["callback_rate"], size=(4, 1)),
    sg.Text("Callback") , sg.Spin(values=[i/10 for i in range(1,51)], key="callback_rate",initial_value=conf_dict["callback_rate"], size=(4, 1))],
    [sg.In(key="price", default_text=conf_dict["price"], size=(10, 1)), ### sg.In(key="price", default_text=conf_dict["price"], size=(10, 1)), 
    sg.Radio('Stop Market', "RADIO1",key="radio2", default=conf_dict["radio2"], size=(10,1)), 
      sg.Radio('Trailing Stop Loss', "RADIO1",key="radio2", default=conf_dict["radio2"], size=(14,1))],
    [
        sg.Button('Reset', key="clr1"),
        sg.In(key="qnty1", default_text=conf_dict["qnty1"] if "qnty1" in conf_dict else 0, size=(8, 1)),
        sg.Button('Long',key='-long1-', size=(8, 1)), sg.Button('Short',key='-short1-', size=(8, 1)),
        sg.Button('Cancel',key='-cancel1-', size=(8, 1))
    ],
    [
        sg.Button('Reset', key="clr2"),
        sg.In(key="qnty2", default_text=conf_dict["qnty2"] if "qnty2" in conf_dict else 0, size=(8, 1)),
        sg.Button('Long',key='-long2-', size=(8, 1)), sg.Button('Short',key='-short2-', size=(8, 1)),
        sg.Button('Cancel',key='-cancel2-', size=(8, 1))
    ],
    [
        sg.Button('Reset', key="clr3"),
        sg.In(key="qnty3", default_text=conf_dict["qnty3"] if "qnty3" in conf_dict else 0, size=(8, 1)),
        sg.Button('Long',key='-long3-', size=(8, 1)), sg.Button('Short',key='-short3-', size=(8, 1)),
        sg.Button('Cancel',key='-cancel3-', size=(8, 1)), 
    ],
    [
        sg.Button('Reset', key="clr4"),
        sg.In(key="qnty4", default_text=conf_dict["qnty4"] if "qnty4" in conf_dict else 0, size=(8, 1)),
        sg.Button('Long',key='-long4-', size=(8, 1)), sg.Button('Short',key='-short4-', size=(8, 1)),
        sg.Button('Cancel',key='-cancel4-', size=(8, 1)), 
    ],

     [
        sg.Button('Reset', key="clr4"),
        sg.In(key="qnty4", default_text=conf_dict["qnty4"] if "qnty4" in conf_dict else 0, size=(8, 1)),
        sg.Button('Long',key='-long4-', size=(8, 1)), sg.Button('Short',key='-short4-', size=(8, 1)),
        sg.Button('Cancel',key='-cancel4-', size=(8, 1)), sg.Button("Clear", key="-clearmulti-", size=(7, 1)), 
    ],

    #[sg.Button("Close Position", key="-close-"), sg.Button("Reverse Position", key="-reverse-"), sg.Button("Reset Values", key="reset"), sg.Button("Exit & Save", key="-exit-")],
    [sg.Multiline(size=(60, 5), key="multi", reroute_stdout = True,autoscroll=True ,reroute_stderr = False)],
    ]),
    sg.Column([

            #[sg.Text("Main Symbol: "+conf_dict["symbol"][:-4], key="symbol-value"),
            [sg.Button(c[:-4],size=(10, 1)) for c in currencies],
            [sg.Button(key=c, size=(10 ,1),) for c in currencies],
            [sg.Text("Rate of change "), sg.In(key="rate", default_text=conf_dict["rate"], size=(3,1)), sg.Radio("Sec","radio_rate", key="sec_rate", default=conf_dict["sec_rate"]),
            sg.Radio("Min","radio_rate", key="min_rate"), sg.Checkbox("Reverse Lock", size=(10, 1), key="-reverse-")],
            [sg.Button(key=d, size=(10 ,1),) for d in currenciess],
            
            [sg.Radio("Live Positions","radio_tracker", key="radio_live", default=True),
            sg.Radio("Long History","radio_tracker", key="radio_buy"),
            sg.Radio("Short History", "radio_tracker", key="radio_sell"),
            sg.Checkbox('Auto-scroll to End', default=True,key="autoscroll")],

            [sg.Text("Long"), sg.Text("",key="long_tot",size=(9,1)), sg.Button("Close", size=(7, 1)), sg.Text("Short"), 
              sg.Text("",key="short_tot",size=(9,1)), sg.Button("Close", size=(7, 1)), sg.Button("Clear", key="-tracker-", size=(7, 1)), sg.Button("Active", key="-clearmulti-", size=(7, 1)), 
    ],


            [sg.Table(values=data_values, headings=data_headings,
                            max_col_width=55,
                            auto_size_columns=False,                       
                            select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                            justification='left',
                            enable_events=True,
                            col_widths=[9,9,9,9,9,9,9,9],
                            visible_column_map=visible_column_map,
                            num_rows=13, key='_tracker_',
                            row_height=25,
                            font='Helvetica", 8')]
    ])
]#rows
]#layout


window = sg.Window('Window Title', layout,finalize=True)
table = window['_tracker_']
table.bind('<Button-1>', "Click")


def update_balance(window):
    while True:
        result_account = client.futures_account()
        update_dict = {"balance" : result_account["availableBalance"]}
        k = ["totalMaintMargin", "totalMarginBalance", "totalUnrealizedProfit"]
        for key in k:
            update_dict[key] = result_account[key]
        pos = client.futures_position_information()
        position_info = next(item for item in pos if item["symbol"] == conf_dict["symbol"])
        update_dict["liquidationPrice"] = position_info["liquidationPrice"]
        prices = client.futures_mark_price()
        for p in prices:
            if p["symbol"] in currencies:
                update_dict[p["symbol"]] = p["markPrice"]

        
        if values["radio_live"]:
            if len(df)>0:
                symbol_price = next(item for item in prices if item["symbol"] == conf_dict["symbol"])
                update_a = client.futures_account_trades()
                update_df = pd.DataFrame.from_dict(update_a)
                update_df = update_df.astype({"price": "float", "qty": "float", "commission": "float"})
                update_df = update_df.loc[update_df["symbol"].eq(conf_dict["symbol"]), :]
                update_df["Mark Price"] = float(symbol_price["markPrice"])
                update_df = update_df.merge(df, on ="orderId",suffixes=("","_r"), how='inner')
                if len(update_df) >0:
                    try:
                        dft = pd.read_csv("trades_history.csv", index_col=0)
                    except FileNotFoundError:
                        dft = pd.DataFrame()
                    dft = dft.append(update_df.drop("Mark Price", axis=1), ignore_index=True)
                    dft = dft.drop_duplicates(keep="last", subset=["orderId"])
                    dft.to_csv("trades_history.csv")
                    update_df["Trade"] = "Close"
                    total_amount = update_df.apply(lambda x:  x["qty"] if x["side"] =="BUY" else x["qty"]*-1, axis=1).sum()
                    update_df = update_df.append({
                        "symbol": conf_dict["symbol"],
                        "side": "BUY" if total_amount>0 else "SELL",
                        "qty": total_amount,
                        "price": update_df["price"].mean(),
                        "commission": update_df["commission"].sum(),
                        "Trade" : "Close All",
                        "Mark Price":  float(symbol_price["markPrice"]),
                    }, ignore_index=True)
                    update_df = update_df.iloc[::-1]

                    update_df["Exit Fee"] = (update_df["commission"] / (update_df["qty"] * update_df["price"])) * update_df["qty"] * update_df["Mark Price"]

                    update_df["PNL"] = (update_df["Mark Price"] * update_df["qty"]) - ((update_df["qty"] * update_df["price"]))  # + update_df["Fee"])
                    update_df["PNL"] = update_df.apply(lambda x: x["PNL"] * -1 if x["side"] == "SELL" else x["PNL"], axis=1)
                    update_df["PNL"] = update_df["PNL"] - update_df["commission"]
                    update_df["PNL"] = update_df["PNL"] - update_df["Exit Fee"]


                    update_df = update_df.loc[:, ["symbol", "side", "qty", "price", "commission", "Mark Price","Exit Fee", "PNL","Trade", "orderId"]]
                    update_dict["table"]=update_df

                else:
                    update_dict["table"] = pd.DataFrame(columns=["symbol", "side", "qty", "price", "commission", "Mark Price", "Exit Fee", "PNL", "Trade", "orderId"])
            else:
                update_dict["table"] = pd.DataFrame(columns=["symbol", "side", "qty", "price", "commission", "Mark Price", "Exit Fee", "PNL","Trade", "orderId"])
            update_dict["live"] = True
        elif values["radio_long"] or values["radio_short"]:

            update_df = pd.DataFrame(columns=["symbol", "side", "qty", "price", "commission", "Mark Price", "Exit Fee", "PNL", "Trade", "orderId"])

            try:
                dft = pd.read_csv("trades_history.csv", index_col=0)
            except FileNotFoundError:
                dft = pd.DataFrame()

            update_df = pd.concat([update_df, dft], ignore_index=True, axis=0)
            update_df = update_df.loc[update_df["side"].eq("BUY" if values["radio_long"] else "SELL"), :]
            update_dict["table"] = update_df.loc[:,["symbol", "side", "qty", "price", "commission", "Mark Price", "Exit Fee", "PNL", "Trade","orderId"]].fillna("/")
        window.write_event_value('-balance-', update_dict)
        interval = float(values["rate"])*60 if values["min_rate"] else float(values["rate"])
        time.sleep(interval)


event, values = window.read(timeout=0)

threadObj = threading.Thread(target=update_balance, args=(window,), daemon=True)
threadObj.start()

last_trade_dict = dict()

while True:
    event, values = window.read()
    if event == "-saveapi-":
        key_settings = {"APIKey": values["apikey"], "APISecret": values["apisecret"], "testnet": values["testnet"]}
        json.dump(key_settings, open("keys.conf", "wt"))
        client = Client(key_settings["APIKey"], key_settings["APISecret"], testnet=key_settings.pop("testnet"))
    if event == "API Settings":
        window["apiframe"].update(visible=True)
    if event == "-hideapi-":
        window["apiframe"].update(visible=False)
    if event == "Exit and Save":
        json.dump(values, open("conf.json","wt"))
        window.close()
        break
    if event == "-closeall-":
        position_info = client.futures_position_information()
        position_amt = float(next(x["positionAmt"] for x in position_info if x["symbol"] ==  conf_dict["symbol"]))
        params = {"symbol": conf_dict["symbol"], "side": "BUY" if position_amt < 0 else "SELL",
                  "type": "MARKET",
                  "quantity": abs(position_amt)}
        order = client.futures_create_order(**params)
        df.drop(df.index, inplace=True)
        df.to_csv("orders.csv")
        df = pd.DataFrame()
        window["_tracker_"].update(values=df.values.tolist())

    #if event in ["radio_live","radio_long", "radio_short"]:
     #   window["_tracker_"].update(values=df_trades.values.tolist())

    if event == "Exit" or event == sg.WIN_CLOSED:
        window.close()
        break
    all_keys_to_clear = ["qnty1", "qnty2", "qnty3", "qnty4", "callback_rate", "radio2", "activation_price", "TLS"]
    if event == "-cleartracker-":
        df = pd.DataFrame()
        window["_tracker_"].update(values=df.values.tolist())
    if event == "-clearmulti-":
        window["multi"].update("")
    if event == "_tracker_Click":
        e = table.user_bind_event
        region = table.Widget.identify('region', e.x, e.y)
        if region == 'heading':
            row = 0
        elif region == 'cell':
            row = int(table.Widget.identify_row(e.y))
        elif region == 'separator':
            continue
        else:
            continue
        column = int(table.Widget.identify_column(e.x)[1:])
        if column == 9:
            table_values = table.Get()
            position_amt = float(round(table_values[row-1][2],6))
            params = {"symbol": conf_dict["symbol"], "side": "BUY" if table_values[row-1][1]=="SELL" else "SELL", "type": "MARKET",
                      "quantity": abs(position_amt)}
            order = client.futures_create_order(**params)
            if row == 1:
                df.drop(df.index, inplace=True)
            else:
                df.drop(df.index[df["orderId"].eq(int(table_values[row-1][9]))], inplace=True)
            df.to_csv("orders.csv")
            print(f"ORDER {order['orderId']} executed")
    if event == "reset":
        for key in all_keys_to_clear:
            window[key]('')

    def reset_key(key):
        window[key]('')

    key_clear = {"clr1": "qnty1", "clr2": "qnty2", "clr3": "qnty3", "clr4": "qnty4"}
    if event in key_clear:
        key = key_clear[event]
        reset_key(key)
    if event =="-symbol-":
        if values["symbol"].upper()+"USDT" in all_symbols:
            symb= values["symbol"].upper()
            conf_dict["symbol"]=(symb+ "USDT")
            json.dump(values, open("conf.json", "wt"))
            window["symbol-value"].update(("Current Symbol: "+symb))
            print("Current Symbol: "+symb)
        else:
            window["symbol"].update(conf_dict["symbol"][:-4])
            print("Wrong input.")
    if event == "-close-":
        positions = client.futures_position_information(symbol=conf_dict["symbol"])
        position_amt = float(positions[0]["positionAmt"])
        if abs(position_amt) > 0:
            params = {"symbol": conf_dict["symbol"], "side": "SELL" if position_amt>0 else "BUY", "type": "MARKET","quantity":abs(position_amt)}
            order = client.futures_create_order(**params)
            order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
            df = df.append(order_df, ignore_index=True)
            df.to_csv("history"+str(time.time())+".csv")
            df = df[0:0]
            df.to_csv("orders.csv")
            print(f"ORDER {order['orderId']} executed")
        else:
            print("NO position Open")
    if event == "-reverse-":
        positions = client.futures_position_information(symbol=conf_dict["symbol"])
        if not values["Isolated"] and len(positions)>0 and positions[0]['marginType'] =="cross":
            positions = client.futures_position_information(symbol=conf_dict["symbol"])
            position_amt = float(positions[0]["positionAmt"])
            params = {"symbol": conf_dict["symbol"], "side": "SELL" if position_amt > 0 else "BUY", "type": "MARKET",
                      "quantity": position_amt*2}
            order = client.futures_create_order(**params)
            order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
            df = df.append(order_df, ignore_index=True)
            df.to_csv("history" + str(time.time()) + ".csv")
            df = df.iloc[-1,:]
            df.to_csv("orders.csv")
            print(f"ORDER {order['orderId']} executed")
        else:
            print("Reverse position only works in cross-mode with an existing open position")
    if event =="-balance-":
        for c in currencies:
            if c in values[event].keys():
                window[c].update(f"{float(values[event][c]):.3f}")
        updating=f'{float(values[event]["balance"]):.3f}'
        window['balance'].update(updating)
        updating=f'{float(values[event]["totalMarginBalance"]):.3f}'
        window['margin'].update(updating)
        updating = f'{float(values[event]["totalMaintMargin"]):.3f}'
        window["maintence"].update(updating)
        updating = f'{float(values[event]["totalUnrealizedProfit"]):.3f}'
        window["PNL"].update(updating)
        updating = f'{float(values[event]["liquidationPrice"]):.3f}'
        window["liquidationPrice"].update(updating)
        if "table" in values[event]:
            update_df = values[event]["table"]

            #tracker_side = "BUY" if values["radio_buy"] else "SELL"
            #update_df = update_df.loc[update_df["side"].eq(tracker_side),:]

            if "live" in values[event]:
                row_colors = ((idx,"green") if pnl > 0 else (idx, "red") for idx, pnl in enumerate(update_df.loc[:,"PNL"]))
            else:
                row_colors = ((idx,"blue") for idx in range(len(update_df)))

            #define colors based on sell

            window["_tracker_"].update(values=update_df.values.tolist(), row_colors=row_colors)

            #if values["autoscroll"]:
            #    table.Widget.yview_moveto(1)

    if event == "-tls-":
        positions = client.futures_position_information(symbol=conf_dict["symbol"])
        position_amt = float(positions[0]["positionAmt"])
        params = {"symbol": conf_dict["symbol"], "side": "SELL" if position_amt>0 else "BUY", "type": "TRAILING_STOP_MARKET","callbackRate":values["callback_rate"] ,"quantity":-position_amt}
        if len(values["activation_price"])>0:
            params["activationPrice"]=values["activation_price"]
        order = client.futures_create_order(**params)
        order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
        df = df.append(order_df, ignore_index=True)
        df.to_csv("orders.csv")
        print(f"ORDER {order['orderId']} executed")
    if event in ["-cancel1-", "-cancel2-", "-cancel3-","-cancel4-"]:
        entry_no = event[-2]
        if entry_no in last_trade_dict:
            try:
                params = {"symbol": conf_dict["symbol"], "side": "BUY" if last_trade_dict[entry_no][1]=="SELL" else "SELL", "type": "MARKET",
                          "quantity": last_trade_dict[entry_no][2]}
                order = client.futures_create_order(**params)
                print("Order canceled")
                if len(df)>0:
                    df.drop(df.index[df["orderId"].eq(last_trade_dict[entry_no][0])], inplace=True)
                last_trade_dict.pop(entry_no)
            except BinanceAPIException as e:
                print("Unexpected error:", e.message)
    if event in ["-long1-", "-long2-", "-long3-","-long4-","-short1-", "-short2-", "-short3-","-short4-"]:
        entry_no=event[-2]
        side = "BUY" if event[1:5]=="long" else "SELL"
        json.dump(values, open("conf.json", "wt"))
        try:
            client.futures_change_leverage(symbol=conf_dict["symbol"], leverage=values["leverage"])
            marginType = "ISOLATED" if values["Isolated"] else "CROSSED"
            client.futures_change_margin_type(symbol=conf_dict["symbol"], marginType=marginType)
        except BinanceAPIException as e:
            if e.code==-4046:
                pass
            else:
                print("Unexpected error:", e.message)
        try:
            params={"symbol":conf_dict["symbol"], "side":side, "type":"MARKET", "quantity":values["qnty"+entry_no],"reduceOnly":values["reduce"]}
            if not values["radio1"]:
                params["type"]= "STOP_MARKET" if values["radio2"] else "TAKE_PROFIT_MARKET"
                params["stopPrice"]=values["price"] if values["radio2"] else values["price_tp"]
            order = client.futures_create_order(**params)
            order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
            df = df.append(order_df, ignore_index=True)
            print(f"ORDER {order['orderId']} executed")
            last_trade_dict[entry_no] = [order['orderId'], params["side"], params["quantity"]]
            if values["TLS"]:
                params["type"]= "TRAILING_STOP_MARKET"
                params["type"]= "TRAILING_STOP_MARKET"
                params["side"] = "SELL" if side=="BUY" else "BUY"
                if len(values["activation_price"]) > 0:
                    params["activationPrice"] = values["activation_price"]
                elif values["radio2"]:
                    params["activationPrice"] = values["price"]
                params["callbackRate"] = values["callback_rate"]
                order = client.futures_create_order(**params)
                order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
                df = df.append(order_df, ignore_index=True)
                print(f"ORDER {order['orderId']} executed")
            df.to_csv("orders.csv")
        except BinanceAPIException as e:
            print("Unexpected error: ",e.message)



