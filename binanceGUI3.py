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


api_key="4qwMmtjwUaA85tiIAGl8ypfnxd4IKp89sOUO9Chpmkf8AwIc0ONgou6QoQISPtrH"
api_secret="9oFz2ym2f2B3KecOlcmhTaZMWWk9O3qTCZgRHtJiqgpisdEK5UyfV5H1B5AV3inM"

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
        'reduce': False,
        'symbol': "BTCUSDT",
        'qnty1': 2,
        'radio_stop_market': True,
        'radio_take_profit': False,
        'price': '',
        'radio_tls': False,
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
    dft = pd.read_csv("trades_history.csv", index_col=0)
except FileNotFoundError:
    dft = pd.DataFrame()


data_values = []
data_headings = ['Symbol', 'Side', 'Amount', 'Entry Price', "Fee", "Mark Price","Exit Fee", "PNL", "Trade", "orderId"]
visible_column_map = [True, True, True, True, True, True, True, True, True, False]

currencies = ['BTCUSDT','ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT', 'DOTUSDT', 'UNIUSDT', 'BCHUSDT']
info = client.futures_exchange_info()

#different currencies have different level of precision as in number behind the decimal point
currency_precision = {}
for c in currencies:
    currency_precision[c] = next(s["quantityPrecision"] for s in info["symbols"] if s["symbol"] == c)


menu_def = [['&File', ['&API Settings',"&Exit and Save"]],
 ]

RADIO1_keys = {
    'radio_market': "MARKET",
    'radio_stop_market': "STOP_MARKET",
    'radio_take_profit': "TAKE_PROFIT_MARKET",
    "radio_tls": "TRAILING_STOP_MARKET"
}

