        while True:
            # Read window event infinitely
            event, values = window.read()

            # ##################################################
            # 1. API setting event, when the user presses
            # "File/API Setting" tab, then occurs
            # --------------------------------------------------
            # works well
            if event == "API Settings":
                window["apiframe"].update(visible=True)
            
            # ##################################################
            # 2. Hide current api setting part
            # -------------------------------------------------
            # works well
            if event == "-hideapi-":
                window["apiframe"].update(visible=False)

            
            # ##################################################
            # 3. If the current user inputs it's own apikey and
            # secret and press save button, then occurs
            # --------------------------------------------------
            # works well
            if event == "-saveapi-":
                key_settings = {"APIKey": values["apikey"], "APISecret": values["apisecret"], "testnet": values["testnet"]}
                json.dump(key_settings, open("keys.conf", "wt"))
                self.client = Client(key_settings["APIKey"], key_settings["APISecret"], testnet=key_settings["testnet"])
            
            

            # ##################################################
            # 4. If the event is exist in current currency and
            # if not checked symbol lock, then it occurs
            # --------------------------------------------------
            # **** but in this project, it's ignored ****
            if event in ["-"+c+"-" for c in self.currencies] and not values["symbol_lock"]:
                new_currency = event[1:-1]
                position_info = self.client.futures_position_information()
                symbol_position = float(next(p["positionAmt"] for p in position_info if p["symbol"] == self.conf_dict["symbol"]))

                params = {}
                params["side"] = "BUY"  if symbol_position<0 else "SELL"
                params["quantity"] = round(abs(symbol_position), 3)
                params["symbol"] = self.conf_dict["symbol"]
                params["type"] = "MARKET"
                self.df.drop(self.df.index, inplace=True)
                if params["quantity"] != 0:
                    #we make the opposite trade
                    order = self.client.futures_create_order(**params)
                    while True:
                        try:
                            order_info = self.client.futures_get_order(symbol=params["symbol"], orderId=order["orderId"])
                            #we iterate throught the loop until the status is FILLED, meaning the trade was executed.
                            if order_info["status"] == "FILLED":
                                break
                        except BinanceAPIException as e:
                            print(e.message)
                        time.sleep(0.1)

                    trades = self.client.futures_account_trades()
                    trades_df = pd.DataFrame.from_dict(trades)
                    trades_df = trades_df.astype({"commission": float, "quoteQty": float})
                    commission, val = trades_df.loc[trades_df["orderId"].eq(order_info["orderId"]) ,["commission", "quoteQty"]].sum()
                    usdt_amount = abs(val) - commission

                    new_price = float(next(p["markPrice"] for p in prices if p["symbol"] == new_currency))

                    params["side"] = params["side"] if values["reverse_lock"] else "BUY" if params["side"] =="SELL" else "SELL"
                    params["quantity"] = round((usdt_amount/new_price), currency_precision[new_currency])
                    params["symbol"] = new_currency
                    order = self.client.futures_create_order(**params)
                    order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
                    self.df = self.df.append(order_df, ignore_index=True)

                self.conf_dict["symbol"] = new_currency
                window["symbol"].update(new_currency[:-4])
                window["symbol-value"].update(("Current Symbol: " + new_currency[:-4]))
                json.dump(values, open("conf.json", "wt"))

                self.df.to_csv("orders.csv")


            # ##############################################            
            # 5. when the user presses "File/Exit and Save"
            #  tab, it occurs. Save current settings
            if event == "Exit and Save":
                json.dump(values, open("conf.json","wt"))
                self.df.to_csv("orders.csv")
                window.close()
                break
            
            # ##############################################
            # 6. when the user presses "Exit Position", occurs
            # ------------------------------------------------
            # It produces exception messages : not working
            if event == "-closeall-":
                position_info = self.client.futures_position_information()
                position_amt = float(next(p["positionAmt"] for p in position_info if p["symbol"] == self.conf_dict["symbol"]))
                params = {
                    "symbol": self.conf_dict["symbol"], 
                    "side": "BUY" if position_amt < 0 else "SELL",
                    "type": "MARKET",
                    # "quantity": abs(position_amt)
                    "quantity": round(abs(position_amt), 3)
                    }

                order = self.client.futures_create_order(**params)
                self.df.drop(self.df.index, inplace=True)
                self.df.to_csv("orders.csv")
                self.df = pd.DataFrame()
                window["_tracker_"].update(values=self.df.values.tolist())

            # 7. Exit event
            if event == "Exit" or event == sg.WIN_CLOSED:
                window.close()
                break
            
            # ##############################################
            # 8. when the user presses "Clear live tracker"
            # ----------------------------------------------
            # working
            if event == "-cleartracker-":
                self.df = pd.DataFrame()
                window["_tracker_"].update(values=self.df.values.tolist())
            
            # ##############################################
            # 9. clear console window, working
            if event == "-clearmulti-":
                window["multi"].update("")
            
            # ##############################################
            # 10. When user click mouse on table, occurs
            # ---------------------------------------------
            # It produces some exception, not working
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
                    # print(table_values)
                    # print(len(table_values), row)
                    position_amt = float(round(table_values[row-1][2],6))
                    params = {"symbol": self.conf_dict["symbol"], "side": "BUY" if table_values[row-1][1]=="SELL" else "SELL", "type": "MARKET",
                            "quantity": abs(position_amt)}
                    order = self.client.futures_create_order(**params)
                    if row == 1:
                        self.df.drop(self.df.index, inplace=True)
                    else:
                        self.df.drop(self.df.index[self.df["orderId"].eq(int(table_values[row-1][9]))], inplace=True)
                    self.df.to_csv("orders.csv")
                    print(f"ORDER {order['orderId']} executed")

            # ##############################################            
            # 11. When user click mouse on close button, occurs
            # ---------------------------------------------
            # It produces some exception, not working
            if event in ["-close_short-", "-close_long-"]:
                side = "BUY" if event == "-close_long-" else "SELL"
                amount = self.df.loc[self.df["side"].eq(side), "origQty"].sum()
                self.df.drop(self.df.index[self.df["side"].eq(side)], inplace=True)
                self.df.to_csv("orders.csv")
                params = {
                    "symbol": self.conf_dict["symbol"], "side": "BUY" if side == "SELL" else "SELL",
                    "type": "MARKET",
                    "quantity":  float(round(amount, 4))
                }
                order = self.client.futures_create_order(**params)
                print("Closing order Executed:", order["orderId"])
            
            # ######################################
            # 12. It's ignored, no needs anymore
            if event == "reset":
                for key in all_keys_to_clear:
                    window[key]('')
            
            # ######################################
            # 13. working : user presses Reset button, occurs
            if event in key_clear:
                key = key_clear[event]
                reset_key(key)
            
            # ######################################
            # 14. When the user input current Symbol and
            #  press Change button, occurs
            # ---------------------------------------
            # works well
            if event =="-symbol-":
                if values["symbol"].upper()+"USDT" in all_symbols:                  # Id the user input correctly 
                    symb= values["symbol"].upper()
                    self.conf_dict["symbol"]=(symb+ "USDT")
                    json.dump(values, open("conf.json", "wt"))
                    window["symbol-value"].update(("Current Symbol: "+symb))        # Update current symbol item     
                    print("Current Symbol: "+symb)
                else:                                                               # else, print wrong message
                    window["symbol"].update(self.conf_dict["symbol"][:-4])
                    print("Wrong input.")
            
            # ######################################
            # 15. No more needs to exist, ignored
            if event == "-close-":
                positions = self.client.futures_position_information(symbol=self.conf_dict["symbol"])
                position_amt = float(positions[0]["positionAmt"])
                if abs(position_amt) > 0:
                    params = {"symbol": self.conf_dict["symbol"], "side": "SELL" if position_amt>0 else "BUY", "type": "MARKET","quantity":abs(position_amt)}
                    order = self.client.futures_create_order(**params)
                    order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
                    self.df = self.df.append(order_df, ignore_index=True)
                    self.df.to_csv("history"+str(time.time())+".csv")
                    self.df = self.df[0:0]
                    self.df.to_csv("orders.csv")
                    print(f"ORDER {order['orderId']} executed")
                else:
                    print("NO position Open")
            
            # ######################################
            # 16. No more needs to exist, ignored
            if event == "-reverse-":
                positions = self.client.futures_position_information(symbol=self.conf_dict["symbol"])
                if not values["Isolated"] and len(positions)>0 and positions[0]['marginType'] =="cross":
                    positions = self.client.futures_position_information(symbol=self.conf_dict["symbol"])
                    position_amt = float(positions[0]["positionAmt"])
                    params = {"symbol": self.conf_dict["symbol"], "side": "SELL" if position_amt > 0 else "BUY", "type": "MARKET",
                            "quantity": position_amt*2}
                    order = self.client.futures_create_order(**params)
                    order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
                    self.df = self.df.append(order_df, ignore_index=True)
                    self.df.to_csv("history" + str(time.time()) + ".csv")
                    self.df = self.df.iloc[-1,:]
                    self.df.to_csv("orders.csv")
                    print(f"ORDER {order['orderId']} executed")
                else:
                    print("Reverse position only works in cross-mode with an existing open position")
            
            # ######################################
            # 17. It's a multi-threading event handler
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

            # ######################################
            # 18. No more needs to exist, ignored
            if event == "-tls-":
                positions = self.client.futures_position_information(symbol=self.conf_dict["symbol"])
                position_amt = float(positions[0]["positionAmt"])
                params = {"symbol": self.conf_dict["symbol"], "side": "SELL" if position_amt>0 else "BUY", "type": "TRAILING_STOP_MARKET","callbackRate":values["callback_rate"] ,"quantity":-position_amt}
                if len(values["activation_price"])>0:
                    params["activationPrice"]=values["activation_price"]
                order = self.client.futures_create_order(**params)
                order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
                self.df = self.df.append(order_df, ignore_index=True)
                self.df.to_csv("orders.csv")
                print(f"ORDER {order['orderId']} executed")
            
            # ######################################
            # 19. When the user selects "Market Lock"
            # --------------------------------------
            # works well
            if event == "market_lock":
                if values["market_lock"]:
                    window["radio_market"].update(False)
                    window["radio_market"].update(disabled=True)
                else:
                    window["radio_market"].update(disabled=False)
            
            # ######################################
            # 20. When the user clicks "Cancel" button
            # --------------------------------------
            # not working, ignored
            if event in ["-cancel1-", "-cancel2-", "-cancel3-","-cancel4-"]:
                entry_no = event[-2]
                if entry_no in last_trade_dict:
                    try:
                        params = {"symbol": self.conf_dict["symbol"], "side": "BUY" if last_trade_dict[entry_no][1]=="SELL" else "SELL", "type": "MARKET",
                                "quantity": last_trade_dict[entry_no][2]}
                        order = self.client.futures_create_order(**params)
                        print("Order canceled")
                        if len(self.df)>0:
                            self.df.drop(self.df.index[self.df["orderId"].eq(last_trade_dict[entry_no][0])], inplace=True)
                        last_trade_dict.pop(entry_no)
                    except BinanceAPIException as e:
                        print("Unexpected error:", e.message)
            
            # ######################################
            # 21. When the user clicks "Long" or
            #  "Short" button, occurs
            # --------------------------------------
            # 
            if event in ["-long1-", "-long2-", "-long3-","-long4-","-short1-", "-short2-", "-short3-","-short4-"]:
                entry_no = event[-2]                                                    # Get the digit
                side = "BUY" if event[1:5] == "long" else "SELL"                        # Set the side, "BUY" or "SELL"
                json.dump(values, open("conf.json", "wt"))                              # Open the conf.json file
                try:
                    # Change user’s initial leverage of specific symbol market
                    self.client.futures_change_leverage(symbol=self.conf_dict["symbol"], leverage=values["leverage"])
                    marginType = "ISOLATED" if values["Isolated"] else "CROSSED"        # Set margin type : "ISOLATED" or "CROSSED"
                    # Change the margin type for a symbo
                    self.client.futures_change_margin_type(symbol=self.conf_dict["symbol"], marginType=marginType)
                except BinanceAPIException as e:
                    if e.code==-4046:
                        pass
                    else:
                        print("Unexpected error:", e.message)
                
                params = {
                    "symbol": self.conf_dict["symbol"],
                    "side": side,
                    "quantity": values["qnty" + entry_no],
                    "reduceOnly": values["reduce"]
                }

                # we get the selected radio button
                key, order_type = next((k, v) for k, v in RADIO1_keys.items() if values[k])
                key = "_".join(key.split("_")[1:])

                # If the market_lock doesn't select & select market
                if not values["market_lock"] and order_type =="MARKET":
                    params["type"] = order_type
                    order = self.client.futures_create_order(**params)                          # Send in a new order
                    order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})       # Make new dataFrame with updated value
                    self.df = self.df.append(order_df, ignore_index=True)                       # Update order dict
                    print(f"ORDER {order['orderId']} executed")
                    last_trade_dict[entry_no] = [order['orderId'], params["side"], params["quantity"]]
                
                else:
                    
                    if values["market_lock"]:                                                   # If the user selects market lock item
                        params["type"]="MARKET"
                        order = self.client.futures_create_order(**params)                      # Send in a new order
                        order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})   # Make new dataFrame with updated value
                        self.df = self.df.append(order_df, ignore_index=True)                   # Update order dict
                        print(f"ORDER {order['orderId']} executed")
                        last_trade_dict[entry_no] = [order['orderId'], params["side"], params["quantity"]]
                    
                    params["type"] = order_type                                                 # Update param type with selected item's value
                    
                    if order_type == "TRAILING_STOP_MARKET":                                    # If the user selects "TRAILING_STOP_MARKET"
                        if values["market_lock"]:                                               # & selected market_lock item
                            params["side"] = "BUY" if params["side"] == "SELL" else "SELL"      # Update side item
                        params["callbackRate"] = float(values["callback_rate"])                 # Update callbackRate with inputted value

                    else:
                        if key == "stop_market":                                                # else, If the user selects "TRAILING_STOP_MARKET"
                            params["side"] = "BUY" if values["check_sign"] else "SELL"
                        elif key == "take_profit":                                              # else, If the user selects "take_profit"
                            params["side"] = "SELL" if values["check_sign"] else "BUY"          
                    
                    activation_type = next(k for k in self.RADIO2 if values[k])                 # Get the activation type : amount, percentage, price
                    mark_price = float(next(p["markPrice"] for p in prices if p["symbol"] == self.conf_dict["symbol"]))
                    
                    if activation_type == "price_value":                                        # If the user selects "Price" item
                        if values["ap_"+ key]:
                            #the keys our value boxes have the same ending, but different prefix.
                            params["stopPrice"] = values["ap_" + key]                           # Update stopPrice value
                    elif activation_type == "amount_value":                                     # If the user selects "Amount" item
                        if values["ap_" + key]:
                            amount = float(values["ap_" + key])
                            add = amount if values["check_sign"] else -amount
                            params["stopPrice"] = round(amount + mark_price, 4)                 # Update stopPrice value
                    elif activation_type == "percentage_value":                                 # If the user selects "Percentage" item
                        add = (float(values["percentage_" + key])/100) * mark_price
                        add = add if values["check_sign"] else -add
                        params["stopPrice"] = round((mark_price + add), 2)                      # Update stopPrice value

                    if order_type == "TRAILING_STOP_MARKET" and "stopPrice" in params:          # If the user selects "Trailing" & stopPrice
                        params["activationPrice"] = params["stopPrice"]                         # Update activationPrice and pop stopPrice
                        params.pop("stopPrice")
                    
                    try:
                        order = self.client.futures_create_order(**params)                      # Send in a new order
                        print(f"{order_type} ORDER {order['orderId']} executed")
                    except BinanceAPIException as e:
                        print(e.message)
                self.df.to_csv("orders.csv")                                                    # Save current dataFrame 


