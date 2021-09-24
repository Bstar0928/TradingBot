layout = [
    [sg.Menu(menu_def)],
    [
        sg.pin(sg.Frame("API settings",
            [
                [sg.Text("API key",size=(10,1)),sg.Input(size=(70,1), key="apikey")],
                [sg.Text("API Secret",size=(10,1)),sg.Input(size=(70,1), key="apisecret")],
                [sg.Checkbox("Testnet", key="testnet")],
                [sg.Button("Save keys",key="-saveapi-"), sg.Button("Hide Frame", key="-hideapi-")]
            ],visible=False, key="apiframe"
            ), shrink=True
        )
    ],
    [
        sg.Column([
            [
                sg.Text("BALANCE:"), 
                sg.Text("",key="balance",size=(13,1)), 
                sg.Text(" Liquidation Price:"), 
                sg.Text("", key="liquidationPrice", size=(10, 1))
            ],
            [
                sg.Text("Margin Balance:"), 
                sg.Text("",key="margin",size=(10,1)), 
                sg.Text("Maintence Margin:"), 
                sg.Text("",key="maintence",size=(10,1))
            ],
            [
                sg.Text("Unrealized PNL:"), 
                sg.Text("",key="PNL",size=(15,1))
            ],  
            [
                sg.Text("Symbol: "),
                sg.In(default_text=conf_dict["symbol"][:-4], key="symbol", size=(10,1)), 
                sg.Checkbox('Symbol Lock', default=False,key="symbol_lock"), 
                sg.Button("Change",key="-symbol-")
            ],
            [
                sg.Radio('Crossed', 'margin', default=(not conf_dict["Isolated"]), size=(7, 1)),
                sg.Radio('Isolated', 'margin', key="Isolated", default=conf_dict["Isolated"], size=(7, 1))
            ],

            #[sg.Text('Leverage: ', size=(15, 1)), sg.Spin(values=[i for i in range(1, 126)], key="leverage",initial_value=conf_dict["leverage"], size=(6, 1))],
            #[sg.Text('Margin-type: '),sg.Radio('Isolated', 'margin',key="Isolated", default=conf_dict["Isolated"], size=(12, 1)), sg.Radio('Crossed', 'margin', default=(not conf_dict["Isolated"]), size=(12, 1))],

            [
                sg.Text("Reduce-only"), 
                sg.Checkbox("", size=(1, 1), default=conf_dict["reduce"],key="reduce"), 
                sg.Text('Leverage: ', size=(7, 1)), 
                sg.Spin(values=[i for i in range(1, 126)], key="leverage", initial_value=conf_dict["leverage"], size=(6, 1))
            ],
            [
                sg.Radio('Market', "RADIO1", default=conf_dict["radio_stop_market"], size=(6,1),key="radio_market"), 
                sg.Checkbox('Market Lock', default=False,key="market_lock")
            ],
            #sg.Radio('Take Profit', "RADIO1", key="radio3", default=conf_dict["radio3"], size=(8,1))],
            [
                sg.Radio('Amount ', "RADIO2", default=True, key="amount_value"), 
                sg.Radio('Exact Price ', "RADIO2", key="price_value"), 
                sg.Radio('Percentage ', "RADIO2", key="percentage_value")
            ], 
            [
                sg.Button('Long',key='-long2-', size=(8, 1)), ##sg.Button('Short',key='-short2-', size=(8, 1)), 
                sg.Text("Percentage") , 
                sg.Spin(values=[i/10 for i in range(1,51)], key="callback_rate",initial_value=conf_dict["callback_rate"], size=(4, 1)),
                sg.Text("Callback") , 
                sg.Spin(values=[i/10 for i in range(1,51)], key="callback_rate",initial_value=conf_dict["callback_rate"], size=(4, 1))
            ],
            [
                sg.In(key="price", default_text=conf_dict["price"], size=(10, 1)), ### sg.In(key="price", default_text=conf_dict["price"], size=(10, 1)), 
                sg.Radio('Stop Market', "RADIO1",key="radio2", default=conf_dict["radio_take_profit"], size=(10,1)), 
                sg.Radio('Trailing Stop Loss', "RADIO1",key="radio2", default=conf_dict["radio_take_profit"], size=(14,1))
            ],
            [
                sg.Button('Reset', key="clr1"),
                sg.In(key="qnty1", default_text=conf_dict["qnty1"] if "qnty1" in conf_dict else 0, size=(8, 1)),
                sg.Button('Long',key='-long1-', size=(8, 1)), 
                sg.Button('Short',key='-short1-', size=(8, 1)),
                sg.Button('Cancel',key='-cancel1-', size=(8, 1))
            ],
            [
                sg.Button('Reset', key="clr2"),
                sg.In(key="qnty2", default_text=conf_dict["qnty2"] if "qnty2" in conf_dict else 0, size=(8, 1)),
                sg.Button('Long',key='-long2-', size=(8, 1)), 
                sg.Button('Short',key='-short2-', size=(8, 1)),
                sg.Button('Cancel',key='-cancel2-', size=(8, 1))
            ],
            [
                sg.Button('Reset', key="clr3"),
                sg.In(key="qnty3", default_text=conf_dict["qnty3"] if "qnty3" in conf_dict else 0, size=(8, 1)),
                sg.Button('Long',key='-long3-', size=(8, 1)), 
                sg.Button('Short',key='-short3-', size=(8, 1)),
                sg.Button('Cancel',key='-cancel3-', size=(8, 1)), 
            ],
            [
                sg.Button('Reset', key="clr4"),
                sg.In(key="qnty4", default_text=conf_dict["qnty4"] if "qnty4" in conf_dict else 0, size=(8, 1)),
                sg.Button('Long',key='-long4-', size=(8, 1)), 
                sg.Button('Short',key='-short4-', size=(8, 1)),
                sg.Button('Cancel',key='-cancel4-', size=(8, 1)), 
            ],

            [
                sg.Button('Reset', key="clr4"),
                sg.In(key="qnty4", default_text=conf_dict["qnty4"] if "qnty4" in conf_dict else 0, size=(8, 1)),
                sg.Button('Long',key='-long4-', size=(8, 1)), 
                sg.Button('Short',key='-short4-', size=(8, 1)),
                sg.Button('Cancel',key='-cancel4-', size=(8, 1)), 
                sg.Button("Clear", key="-clearmulti-", size=(7, 1)), 
            ],

            #[sg.Button("Close Position", key="-close-"), sg.Button("Reverse Position", key="-reverse-"), sg.Button("Reset Values", key="reset"), sg.Button("Exit & Save", key="-exit-")],
            [sg.Multiline(size=(60, 5), key="multi", reroute_stdout = True,autoscroll=True ,reroute_stderr = False)],
        ]),
            
        sg.Column([

                #[sg.Text("Main Symbol: "+conf_dict["symbol"][:-4], key="symbol-value"),
                [sg.Button(c[:-4],size=(10, 1)) for c in currencies],
                [sg.Button(key=c, size=(10 ,1),) for c in currencies],
                [
                    sg.Text("Rate of change "), 
                    sg.In(key="rate", default_text=conf_dict["rate"], size=(3,1)), 
                    sg.Radio("Sec","radio_rate", key="sec_rate", default=conf_dict["sec_rate"]),
                    sg.Radio("Min","radio_rate", key="min_rate"), 
                    sg.Checkbox("Reverse Lock", size=(10, 1), key="-reverse-")
                ],
                [sg.Button(key=d, size=(10 ,1),) for d in currenciess],
                [
                    sg.Radio("Live Positions","radio_tracker", key="radio_live", default=True),
                    sg.Radio("Long History","radio_tracker", key="radio_buy"),
                    sg.Radio("Short History", "radio_tracker", key="radio_sell"),
                    sg.Checkbox('Auto-scroll to End', default=True,key="autoscroll")
                ],
                [
                    sg.Text("Long"), 
                    sg.Text("",key="long_tot",size=(9,1)), 
                    sg.Button("Close", size=(7, 1)), 
                    sg.Text("Short"), 
                    sg.Text("",key="short_tot",size=(9,1)), 
                    sg.Button("Close", size=(7, 1)), 
                    sg.Button("Clear", key="-tracker-", size=(7, 1)), 
                    sg.Button("Active", key="-clearmulti-", size=(7, 1)), 
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
                                font='Helvetica", 8')
                ]
        ])
    ]#rows
]#layout