RADIO2= ["amount_value", "percentage_value", "price_value"]


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
    [sg.Text("BALANCE:"), sg.Text("",key="balance",size=(15,1))],
    [sg.Text("Margin Balance:"), sg.Text("",key="margin",size=(15,1))],
    [sg.Text("Maintence Margin:"), sg.Text("",key="maintence",size=(15,1))],
    [sg.Text("Unrealized PNL Margin:"), sg.Text("",key="PNL",size=(15,1))],
    [sg.Text("Liquidation Price:"), sg.Text("", key="liquidationPrice", size=(15, 1))],
    [sg.Text("Unrealized Commisson:"), sg.Text("",key="commission",size=(15,1))],
    [sg.Text("Current Symbol: "+conf_dict["symbol"][:-4], key="symbol-value", size=(25,1))],
    [sg.Text("Choose Symbol: "),sg.In(default_text=conf_dict["symbol"][:-4], key="symbol", size=(10,1)), sg.Button("Change",key="-symbol-")],
    [sg.Text('Margin-type: '), sg.Radio('Crossed', 'margin', default=(not conf_dict["Isolated"]), size=(7, 1)),
     sg.Radio('Isolated', 'margin', key="Isolated", default=conf_dict["Isolated"], size=(7, 1)),
     sg.Text('Leverage: ', size=(7, 1)),
     sg.Spin(values=[i for i in range(1, 126)], key="leverage", initial_value=conf_dict["leverage"], size=(6, 1))],

    #[sg.Text('Leverage: ', size=(15, 1)), sg.Spin(values=[i for i in range(1, 126)], key="leverage",initial_value=conf_dict["leverage"], size=(6, 1))],
    #[sg.Text('Margin-type: '),sg.Radio('Isolated', 'margin',key="Isolated", default=conf_dict["Isolated"], size=(12, 1)), sg.Radio('Crossed', 'margin', default=(not conf_dict["Isolated"]), size=(12, 1))],
    [sg.Text("Reduce-only"), sg.Checkbox("",size=(20, 1), default=conf_dict["reduce"],key="reduce")],
    [
        sg.Radio('Market', "RADIO1", default=False, disabled=False, size=(10,1),key="radio_market"), 
        sg.Checkbox("Market Lock",  default=False, key="market_lock", enable_events=True)
    ],
    [
        sg.Radio('Amount ', "RADIO2", default=True, key="amount_value"), 
        sg.Radio('Percentage ', "RADIO2", key="percentage_value"), 
        sg.Radio('Price ', "RADIO2", key="price_value")
    ],
    [sg.Checkbox("+/-", default=True, key="check_sign")],
    [
        sg.Radio('Stop Market', "RADIO1",key="radio_stop_market", default= True if (conf_dict["radio_stop_market"]+conf_dict["radio_take_profit"]+conf_dict["radio_tls"])==0 else conf_dict["radio_stop_market"], size=(14,1)),
        sg.In(key="ap_stop_market", size=(15, 1)),
        sg.Text("Rate %"),
        sg.Spin(values=[i/10 for i in range(1,51)], key="percentage_stop_market",initial_value=1, size=(4, 1))
    ],
    [
        sg.Radio('Take Profit', "RADIO1", key="radio_take_profit", default=conf_dict["radio_take_profit"], size=(14,1)),
        sg.In(key="ap_take_profit", size=(15, 1)),
        sg.Text("Rate %"),
        sg.Spin(values=[i/10 for i in range(1,51)], key="percentage_take_profit",initial_value=1, size=(4, 1))
    ],
    [
        sg.Radio('Trailling Stop Loss', "RADIO1", default=conf_dict["radio_tls"], key="radio_tls",size=(14,1)),
        sg.In(key="ap_tls", size=(15, 1)),
        sg.Text("Rate %"),
        sg.Spin(values=[i/10 for i in range(1,51)], key="percentage_tls",initial_value=1, size=(4, 1)), sg.Text("Callback rate:") , sg.Spin(values=[i/10 for i in range(1,51)], key="callback_rate",initial_value=conf_dict["callback_rate"], size=(6, 1))
    ],
    [
        sg.Text('Quantity', size=(7, 1)), sg.Button('Reset', key="clr1"),
        sg.In(key="qnty1", default_text=conf_dict["qnty1"] if "qnty1" in conf_dict else 0, size=(8, 1)),
        sg.Button('Long',key='-long1-', size=(8, 1)), sg.Button('Short',key='-short1-', size=(8, 1)),
        sg.Button('Cancel',key='-cancel1-', size=(8, 1))
    ],
    [
        sg.Text('Quantity', size=(7, 1)), sg.Button('Reset', key="clr2"),
        sg.In(key="qnty2", default_text=conf_dict["qnty2"] if "qnty2" in conf_dict else 0, size=(8, 1)),
        sg.Button('Long',key='-long2-', size=(8, 1)), sg.Button('Short',key='-short2-', size=(8, 1)),
        sg.Button('Cancel',key='-cancel2-', size=(8, 1))
    ],
    [
        sg.Text('Quantity', size=(7, 1)), sg.Button('Reset', key="clr3"),
        sg.In(key="qnty3", default_text=conf_dict["qnty3"] if "qnty3" in conf_dict else 0, size=(8, 1)),
        sg.Button('Long',key='-long3-', size=(8, 1)), sg.Button('Short',key='-short3-', size=(8, 1)),
        sg.Button('Cancel',key='-cancel3-', size=(8, 1))
    ],
    [
        sg.Text('Quantity', size=(7, 1)), sg.Button('Reset', key="clr4"),
        sg.In(key="qnty4", default_text=conf_dict["qnty4"] if "qnty4" in conf_dict else 0, size=(8, 1)),
        sg.Button('Long',key='-long4-', size=(8, 1)), sg.Button('Short',key='-short4-', size=(8, 1)),
        sg.Button('Cancel',key='-cancel4-', size=(8, 1))
    ],
    #[sg.Button("Close Position", key="-close-"), sg.Button("Reverse Position", key="-reverse-"), sg.Button("Reset Values", key="reset"), sg.Button("Exit & Save", key="-exit-")],
    [sg.Multiline(size=(65, 6), key="multi", reroute_stdout = True,autoscroll=True ,reroute_stderr = False)],
    ]),
    sg.Column([

            [
                sg.Text("Rate of Change:"), 
                sg.In(key="rate", default_text=conf_dict["rate"], size=(3,1)), 
                sg.Radio("Sec","radio_rate", key="sec_rate", default=conf_dict["sec_rate"]),
                sg.Radio("Min","radio_rate", key="min_rate"), 
                sg.Button("Clear live-tracker", key="-cleartracker-"), 
                sg.Button("Clear Multi-line", key="-clearmulti-"), 
                sg.Button("Exit Positions",key="-closeall-")
            ],
            [sg.Button(key=c, size=(7,1),) for c in currencies],
            [sg.Button(c[:-4],size=(7, 1), key ="-"+c+"-") for c in currencies],
            #[sg.Checkbox('Auto-scroll to end: ', default=True,key="autoscroll")],
            [
                sg.Radio("Live Tracker","radio_tracker", key="radio_live", default=True, enable_events=True),
                sg.Radio("Long History", "radio_tracker", key="radio_long", enable_events=True),
                sg.Radio("Short History", "radio_tracker", key="radio_short"),
                sg.Checkbox("Symbol Lock", key="symbol_lock"),
                sg.Checkbox("Reverse Lock", key="reverse_lock")
            ],
            [
                sg.Text("Long Total"), 
                sg.Text("",key="long_total", background_color="blue", size=(8,1)),
                sg.Button("Close", size=(7, 1), key="-close_long-"),
                sg.Text("Short Total"),sg.Text("",key="short_total",size=(8,1), background_color="blue",),
                sg.Button("Close", size=(7, 1), key="-close_short-")
            ],
            [sg.Table(values=data_values, headings=data_headings,
                            max_col_width=65,
                            auto_size_columns=False,
                            select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                            justification='left',
                            enable_events=True,
                            col_widths=[9, 4, 6,10,10,8,8,10],
                            visible_column_map=visible_column_map,
                            num_rows=27, key='_tracker_')]
    ])
]#rows
]#layout

