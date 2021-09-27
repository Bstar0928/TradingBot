
from typing import Text
import PySimpleGUI as sg
import json
import pandas as pd
import ctypes, sys


class GUI_object():
    # Initialize the GUI object
    def __init__(self, _client, _conf_filename = "conf.json", _order_filename = "orders.csv", _trades_history_filename = "trades_history.csv"):
        self.client = _client                                                   # Get the current client instance
        self.table = None
        # Initialize the variable
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
                'APIKey': '',                                                   # 'APIKey': '',
                'APISecret': '',                                                # 'APISecret': '',
                'leverage': 20,                                                 # 'leverage': 20,
                'Isolated': False,                                              # 'Isolated': False,
                'reduce': True,                                                 # 'reduce': False,
                'symbol': "BTCUSDT",                                            # 'symbol': "BTCUSDT",
                'qnty1': 2,                                                     # 'qnty1': 2,
                'radio_stop_market': True,                                      # 'radio_stop_market': True,
                'radio_take_profit': False,                                     # 'radio_take_profit': False,
                'price': '',                                                    # 'price': 'No_price',
                'radio_tls': False,                                             # 'radio_tls': False,
                'price_tp': '',                                                 # 'price_tp': '',
                'TLS': False,                                                   # 'TLS': False,
                'activation_price': '',                                         # 'activation_price': '',
                'callback_rate': 0.8,                                           # 'callback_rate': 0.8,
                'sec_rate' : True,                                              # 'sec_rate' : True,
                'rate' : 1,                                                     # 'rate' : 1,
                }
        finally:
            return conf_dict

    def load_history(self, trades_history_filename):
        try:
            dft = pd.read_csv(trades_history_filename, index_col=0)             # Load trades history file content
        except FileNotFoundError:
            dft = pd.DataFrame()
        finally:
            return dft
    

    # ###############################################
    #   Initialize the layout for main window
    # -----------------------------------------------
    def get_layout(self):
        data_values = []
        data_headings = ['Symbol', 'Side', 'Amount', 'Entry Price', "Fee", "Mark Price","Exit Fee", "PNL", "Trade", "orderId"]
        visible_column_map = [True, True, True, True, True, True, True, True, True, False]
        menu_def = [['&File', ['&API Settings',"&Exit and Save"]]]
        # menu_def = [['&File', ["&Exit and Save"]]]

        layout = [
            [sg.Menu(menu_def)],
            [
                sg.Column([
                    # [
                    #     sg.pin(sg.Frame("Introduction",
                    #         [
                    #             [
                    #                 sg.Text("Description : ", size=(54,3)),
                    #             ],
                                
                    #         ],
                    #         key="apiframe", font = ("Arial", 14, "bold")), shrink=True
                    #     )
                    # ],
                    [sg.Text("")],
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
                        sg.Text("Symbol"),
                        sg.In(default_text=self.conf_dict["symbol"][:-4], size=(6, 1), key="symbol"), 
                        sg.Text("  "),
                        sg.Button("Change", key="-symbol-", size =(8, 1)),
                        sg.Text("         "),
                        sg.Checkbox('Symbol Lock', default=False, key="symbol_lock"), 
                        
                    ],
                    [
                        sg.Text("Reduce-only"), 
                        sg.Checkbox("", default=self.conf_dict["reduce"], key="reduce"), 
                        sg.Text("   Leverage"), 
                        sg.Spin(values=[i for i in range(1, 126)], key="leverage", initial_value=self.conf_dict["leverage"], size=(5, 1)),
                        sg.Text("   Callback"), 
                        sg.Spin(values=[i/10 for i in range(1,51)], key="percentage_tls",initial_value=self.conf_dict["callback_rate"], size=(5, 1)),
                    ],
                    [
                        sg.Radio('Crossed', 'margin', default=(not self.conf_dict["Isolated"]), key="Crossed"),
                        sg.Text(" "*8),
                        sg.Radio('Isolated', 'margin', key="Isolated")
                    ], 
                    
                    [
                        sg.Radio('Market', "RADIO1", default=self.conf_dict["radio_market"], key="radio_market"),
                        sg.Text(" "*10),
                        sg.Checkbox('Market Lock', default=False, key="market_lock", enable_events=True)
                    ],
                    [
                        sg.Radio('Stop Market', "RADIO1",key="radio_stop_market"), 
                        sg.Text(" "*2),
                        sg.Radio('Trailing Stop Loss', "RADIO1",key="radio_tls")
                    ],
                    # [sg.Text("")], 
                    [
                        
                        sg.Radio('Amount  ', "RADIO2", default=True, key="amount_value"), 
                        sg.Text(" "*7),
                        sg.Radio('Exact Price', "RADIO2", key="price_value"), 
                        sg.Text(" "*5),
                        sg.In(key="qnty7", default_text=self.conf_dict["qnty7"] if "qnty7" in self.conf_dict else 0, size=(6, 1)),
                        sg.Button('Above', size=(8, 1)),
                    ],
                    [
                        sg.Radio('Percentage ', "RADIO2", key="percentage_value"),
                        sg.Text(" "*4),
                        sg.Spin(values=[i/10 for i in range(1,51)], key="callback_rate",initial_value=self.conf_dict["callback_rate"], size=(5, 1)),
                        sg.Button('Long', size=(8, 1)), 
                    ],
                    # [
                    #     sg.Button('Long', size=(8, 1)), 
                    # ],
                    [
                        sg.Text("Single order mode"),
                    ],
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
                    # [sg.Multiline(size=(60, 5), key="multi", reroute_stdout = True,autoscroll=True ,reroute_stderr = False)],
                    [
                        sg.Button("Clear", key="-clearmulti-", size=(7, 1)), 
                    ],
                    
                ], expand_y = True),
                    
                sg.Column([
                        # [
                        #     sg.pin(sg.Frame("API settings",
                        #         [
                        #             [
                        #                 sg.Text("API key", size=(11,1)),
                        #                 sg.Input(size=(73,1), key="apikey1"),
                        #                 # sg.Text("", size = (2, 1)),
                        #                 sg.Checkbox("Testnet", key="testnet1")
                        #             ],
                        #             [
                        #                 sg.Text("API Secret", size=(11,1)),
                        #                 sg.Input(size=(73,1), key="apisecret1"),
                        #                 # sg.Text("", size = (2, 1)),
                        #                 sg.Button("Save keys",key="-saveapi1-", size = (11, 1))
                        #             ],
                        #         ],
                        #         key="apiframe1",
                        #         ), shrink=True,
                        #     )
                        # ],
                        [sg.Text("")],
                        [sg.Button(c[:-4], key="-"+c+"-", size=(11, 1)) for c in self.currencies],
                        [sg.Button(key=d, size=(11 ,1), button_text="- . -- %") for d in self.currencies],
                        [sg.Button(key=c, size=(11 ,1), enable_events=False) for c in self.currencies],
                        [
                            sg.Text("Rate of change "), 
                            sg.In(key="rate", default_text=self.conf_dict["rate"], size=(3,1)), 
                            sg.Radio("Sec","radio_rate", key="sec_rate", default=True),
                            sg.Radio("Min","radio_rate", key="min_rate"), 
                            # sg.Text("       "), 
                            sg.Button("Reset", size=(8, 1), key="-applyrate-"), 
                            sg.Text("Counter:"), 
                            sg.Text(text =300, key="counterdown", size=(3,1)), 
                            sg.Checkbox("Convert USDT", default=True, key="toggle_USDT"),
                            sg.Checkbox("Reverse Lock", size=(10, 1), key="reverse_lock", enable_events=True),
                        ],
                        [sg.Text("")],
                        [
                            sg.Checkbox("Enable Tracker", key="tracker_on", default=True),
                            sg.Radio("Live Positions","radio_tracker", key="radio_live", default=True),
                            sg.Radio("Long History","radio_tracker", key="radio_long"),
                            sg.Radio("Short History", "radio_tracker", key="radio_short"),
                        ],
                        [
                            sg.Text("Profit"), 
                            sg.Text("", key="long_total", size=(9,1), font="Arial, 11"), 
                            sg.Button("Close", size=(7, 1), key="-close_long-"), 
                            sg.Text("    "),
                            sg.Text("Losses"), 
                            sg.Text("", key="short_total", size=(9,1), font="Arial, 11"), 
                            sg.Button("Close", size=(7, 1), key="-close_short-"), 
                            sg.Text("    "),
                            sg.Text("Total"),
                            sg.Text("", key="total_pnl", size=(9, 1), font="Arial, 11"), 
                            sg.Button("Close", size=(7, 1), key="-close_total-"), 
                        ],
                        # [
                        #     sg.Checkbox("Show", default=True, key="-"+str(i)+"_sh-", size=(7, 1)) for i in range(len(data_headings)-2)
                        # ],
                        [sg.Table(values=data_values, headings=data_headings,
                                        max_col_width=55,
                                        auto_size_columns=False,                       
                                        select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                                        justification='center',
                                        enable_events=True,
                                        col_widths=[9,8,8,8,9,9,9,],
                                        visible_column_map=visible_column_map,
                                        num_rows=13, key='_tracker_',
                                        row_height=28,
                                        font='Helvetica", 10')
                        ],
                        [
                            sg.Button("Clear", key="-cleartracker-", size=(7, 1)), 
                            sg.Button("Active", key="-active-", size=(7, 1)), 
                            sg.Checkbox('Auto-scroll to End', default=True, key="autoscroll")
                        ], 
                ], expand_y = True)
            ] # rows
        ] # layout
        return layout
  
    
    def init_Window(self):
        sg.theme_background_color("#323233")                                                    # Set background color
        sg.theme_button_color(("#e1e1e1", '#1e1e1e'))                                           # Set button color
        sg.theme_element_background_color("#323233")        
        sg.theme_text_element_background_color("#323233")
        sg.theme_text_color("#d6d6d6")
        
        window = sg.Window( 
            'Main Window',                                                                      # Initilalize the main window
            self.get_layout(), 
            finalize=True, 
            font="Helvetica, 10",
            )   
            # keep_on_top=True)   
        self.table = window['_tracker_']                                                        # Define window table
        self.table.bind('<Button-1>', "Click")                                                  # and apply button property
        table_widget = window['_tracker_'].Widget
        anchors = ["center", "center", "center", "center", "center", "e", "e", "e", "center"]
        for cid, anchor in enumerate(anchors):
            table_widget.column(cid, anchor=anchor)
        return window
    
    

