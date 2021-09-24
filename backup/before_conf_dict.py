from tkinter import font
import PySimpleGUI as sg
import threading
from PySimpleGUI.PySimpleGUI import ReadButton
from binance import Client
from binance.exceptions import BinanceAPIException
import json
import sys
import time
from numpy import positive
import pandas as pd
import win32api
import ctypes, sys


class Main_window():
    
    def __init__(self, _client, _conf_filename = "conf.json", _order_filename = "orders.csv", _trades_history_filename = "trades_history.csv"):
        self.client = _client                                                   # Get the current client instance

        # Initialize the variable
        # self.currencies = ['BTCUSDT','ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT', 'DOTUSDT', 'UNIUSDT', 'BCHUSDT']
        self.currencies = ['ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT', 'DOTUSDT', 'UNIUSDT',]
        self.RADIO2= ["amount_value", "percentage_value", "price_value"]
        
        # Load needed files
        self.conf_dict = self.load_conf_dict(_conf_filename)                    # Load conf.json file
        self.df = self.load_order_file(_order_filename)                         # Load orders.csv file
        self.history_filename = _trades_history_filename
        self.dft = self.load_history(self.history_filename)                     # Load trades_history.csv file

    def load_order_file(self, order_filename):                                  # Load order file content
        try:
            df = pd.read_csv(order_filename, index_col=0)                       # df = pd.read_csv("orders.csv", index_col=0)
        except FileNotFoundError:
            df = pd.DataFrame()
        finally:
            return df

    def load_conf_dict(self, conf_filename):                                    # Load conf file content
        try:
            conf_dict= json.load(open(conf_filename))                           # conf_dict= json.load(open("conf.json"))
            conf_dict["symbol"]=conf_dict["symbol"].upper()+"USDT"
        except:
            conf_dict={
                'APIKey': '',                              # 'APIKey': '',
                'APISecret': '',                           # 'APISecret': '',
                'leverage': 20,                            # 'leverage': 20,
                'Isolated': False,                         # 'Isolated': False,
                'reduce': True,                            # 'reduce': False,
                'symbol': "BTCUSDT",                       # 'symbol': "BTCUSDT",
                'qnty1': 2,                                # 'qnty1': 2,
                'radio_stop_market': True,                 # 'radio_stop_market': True,
                'radio_take_profit': False,                # 'radio_take_profit': False,
                'price': '',                               # 'price': 'No_price',
                'radio_tls': False,                        # 'radio_tls': False,
                'price_tp': '',                            # 'price_tp': '',
                'TLS': False,                              # 'TLS': False,
                'activation_price': '',                    # 'activation_price': '',
                'callback_rate': 0.8,                      # 'callback_rate': 0.8,
                'sec_rate' : True,                         # 'sec_rate' : True,
                'rate' : 1,                                # 'rate' : 1,
                }
        finally:
            return conf_dict

    def get_layout(self):
        # ###############################################
        #   Initialize the layout for main window
        # -----------------------------------------------

        data_values = []
        data_headings = ['Symbol', 'Side', 'Amount', 'Entry Price', "Fee", "Mark Price","Exit Fee", "PNL", "Trade", "orderId"]
        visible_column_map = [True, True, True, True, True, True, True, True, True, False]

        menu_def = [['&File', ['&API Settings',"&Exit and Save"]],
        ]

        layout = [
            [sg.Menu(menu_def)],
            [
                sg.pin(sg.Frame("API settings",
                    [
                        [sg.Text("API key", size=(10,1)),sg.Input(size=(70,1), key="apikey")],
                        [sg.Text("API Secret", size=(10,1)),sg.Input(size=(70,1), key="apisecret")],
                        [sg.Checkbox("Testnet", key="testnet")],
                        [sg.Button("Save keys",key="-saveapi-"), sg.Button("Hide Frame", key="-hideapi-")]
                    ],visible=False, key="apiframe"
                    ), shrink=True
                )
            ],
            [
                sg.Column([
                    [
                        sg.Text("BALANCE:", size =(14, 1)), 
                        sg.Text("", key="balance", size=(10, 1)), 
                        sg.Text("Liquidation Price:", size =(14, 1)), 
                        sg.Text("", key="liquidationPrice", size=(10, 1))
                    ],
                    [
                        sg.Text("Margin Balance:", size =(14, 1)), 
                        sg.Text("", key="margin", size=(10, 1)), 
                        sg.Text("Maintence Margin:", size =(14, 1)), 
                        sg.Text("", key="maintence", size=(10, 1))
                    ],
                    [
                        sg.Text("Unrealized PNL:", size =(14, 1)), 
                        sg.Text("", key="PNL", size=(10, 1))
                    ], 
                    [sg.Text("")], 
                    [
                        sg.Text("Symbol: ", size =(9, 1)),
                        sg.In(default_text=self.conf_dict["symbol"][:-4], size=(11, 1), key="symbol"), 
                        sg.Checkbox('Symbol Lock', default=False, key="symbol_lock", size =(12, 1)), 
                        sg.Button("Change", key="-symbol-", size =(10, 1))
                    ],
                    
                    [
                        sg.Radio('Crossed', 'margin', default=(not self.conf_dict["Isolated"]), size=(10, 1)),
                        sg.Radio('Isolated', 'margin', key="Isolated", default=self.conf_dict["Isolated"], size=(10, 1))
                    ],
                    [
                        sg.Radio('Amount ', "RADIO2", size=(10, 1), default=True, key="amount_value"), 
                        sg.Radio('Exact Price ', "RADIO2", size=(10, 1), key="price_value"), 
                        sg.Radio('Percentage ', "RADIO2", key="percentage_value")
                    ], 
                    
                    [
                        sg.Radio('Market', "RADIO1", default=self.conf_dict["radio_stop_market"], size=(10,1), key="radio_market"), 
                        sg.Checkbox('Market Lock', default=False, key="market_lock", enable_events=True)
                    ],
                    [
                        sg.Radio('Stop Market', "RADIO1",key="radio1", default=self.conf_dict["radio_stop_market"], size=(10,1)), 
                        sg.Radio('Take Profit', "RADIO1", key="radio2", default=self.conf_dict["radio_take_profit"], size=(10, 1)),
                        sg.Radio('Trailing Stop Loss', "RADIO1",key="radio3", default=self.conf_dict["radio_tls"], size=(14,1))
                    ],
                    [sg.Text("")], 
                    [
                        sg.Text("Reduce-only", size =(9, 1)), 
                        sg.Checkbox("", size=(1, 1), default=self.conf_dict["reduce"], key="reduce"), 
                        sg.Text('   Leverage: ', size =(10, 1)), 
                        sg.Spin(values=[i for i in range(1, 126)], key="leverage", initial_value=self.conf_dict["leverage"], size=(5, 1))
                    ],
                    [
                        sg.Button('Long',key='-???-', size=(8, 1)), ##sg.Button('Short',key='-short2-', size=(8, 1)), 
                        sg.Text("            "),
                        sg.Text("Percentage", size =(9, 1)) , 
                        sg.Spin(values=[i/10 for i in range(1,51)], key="percentage_tls",initial_value=self.conf_dict["callback_rate"], size=(5, 1)),
                        sg.Text("Callback") , 
                        sg.Spin(values=[i/10 for i in range(1,51)], key="callback_rate",initial_value=self.conf_dict["callback_rate"], size=(5, 1))
                    ],
                    [sg.Text("")], 
                    [
                        sg.Button('Reset', key="clr1"),
                        sg.In(key="qnty1", default_text=self.conf_dict["qnty1"] if "qnty1" in self.conf_dict else 0, size=(8, 1)),
                        sg.Button('Long',key='-long1-', size=(8, 1)), 
                        sg.Button('Short',key='-short1-', size=(8, 1)),
                        sg.Button('Cancel',key='-cancel1-', size=(8, 1))
                    ],
                    [
                        sg.Button('Reset', key="clr2"),
                        sg.In(key="qnty2", default_text=self.conf_dict["qnty2"] if "qnty2" in self.conf_dict else 0, size=(8, 1)),
                        sg.Button('Long',key='-long2-', size=(8, 1)), 
                        sg.Button('Short',key='-short2-', size=(8, 1)),
                        sg.Button('Cancel',key='-cancel2-', size=(8, 1))
                    ],
                    [
                        sg.Button('Reset', key="clr3"),
                        sg.In(key="qnty3", default_text=self.conf_dict["qnty3"] if "qnty3" in self.conf_dict else 0, size=(8, 1)),
                        sg.Button('Long',key='-long3-', size=(8, 1)), 
                        sg.Button('Short',key='-short3-', size=(8, 1)),
                        sg.Button('Cancel',key='-cancel3-', size=(8, 1)), 
                    ],
                    [
                        sg.Button('Reset', key="clr4"),
                        sg.In(key="qnty4", default_text=self.conf_dict["qnty4"] if "qnty4" in self.conf_dict else 0, size=(8, 1)),
                        sg.Button('Long',key='-long4-', size=(8, 1)), 
                        sg.Button('Short',key='-short4-', size=(8, 1)),
                        sg.Button('Cancel',key='-cancel4-', size=(8, 1)), 
                    ],
                    [
                        sg.Button('Reset', key="clr5"),
                        sg.In(key="qnty5", default_text=self.conf_dict["qnty5"] if "qnty5" in self.conf_dict else 0, size=(8, 1)),
                        sg.Button('Long',key='-long5-', size=(8, 1)), 
                        sg.Button('Short',key='-short5-', size=(8, 1)),
                        sg.Button('Cancel',key='-cancel5-', size=(8, 1)), 
                    ],
                    [sg.Multiline(size=(60, 5), key="multi", reroute_stdout = True,autoscroll=True ,reroute_stderr = False)],
                    [
                        sg.Button("Clear", key="-clearmulti-", size=(7, 1)), 
                    ],
                    
                ]),
                    
                sg.Column([
                        [sg.Button(c[:-4], size=(10, 1)) for c in self.currencies],
                        [sg.Button(key=c, size=(10 ,1),) for c in self.currencies],
                        [
                            sg.Text("Rate of change "), 
                            sg.In(key="rate", default_text=self.conf_dict["rate"], size=(3,1)), 
                            sg.Radio("Sec","radio_rate", key="sec_rate", default=self.conf_dict["sec_rate"]),
                            sg.Radio("Min","radio_rate", key="min_rate"), 
                            sg.Checkbox("Reverse Lock", size=(10, 1), key="-reverse-", enable_events=True)
                        ],
                        [sg.Button(key=d, size=(10 ,1),) for d in self.currencies],
                        [
                            sg.Radio("Live Positions","radio_tracker", key="radio_live", default=True),
                            sg.Radio("Long History","radio_tracker", key="radio_buy"),
                            sg.Radio("Short History", "radio_tracker", key="radio_sell"),
                            sg.Checkbox('Auto-scroll to End', default=True,key="autoscroll")
                        ],
                        [
                            sg.Text("Long"), 
                            sg.In("", key="long_total", size=(9,1), readonly=True), 
                            sg.Button("Close", size=(7, 1), key="-closeLong-"), 
                            sg.Text("Short"), 
                            sg.In("", key="short_total", size=(9,1), readonly=True), 
                            sg.Button("Close", size=(7, 1), key="-closeShort-"), 
                            sg.Button("Clear", key="-cleartracker-", size=(7, 1)), 
                            sg.Button("Active", key="-active-", size=(7, 1)), 
                        ],
                        [sg.Text("")], 
                        [sg.Table(values=data_values, headings=data_headings,
                                        max_col_width=55,
                                        auto_size_columns=False,                       
                                        select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                                        justification='left',
                                        enable_events=True,
                                        col_widths=[10,10,10,10,10,10, 10],
                                        visible_column_map=visible_column_map,
                                        num_rows=15, key='_tracker_',
                                        row_height=28,
                                        font='Helvetica", 8')
                        ]
                ])
            ] # rows
        ] # layout
        return layout
  
    def load_history(self, trades_history_filename):
        try:
            dft = pd.read_csv(trades_history_filename, index_col=0)             # Load trades history file content
        except FileNotFoundError:
            dft = pd.DataFrame()
        finally:
            return dft

    def init_Window(self):
        sg.theme_background_color("#323233")                                                    # Set background color
        sg.theme_button_color(("#e1e1e1", '#1e1e1e'))                                           # Set button color
        sg.theme_element_background_color("#323233")        
        sg.theme_text_element_background_color("#323233")
        sg.theme_text_color("#d6d6d6")
        window = sg.Window('Main Window', self.get_layout(), finalize=True, font="Arial, 11")   # Initilalize the main window
        table = window['_tracker_']                                                             # Define window table
        table.bind('<Button-1>', "Click")                                                       # and apply button property
        table_widget = window['_tracker_'].Widget
        anchors = ["w", "w", "e", "e", "e", "e", "e", "e", "center"]
        for cid, anchor in enumerate(anchors):
            table_widget.column(cid, anchor=anchor)
        return window
    
    def main_logic(self):
        # ###############################################
        #   Initialize the variables for main logic
        # -----------------------------------------------
        # Create Main window and initialize the variables
        window = self.init_Window()
        last_trade_dict = dict()
        all_keys_to_clear = ["qnty1", "qnty2", "qnty3", "qnty4", "callback_rate", "radio2", "activation_price", "TLS"]
        key_clear = {"clr1": "qnty1", "clr2": "qnty2", "clr3": "qnty3", "clr4": "qnty4", "clr5": "qnty5"}
        currency_precision = {}
        RADIO1_keys = {
            'radio_market': "MARKET",
            'radio_stop_market': "STOP_MARKET",
            'radio_take_profit': "TAKE_PROFIT_MARKET",
            "radio_tls": "TRAILING_STOP_MARKET"
        }

        # ######################################################
        # Read Mark Price and Funding Rate and
        # read window event and values for Thread
        prices = self.client.futures_mark_price()
        event, values = window.read(timeout=0)

        # ######################################################
        # Get the Current exchange trading rules
        #  and symbol information
        all_symbols_return = self.client.futures_exchange_info()
        all_symbols = [s["symbol"] for s in all_symbols_return["symbols"] if s["symbol"][-4:]=="USDT"]

        # ######################################################
        # Get the precision of current currency
        # different self.currencies have different level of precision
        # as in number behind the decimal point
        for c in self.currencies:
            currency_precision[c] = next(s["quantityPrecision"] for s in all_symbols_return["symbols"] if s["symbol"] == c)

        
        # ######################################################
        #   Define Threading, reset key method
        # ------------------------------------------------------
        def update_balance(window):
            while True:
                # ###############################
                # Get the current account info and 
                # update dict with it's value
                result_account = self.client.futures_account()
                update_dict = {"balance" : result_account["availableBalance"]}
                k = ["totalMaintMargin", "totalMarginBalance", "totalUnrealizedProfit"]
                for key in k:
                    update_dict[key] = result_account[key]

                # ################################
                # Get the position info and
                # pick the info with current symbol, e.g. "currency" : XRPUDST
                # and update dict with position and currency info
                pos = self.client.futures_position_information()
                position_info = next(item for item in pos if item["symbol"] == self.conf_dict["symbol"])
                update_dict["liquidationPrice"] = position_info["liquidationPrice"]
                global prices
                prices = self.client.futures_mark_price()
                for p in prices:
                    if p["symbol"] in self.currencies:
                        update_dict[p["symbol"]] = p["markPrice"]
                
                # ######################################
                # If the user select Live Tracker radio,
                if values["radio_live"]:
                    # #############################
                    # If the order file dict exists
                    if len(self.df)>0:
                        # ################################################
                        # Get the current currency and my trade and
                        # and Filter with current currency 
                        # update my trade's "Mark Price" => current value
                        symbol_price = next(item for item in prices if item["symbol"] == self.conf_dict["symbol"])
                        update_a = self.client.futures_account_trades()
                        update_df = pd.DataFrame.from_dict(update_a)
                        update_df = update_df.astype({"price": "float", "qty": "float", "commission": "float"})
                        update_df = update_df.loc[update_df["symbol"].eq(self.conf_dict["symbol"]), :]
                        update_df["Mark Price"] = float(symbol_price["markPrice"])
                        update_df = update_df.merge(self.df, on ="orderId", suffixes=("", "_r"), how='inner')

                        # ########################
                        # If success
                        if len(update_df) >0:
                            # #####################################
                            # Calculate each colum's sum, mean ...
                            # and update "commission", "price", "qty"
                            # and delete duplicated rows
                            update_df["commission"] = update_df.groupby(by="orderId")["commission"].cumsum()
                            update_df["price"] = update_df.groupby(by="orderId")["price"].transform(lambda x: x.mean())
                            update_df["qty"] = update_df.groupby(by="orderId")["qty"].transform(lambda x: x.sum())
                            update_df = update_df.drop_duplicates(keep="last", subset="orderId")

                            # Save history dataFrame
                            self.dft = self.dft.append(update_df.drop("Mark Price", axis=1), ignore_index=True)
                            self.dft = self.dft.drop_duplicates(keep="last", subset=["orderId", "qty"])
                            self.dft.to_csv("trades_history.csv")

                            # ################################################
                            # add "Trade" key item and calculate total sum
                            # of the "qty" column 
                            # and append update_df dict with new values
                            update_df["Trade"] = "Close"
                            total_amount = update_df.apply(lambda x:  x["qty"] if x["side"] =="BUY" else x["qty"] * - 1, axis=1).sum()
                            update_df = update_df.append({
                                "symbol": self.conf_dict["symbol"],
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
                            
                            # ######################################
                            # Finally, make update_dict["table"] item
                            update_dict["table"]=update_df

                        # ##################################
                        # If there is no dataFrame
                        # empty table value
                        else:
                            update_dict["table"] = pd.DataFrame(columns=["symbol", "side", "qty", "price", "commission", "Mark Price", "Exit Fee", "PNL", "Trade", "orderId"])
                    
                    # #############################
                    # If the order file doesn't exists
                    else:
                        update_dict["table"] = pd.DataFrame(columns=["symbol", "side", "qty", "price", "commission", "Mark Price", "Exit Fee", "PNL","Trade", "orderId"])
                    update_dict["live"] = True


                # ######################################
                # If the user select Long History || Short,
                elif values["radio_long"] or values["radio_short"]:
                    update_df = pd.DataFrame(columns=["symbol", "side", "qty", "price", "commission", "Mark Price", "Exit Fee", "PNL", "Trade", "orderId"])
                    
                    # Load history file
                    self.dft = self.load_history(self.history_filename)

                    update_df = pd.concat([update_df, self.dft], ignore_index=True, axis=0)
                    update_df = update_df.loc[update_df["side"].eq("BUY" if values["radio_long"] else "SELL"), :]
                    update_dict["table"] = update_df.loc[:,["symbol", "side", "qty", "price", "commission", "Mark Price", "Exit Fee", "PNL", "Trade","orderId"]].fillna("/")
                
                
                # ################################
                # If the above process finished,
                # send event with '-balance-' and
                # update current GUI info with dict
                # Get the rate value, set delay time 
                window.write_event_value('-balance-', update_dict)
                interval = float(values["rate"])*60 if values["min_rate"] else float(values["rate"])
                time.sleep(interval)

        # Used to reset content
        def reset_key(key):
            window[key]('')

       
        # ######################################################
        #       Main Logic
        # ------------------------------------------------------
        # Start Threading
        threadObj = threading.Thread(target=update_balance, args=(window,), daemon=True)
        threadObj.start()

        # Event handler
        while True:
            # Read window event infinitely
            event, values = window.read()
            print("event :", event)

            # ######################################
            # Multi-threading event handler
            # --------------------------------------
            # works well, It receives therad event
            # with the update_dict's content
            # It updates the GUI content
            if event == "-balance-":
                for c in self.currencies:                                                   # Read current currency item
                    if c in values[event].keys():
                        window[c].update(f"{float(values[event][c]):.3f}")                  # Update it's value with the content of new data
                
                # ################################
                # Update Left - Upper visiable item values
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

                # #########################################
                # Update "Long Total" and "Short total" content
                if all([v in values[event] for v in ["long_total", "short_total"]]):
                    updating = f'{float(values[event]["long_total"]):.3f}' if not pd.isna(values[event]["long_total"]) else "/"
                    window["long_total"].update(updating)
                    long_color = ("green" if float(updating)>0 else "red") if updating != "/" else "blue"
                    window["long_total"].update(background_color=long_color)

                    updating = f'{float(values[event]["short_total"]):.3f}' if not pd.isna(values[event]["short_total"]) else "/"
                    window["short_total"].update(updating)
                    short_color = ("green" if float(updating) >= 0 else "red") if updating != "/" else "blue"
                    window["short_total"].update(background_color=short_color)
                
                # ##########################################
                # If there is no exists, filling with "/"
                else:
                    window["long_total"].update("/")
                    window["long_total"].update(background_color="blue")

                    window["short_total"].update("/")
                    window["short_total"].update(background_color="blue")

                # ##########################################
                # If the "table" event occurs,
                # Paint table with Green & blue colour 
                if "table" in values[event]:
                    update_df = values[event]["table"]
                    if "live" in values[event]:
                        row_colors = ((idx,"green") if pnl > 0 else (idx, "red") for idx, pnl in enumerate(update_df.loc[:,"PNL"]))
                    else:
                        row_colors = ((idx,"blue") for idx in range(len(update_df)))

                    #define colors based on sell
                    window["_tracker_"].update(values=update_df.values.tolist(), row_colors=row_colors)

            # 1
            if event == "API Settings":                                             # "File/API Setting" tab, then occurs
                window["apiframe"].update(visible=True)
            
            # 2            
            if event == "-hideapi-":                                                # Hide current api setting part
                window["apiframe"].update(visible=False)

            # 3
            if event == "-saveapi-":                                                # Save inputted key and secret code
                key_settings = {"APIKey": values["apikey"], "APISecret": values["apisecret"], "testnet": values["testnet"]}
                json.dump(key_settings, open("keys.conf", "wt"))                    # Save into json file
                self.client = Client(key_settings["APIKey"], key_settings["APISecret"], testnet=key_settings["testnet"])
            
            # 4
            if event == "Exit and Save":                                            # When the user presses "File/Exit and Save" ...
                json.dump(values, open("conf.json","wt"))
                if len(self.df) < 1:
                    self.df.to_csv("orders.csv")
                window.close()
                break
            
            # 5. Exit event
            if event == "Exit" or event == sg.WIN_CLOSED:                   
                window.close()
                break
            
            # 6.
            if event == "-clearmulti-":                                             # Clear console window, working
                window["multi"].update("")
            
            # 7
            if event in key_clear:                                                  # User presses Reset button, occurrs
                key = key_clear[event]                                              # Clear item content
                reset_key(key)
            
            # 8
            if event =="-symbol-":                                                  # When the user input current Symbol
                if values["symbol"].upper()+"USDT" in all_symbols:                  # If the user input correctly 
                    symb = values["symbol"].upper()
                    self.conf_dict["symbol"] = (symb + "USDT")                      # Update current conf_dict value
                    json.dump(values, open("conf.json", "wt"))                      # Save current symbol information
                    print("Current Symbol: " + symb)
                else:                                                               # else, print wrong message
                    window["symbol"].update(self.conf_dict["symbol"][:-4])          # restore original symbol
                    print("Warning! wrong input, please input correct symbol.")     # If it's not correct, print warning message
            
            # 9.
            if event == "market_lock":                                              # When the user selects "Market Lock"
                if values["market_lock"]:                                           # If value is checked, 
                    window["radio_market"].update(False)                            # Disable market radio button
                    window["radio_market"].update(disabled=True)
                else:
                    window["radio_market"].update(disabled=False)                   # Non-selected, enable radio button
            
            
            # 10. When the user clicks "Cancel" button
            if event in ["-cancel1-", "-cancel2-", "-cancel3-", "-cancel4-", "-cancel5-",]:
                # entry_no = event[-2]
                # if entry_no in last_trade_dict:
                #     try:
                #         params = {"symbol": self.conf_dict["symbol"], "side": "BUY" if last_trade_dict[entry_no][1]=="SELL" else "SELL", "type": "MARKET",
                #                 "quantity": last_trade_dict[entry_no][2]}
                #         order = self.client.futures_create_order(**params)
                #         print("Order canceled")
                #         if len(self.df)>0:
                #             self.df.drop(self.df.index[self.df["orderId"].eq(last_trade_dict[entry_no][0])], inplace=True)
                #         last_trade_dict.pop(entry_no)
                #     except BinanceAPIException as e:
                #         print("Unexpected error:", e.message)
                pass
            
            # 11. When the user clicks "Long" or "Short" button, occurs
            if event in ["-long1-", "-long2-", "-long3-","-long4-","-short1-", "-short2-", "-short3-","-short4-"]:
                pass
                # entry_no = event[-2]                                                    # Get the digit
                # side = "BUY" if event[1:5] == "long" else "SELL"                        # Set the side, "BUY" or "SELL"
                # json.dump(values, open("conf.json", "wt"))                              # Open the conf.json file
                # try:
                #     # Change user’s initial leverage of specific symbol market
                #     self.client.futures_change_leverage(symbol=self.conf_dict["symbol"], leverage=values["leverage"])
                #     marginType = "ISOLATED" if values["Isolated"] else "CROSSED"        # Set margin type : "ISOLATED" or "CROSSED"
                #     # Change the margin type for a symbo
                #     self.client.futures_change_margin_type(symbol=self.conf_dict["symbol"], marginType=marginType)
                # except BinanceAPIException as e:
                #     if e.code==-4046:
                #         pass
                #     else:
                #         print("Unexpected error:", e.message)
                
                # params = {
                #     "symbol": self.conf_dict["symbol"],
                #     "side": side,
                #     "quantity": values["qnty" + entry_no],
                #     "reduceOnly": values["reduce"]
                # }

                # # we get the selected radio button
                # key, order_type = next((k, v) for k, v in RADIO1_keys.items() if values[k])
                # key = "_".join(key.split("_")[1:])

                # # If the market_lock doesn't select & select market
                # if not values["market_lock"] and order_type =="MARKET":
                #     params["type"] = order_type
                #     order = self.client.futures_create_order(**params)                          # Send in a new order
                #     order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})       # Make new dataFrame with updated value
                #     self.df = self.df.append(order_df, ignore_index=True)                       # Update order dict
                #     print(f"ORDER {order['orderId']} executed")
                #     last_trade_dict[entry_no] = [order['orderId'], params["side"], params["quantity"]]
                
                # else:
                    
                #     if values["market_lock"]:                                                   # If the user selects market lock item
                #         params["type"]="MARKET"
                #         order = self.client.futures_create_order(**params)                      # Send in a new order
                #         order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})   # Make new dataFrame with updated value
                #         self.df = self.df.append(order_df, ignore_index=True)                   # Update order dict
                #         print(f"ORDER {order['orderId']} executed")
                #         last_trade_dict[entry_no] = [order['orderId'], params["side"], params["quantity"]]
                    
                #     params["type"] = order_type                                                 # Update param type with selected item's value
                    
                #     if order_type == "TRAILING_STOP_MARKET":                                    # If the user selects "TRAILING_STOP_MARKET"
                #         if values["market_lock"]:                                               # & selected market_lock item
                #             params["side"] = "BUY" if params["side"] == "SELL" else "SELL"      # Update side item
                #         params["callbackRate"] = float(values["callback_rate"])                 # Update callbackRate with inputted value

                #     else:
                #         if key == "stop_market":                                                # else, If the user selects "TRAILING_STOP_MARKET"
                #             params["side"] = "BUY" if values["check_sign"] else "SELL"
                #         elif key == "take_profit":                                              # else, If the user selects "take_profit"
                #             params["side"] = "SELL" if values["check_sign"] else "BUY"          
                    
                #     activation_type = next(k for k in self.RADIO2 if values[k])                 # Get the activation type : amount, percentage, price
                #     mark_price = float(next(p["markPrice"] for p in prices if p["symbol"] == self.conf_dict["symbol"]))
                    
                #     if activation_type == "price_value":                                        # If the user selects "Price" item
                #         if values["ap_"+ key]:
                #             #the keys our value boxes have the same ending, but different prefix.
                #             params["stopPrice"] = values["ap_" + key]                           # Update stopPrice value
                #     elif activation_type == "amount_value":                                     # If the user selects "Amount" item
                #         if values["ap_" + key]:
                #             amount = float(values["ap_" + key])
                #             add = amount if values["check_sign"] else -amount
                #             params["stopPrice"] = round(amount + mark_price, 4)                 # Update stopPrice value
                #     elif activation_type == "percentage_value":                                 # If the user selects "Percentage" item
                #         add = (float(values["percentage_" + key])/100) * mark_price
                #         add = add if values["check_sign"] else -add
                #         params["stopPrice"] = round((mark_price + add), 2)                      # Update stopPrice value

                #     if order_type == "TRAILING_STOP_MARKET" and "stopPrice" in params:          # If the user selects "Trailing" & stopPrice
                #         params["activationPrice"] = params["stopPrice"]                         # Update activationPrice and pop stopPrice
                #         params.pop("stopPrice")
                    
                #     try:
                #         order = self.client.futures_create_order(**params)                      # Send in a new order
                #         print(f"{order_type} ORDER {order['orderId']} executed")
                #     except BinanceAPIException as e:
                #         print(e.message)
                # self.df.to_csv("orders.csv")                                                    # Save current dataFrame 



# ###########################################################
#       Start Main Function
# -----------------------------------------------------------

if __name__ == "__main__":

    # Initialize the key and secret variables
    # api_key="aIiba3UUYLiElcsMaJwQBPcbXig8YtrEJPBYCAvrlGUEWKr0cHXL85uIRtJuU5QL"
    # api_secret="cjU3D8ZF1LxwN0ZLpyYqqw5id332fSZ9XFt0Cb6DPDRF1br1kBViqZy8afUX9lyJ" 
    # api_key="DsAGVwPLETLRDFcisNRNXbK10irFnyu5sRuHSRsilaLmPfoseXpj0NH3t9ooDQ59"
    # api_secret="hLaQdpIxkfTvyxESfDtz1wVgFCHUsuds3q17kccTSAgMl0ePDZNSiCYvrofNmt4T"
    api_key="4qwMmtjwUaA85tiIAGl8ypfnxd4IKp89sOUO9Chpmkf8AwIc0ONgou6QoQISPtrH"
    api_secret="9oFz2ym2f2B3KecOlcmhTaZMWWk9O3qTCZgRHtJiqgpisdEK5UyfV5H1B5AV3inM"

    # Initialize the several file names
    conf_filename = "conf.json" 
    order_filename = "orders.csv"
    trades_history_filename = "trades_history.csv"

    # Main 
    client = Client(api_key, api_secret)                                                    # Create client instance
    window = Main_window(client, conf_filename, order_filename, trades_history_filename)    # Create Main window instance
    window.main_logic()                                                                     # Perform main logic