prices = {}
window = sg.Window('Window Title', layout, finalize=True)
table = window['_tracker_']
table.bind('<Button-1>', "Click")

table_widget = window['_tracker_'].Widget

anchors = ["w", "w", "e", "e", "e", "e", "e", "e", "center"]
for cid, anchor in enumerate(anchors):
    table_widget.column(cid, anchor=anchor)


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
        global prices
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
                    update_df["commission"] = update_df.groupby(by="orderId")["commission"].cumsum()
                    update_df["price"] = update_df.groupby(by="orderId")["price"].transform(lambda x: x.mean())
                    update_df["qty"] = update_df.groupby(by="orderId")["qty"].transform(lambda x: x.sum())

                    update_df = update_df.drop_duplicates(keep="last", subset="orderId")
                    global dft
                    dft = dft.append(update_df.drop("Mark Price", axis=1), ignore_index=True)
                    dft = dft.drop_duplicates(keep="last", subset=["orderId", "qty"])
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
                    update_dict["long_total"] = update_df.iloc[1:,:].loc[update_df["side"].eq("BUY"),"PNL"].sum(min_count=1)
                    update_dict["short_total"] = update_df.iloc[1:,:].loc[update_df["side"].eq("SELL"),"PNL"].sum(min_count=1)

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
    #if event == "-debug-":
    #    print(conf_dict["symbol"])
    if event in ["-"+c+"-" for c in currencies] and not values["symbol_lock"]:
        new_currency = event[1:-1]
        position_info = client.futures_position_information()
        symbol_position = float(next(p["positionAmt"] for p in position_info if p["symbol"] == conf_dict["symbol"]))

        params = {}
        params["side"] = "BUY"  if symbol_position<0 else "SELL"
        params["quantity"] = round(abs(symbol_position), 3)
        params["symbol"] = conf_dict["symbol"]
        params["type"] = "MARKET"
        df.drop(df.index, inplace=True)
        if params["quantity"] != 0:
            #we make the opposite trade
            order = client.futures_create_order(**params)
            while True:
                try:
                    order_info = client.futures_get_order(symbol=params["symbol"], orderId=order["orderId"])
                    #we iterate throught the loop until the status is FILLED, meaning the trade was executed.
                    if order_info["status"] == "FILLED":
                        break
                except BinanceAPIException as e:
                    print(e.message)
                time.sleep(0.1)

            trades = client.futures_account_trades()
            trades_df = pd.DataFrame.from_dict(trades)
            trades_df = trades_df.astype({"commission": float, "quoteQty": float})
            commission, val = trades_df.loc[trades_df["orderId"].eq(order_info["orderId"]) ,["commission", "quoteQty"]].sum()
            usdt_amount = abs(val) - commission

            new_price = float(next(p["markPrice"] for p in prices if p["symbol"] == new_currency))

            params["side"] = params["side"] if values["reverse_lock"] else "BUY" if params["side"] =="SELL" else "SELL"
            params["quantity"] = round((usdt_amount/new_price), currency_precision[new_currency])
            params["symbol"] = new_currency
            order = client.futures_create_order(**params)
            order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
            df = df.append(order_df, ignore_index=True)

        conf_dict["symbol"] = new_currency
        window["symbol"].update(new_currency[:-4])
        window["symbol-value"].update(("Current Symbol: " + new_currency[:-4]))
        json.dump(values, open("conf.json", "wt"))

        df.to_csv("orders.csv")
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
        df.to_csv("orders.csv")
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
    if event in ["-close_short-", "-close_long-"]:
        side = "BUY" if event == "-close_long-" else "SELL"
        amount = df.loc[df["side"].eq(side), "origQty"].sum()
        df.drop(df.index[df["side"].eq(side)], inplace=True)
        df.to_csv("orders.csv")
        params = {
            "symbol": conf_dict["symbol"], "side": "BUY" if side == "SELL" else "SELL",
            "type": "MARKET",
            "quantity":  float(round(amount, 4))
        }
        order = client.futures_create_order(**params)
        print("Closing order Executed:", order["orderId"])
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
    if event == "-balance-":
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

        if all([v in values[event] for v in ["long_total", "short_total"]]):
            updating = f'{float(values[event]["long_total"]):.3f}' if not pd.isna(values[event]["long_total"]) else "/"
            window["long_total"].update(updating)
            long_color = ("green" if float(updating)>0 else "red") if updating != "/" else "blue"
            window["long_total"].update(background_color=long_color)

            updating = f'{float(values[event]["short_total"]):.3f}' if not pd.isna(values[event]["short_total"]) else "/"
            window["short_total"].update(updating)
            short_color = ("green" if float(updating) >= 0 else "red") if updating != "/" else "blue"
            window["short_total"].update(background_color=short_color)
        else:
            window["long_total"].update("/")
            window["long_total"].update(background_color="blue")

            window["short_total"].update("/")
            window["short_total"].update(background_color="blue")

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
    if event == "market_lock":
        if values["market_lock"]:
            window["radio_market"].update(False)
            window["radio_market"].update(disabled=True)
        else:
            window["radio_market"].update(disabled=False)
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
        entry_no = event[-2]
        side = "BUY" if event[1:5] == "long" else "SELL"
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
        params = {
            "symbol": conf_dict["symbol"],
            "side": side,
            "quantity": values["qnty" + entry_no],
            "reduceOnly": values["reduce"]
        }

        # we get the selected radio button
        key, order_type = next((k, v) for k, v in RADIO1_keys.items() if values[k])
        key = "_".join(key.split("_")[1:])

        if not values["market_lock"] and order_type =="MARKET":
            params["type"] = order_type
            order = client.futures_create_order(**params)
            order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
            df = df.append(order_df, ignore_index=True)
            print(f"ORDER {order['orderId']} executed")
            last_trade_dict[entry_no] = [order['orderId'], params["side"], params["quantity"]]
        else:
            if values["market_lock"]:
                params["type"]="MARKET"
                order = client.futures_create_order(**params)
                order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
                df = df.append(order_df, ignore_index=True)
                print(f"ORDER {order['orderId']} executed")
                last_trade_dict[entry_no] = [order['orderId'], params["side"], params["quantity"]]
            params["type"] = order_type
            if order_type == "TRAILING_STOP_MARKET":
                if values["market_lock"]:
                    params["side"] = "BUY" if params["side"] == "SELL" else "SELL"
                params["callbackRate"] = float(values["callback_rate"])
            else:
                if key == "stop_market":
                    params["side"] = "BUY" if values["check_sign"] else "SELL"
                elif key == "take_profit":
                    params["side"] = "SELL" if values["check_sign"] else "BUY"
            activation_type = next(k for k in RADIO2 if values[k])
            mark_price = float(next(p["markPrice"] for p in prices if p["symbol"] == conf_dict["symbol"]))
            if activation_type == "price_value":
                if values["ap_"+ key]:
                    #the keys our value boxes have the same ending, but different prefix.
                    params["stopPrice"] = values["ap_" + key]
            elif activation_type == "amount_value":
                if values["ap_" + key]:
                    amount = float(values["ap_" + key])
                    add = amount if values["check_sign"] else -amount
                    params["stopPrice"] = round(amount + mark_price, 4)
            elif activation_type == "percentage_value":
                add = (float(values["percentage_" + key])/100) * mark_price
                add = add if values["check_sign"] else -add
                params["stopPrice"] = round((mark_price + add), 2)
            if order_type == "TRAILING_STOP_MARKET" and "stopPrice" in params:
                params["activationPrice"] = params["stopPrice"]
                params.pop("stopPrice")
            try:
                order = client.futures_create_order(**params)
                print(f"{order_type} ORDER {order['orderId']} executed")
            except BinanceAPIException as e:
                print(e.message)
        df.to_csv("orders.csv")


