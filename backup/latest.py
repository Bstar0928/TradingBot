# Not change color

import os
from tkinter.constants import DISABLED
from binance.exceptions import BinanceAPIException
import PySimpleGUI as sg
import threading
from binance import Client
import json
import time
import numpy as np
import pandas as pd
import ctypes, sys
from datetime import datetime
from utils.event_handler import applyRate_handler, get_interval

# ###############################################
#   Initialize the variables for main logic
# -----------------------------------------------
# Create Main window and initialize the variables

def Process(_obj):
    
    window = _obj.init_Window()                                                                                     # Initialize the window object                                                                       
    last_trade_dict = dict()                                                                                        # Define new dictionary
    # all_keys_to_clear = ["qnty1", "qnty2", "qnty3", "qnty4", "callback_rate", "radio2", "activation_price", "TLS"]  
    key_clear = {"clr1": "qnty1", "clr2": "qnty2", "clr3": "qnty3", "clr4": "qnty4", "clr5": "qnty5"}               # define clear keys
    RADIO1_keys = {                                                                                                 # Define radio buttons
        'radio_market': "MARKET",
        'radio_stop_market': "STOP_MARKET",
        'radio_take_profit': "TAKE_PROFIT_MARKET",
        "radio_tls": "TRAILING_STOP_MARKET"
    }


    # ######################################################
    # Read Mark Price and Funding Rate and
    # read window event and values for Thread
    # prices = _obj.client.futures_mark_price()
    event, values = window.read(timeout=0)

    

    # ######################################################
    # Get the precision of current currency
    # different _obj.currencies have different level of precision
    # as in number behind the decimal point
    all_symbols_return = _obj.client.futures_exchange_info()                                                    # Get the Current exchange trading rules
    currency_precision = {}                                                                                     # define new dict
    for c in _obj.currencies:                                                                                   
        currency_precision[c] = next(s["quantityPrecision"] for s in all_symbols_return["symbols"] if s["symbol"] == c)

    
    # ######################################################
    #   Define Threading, reset key method
    # ------------------------------------------------------
    # rate_buffer = [0] * 300                                                                                   # Used to save current currency
    def update_balance(window):
        while True:
            result_account = _obj.client.futures_account()                                                      # Get the current account info and 
            update_dict = {"balance" : result_account["availableBalance"]}                                      # update dict with it's value
            k = ["totalMaintMargin", "totalMarginBalance", "totalUnrealizedProfit"]     
            for key in k:       
                update_dict[key] = result_account[key]                                                          # update dict with it's value

            pos = _obj.client.futures_position_information()                                                    # Get the position info and
            position_info = next(item for item in pos if item["symbol"] == _obj.conf_dict["symbol"])            # pick the info with current symbol, e.g. "currency" : XRPUDST
            update_dict["liquidationPrice"] = position_info["liquidationPrice"]                                 # update dict with it's value
            global prices     
            prices = _obj.client.futures_mark_price()                                                           # Get the mark price info
            for p in prices:        
                if p["symbol"] in _obj.currencies:      
                    update_dict[p["symbol"]] = p["markPrice"]                                                   # update dict with symbol and price

            # ######################################        
            # If the user select Live Tracker radio,        
            if values["radio_live"]:                                                                            # If the user select Live Tracker radio,
                # #############################
                # If the order file dict exists
                if len(_obj.df)>0:
                    symbol_price = next(item for item in prices if item["symbol"] == _obj.conf_dict["symbol"])  # Get the current currency and my trade and
                    update_a = _obj.client.futures_account_trades()                                             # and Filter with current currency 
                    update_df = pd.DataFrame.from_dict(update_a)
                    update_df = update_df.astype({"price": "float", "qty": "float", "commission": "float"})     # update my trade's "Mark Price" => current value
                    update_df = update_df.loc[update_df["symbol"].eq(_obj.conf_dict["symbol"]), :]
                    update_df["Mark Price"] = float(symbol_price["markPrice"])
                    update_df = update_df.merge(_obj.df, on ="orderId", suffixes=("", "_r"), how='inner')       # Filter update dataFrame
                    

                    # ########################
                    # If success
                    if len(update_df) >0:                                                                       # If success
                        update_df["commission"] = update_df.groupby(by="orderId")["commission"].cumsum()        # Calculate each colum's sum, mean ...
                        update_df["price"] = update_df.groupby(by="orderId")["price"].transform(lambda x: x.mean()) 
                        update_df["qty"] = update_df.groupby(by="orderId")["qty"].transform(lambda x: x.sum())  # Calculate each colum's sum, mean ...
                        update_df = update_df.drop_duplicates(keep="last", subset="orderId")                    # and update "commission", "price", "qty"

                        # Save history dataFrame
                        _obj.dft = _obj.dft.append(update_df.drop("Mark Price", axis=1), ignore_index=True)
                        _obj.dft = _obj.dft.drop_duplicates(keep="last", subset=["orderId", "qty"])
                        _obj.dft.to_csv("utils/trades_history.csv")

                        update_df["Trade"] = "Close"                                                            # add "Trade" key item and calculate total sum
                        total_amount = update_df.apply(lambda x:  x["qty"] if x["side"] =="BUY" else x["qty"] * -1, axis=1).sum() # of the "qty" column 
                        update_df = update_df.append({                                                          # and append update_df dict with new values
                            "symbol": _obj.conf_dict["symbol"],
                            "side": "BUY" if total_amount>0 else "SELL",
                            "qty": total_amount,
                            "price": update_df["price"].mean(),
                            "commission": update_df["commission"].sum(),
                            "Trade" : "Close All",
                            "Mark Price":  float(symbol_price["markPrice"]),
                        }, ignore_index=True)
                        update_df = update_df.iloc[::-1]                                                        # Filter update dataFrame

                        # Construct a update dataFrame
                        update_df["Exit Fee"] = (update_df["commission"] / (update_df["qty"] * update_df["price"])) * update_df["qty"] * update_df["Mark Price"]
                        update_df["PNL"] = (update_df["Mark Price"] * update_df["qty"]) - ((update_df["qty"] * update_df["price"]))  # + update_df["Fee"])
                        update_df["PNL"] = update_df.apply(lambda x: x["PNL"] * -1 if x["side"] == "SELL" else x["PNL"], axis=1)
                        update_df["PNL"] = update_df["PNL"] - update_df["commission"]
                        update_df["PNL"] = update_df["PNL"] - update_df["Exit Fee"]
                        update_dict["long_total"] = update_df.iloc[1:,:].loc[update_df["side"].eq("BUY"),"PNL"].sum(min_count=1)
                        update_dict["short_total"] = update_df.iloc[1:,:].loc[update_df["side"].eq("SELL"),"PNL"].sum(min_count=1)
                        update_df = update_df.loc[:, ["symbol", "side", "qty", "price", "commission", "Mark Price","Exit Fee", "PNL","Trade", "orderId"]]
                        update_dict["table"]=update_df                                                          # Finally, make update_dict["table"] item

                        ########### 
                        # update_df.to_csv("backup\\updated_at3.csv")

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
                _obj.dft = _obj.load_history(_obj.history_filename)                                             # Load history file            
                update_df = pd.concat([update_df, _obj.dft], ignore_index=True, axis=0)                         # Concatenate each dataFrame
                update_df = update_df.loc[update_df["side"].eq("BUY" if values["radio_long"] else "SELL"), :]
                update_dict["table"] = update_df.loc[:,["symbol", "side", "qty", "price", "commission", "Mark Price", "Exit Fee", "PNL", "Trade","orderId"]].fillna("/")
            
            
            # ################################
            # If the above process finished,
            # send event with '-balance-' and
            # update current GUI info with dict
            # Get the rate value, set delay time 
            window.write_event_value('-balance-', update_dict)
            time.sleep(0.8)


        
        
            
    
    # #############################################
    # This is first thread function: it counts down
    # the rate value 
    # thread_state = True
    def counterdown(window):
        thread1 = threading.Thread(target=update_balance, args=(window, ), daemon=True)                         # Initialize first thread
        thread1.start()                                                                                         # Start thread
        thread1.join()
        seconds = int(values["rate"]) if not values["min_rate"] else int(values["rate"]) * 60                   # Get the current rate
        seconds = get_interval(values)
        while True:
            window["counterdown"].update(round(seconds * 0.01, 2))                                              # Update current rate count
            seconds -= 1                                                                                        # Decrease count
            if seconds < 1:                                                                                     # If the current sec < 1, disable apply
                window["-applyrate-"].update(disabled = True)           
            else:                                                                                               # else, enable
                window["-applyrate-"].update(disabled = False)
            if seconds < 0:
                seconds = get_interval(values)                                                                  # Read current second
                thread1 = threading.Thread(target=update_balance, args=(window, ), daemon=True)                 # Initialize first thread 
                thread1.start()                                                                                 # Start first thread
                thread1.join()
            time.sleep(1)

    
    # ######################################
    #   Read Price Thread methiod
    # --------------------------------------
    # It read current price at a 1 sec, and
    # Save it's value into buffer
    price_Buffer = {i:[] for i in _obj.currencies}                                                              # Initialize the rate buffer
    counter_state = True                                                                                        # Counter state
    def read_prices():
        while True:
            prices = _obj.client.futures_mark_price()                                                           # Get the current price info
            for p in prices:
                if p["symbol"] in _obj.currencies:
                    if len(price_Buffer[p["symbol"]]) < 300:                                                    # If the length of buffer is less than 5 min
                        price_Buffer[p["symbol"]].append(float(p["markPrice"]))                                 # append it
                    else:           
                        price_Buffer[p["symbol"]].pop(0)                                                        # Else, remove oldest node
                        price_Buffer[p["symbol"]].append(float(p["markPrice"]))                                 # and, input new node
            
            
            try:
                second = int(values["rate"])                                                                    # Calculate rate of change
                if not values["min_rate"]:                                                                      # Set the rate value 5 ~ 59 sec
                    if second < 5:                                                                              # If the user input minus value
                        second = 5                                                                              # Reset
                        print("Warning! Please input 5 ~ 59 sec value.")                                        # Print warning msg
                        window["rate"].update(5)                                                            
                    elif second > 59:                                                                           # Else, it's bigger than 1 min
                        second = 59                                                                             # Reset
                        print("Warning! Please input 5 ~ 59 sec value.")                                        # Print warning msg
                        window["rate"].update(59)    
                else:                                                                                           # Set the rate value 1 ~ 5 min
                    if second < 1:                                                                              # If the user input minus value
                        second = 1                                                                              # Reset
                        print("Warning! Please input 1 ~ 5 min value.")
                        window["rate"].update(1)                                                                # Reset
                    elif second > 5:                                                                            # Else, it's bigger than 5 min
                        second = 5                                                                              # Reset
                        print("Warning! Please input 1 ~ 5 min value.")
                        window["rate"].update(5)                                                                # Reset
                    second *= 60                                                                                # Convert into sec value
                cur_index = second
            except Exception as e:                                                                              # If there is an error
                print("Error!, Please input correctly.")
                if not values["min_rate"]:
                    window["rate"].update(5)                                                                    # Reset content into 5 sec
                    second = 5  
                else:
                    window["rate"].update(5)    
                    second = 300                                                                                # Reset content into 5 min
                cur_index = second                                                                              # Save current seconds

            # print(cur_index)
            pre_list = []                                                                                       # Pre-temporary buffer
            cur_list = []                                                                                       # Cur-temporary buffer
            for p in _obj.currencies:                                                                           # check current currencies
                window[p].update(f"{float(price_Buffer[p][-1]):.3f}")                                           # Update it's value with the content of new data
                # check validity of buffer data
                # print(len(price_Buffer[p]))
                if len(price_Buffer[p]) >= cur_index:                                                           # check current buffer length
                    pre_list.append(price_Buffer[p][-cur_index])                                                # append pre value
                    cur_list.append(price_Buffer[p][-1])                                                        # append cur value
            
            
            # check toggle state
            
            if values["toggle_USDT"]:
                # display %
                if len(pre_list) != 0:                                                                              # If the data available, calculate percentage
                    percent = (np.array(cur_list) - np.array(pre_list))/np.array(pre_list) * 100                    # Calculate percentage
                    for i, c in enumerate(_obj.currencies):  
                        temp = round(percent[i], 2)                                                                 # Read current currency item
                        if temp == (-0.00):
                            temp = 0.00
                        if temp > 0:                                                                                # check threshold value
                            color = ("green", "#1e1e1e")                                                            # Set green
                        elif temp == 0:
                            color = ("#f7983c", "#1e1e1e")                                                          # Set yello
                        else:                   
                            color = ("#ff2222", "#1e1e1e")                                                          # Set red color
                        window[c + str(i)].update("{}%".format(temp), button_color=color)                           # Update it's value with the content of new data
                else:                                                                                               # If there is no data available yet, print  -.--%
                    for i, c in enumerate(_obj.currencies):                                                         # Read current currency item
                        window[c + str(i)].update("-.--%", button_color = ("#e1e1e1", '#1e1e1e'))                                                          # Update it's value with the content of new data
            
            else:
                # display USDT
                if len(pre_list) != 0:                                                                              # If the data available, calculate percentage
                    usdt = (np.array(cur_list) - np.array(pre_list))                                                # Calculate percentage
                    for i, c in enumerate(_obj.currencies):                                                         # Read current currency item
                        temp = round(usdt[i], 2)                                                                    # Read current currency item
                        if temp == (-0.00):
                            temp = 0.00
                        if temp > 0:
                            color = ("green", "#1e1e1e")                                                            # Set green colour
                        elif temp == 0: 
                            color = ("#f7983c", "#1e1e1e")                                                          # Set yello colour
                        else:   
                            color = ("#ff2222", "#1e1e1e")                                                          # Set red colour
                        window[c + str(i)].update("{}".format(temp), button_color=color)                            # Update it's value with the content of new data

                # If there is no data available yet, print  -.--%
                else:
                    for i, c in enumerate(_obj.currencies):                                                         # Read current currency item
                        window[c + str(i)].update("-.--", button_color = ("#e1e1e1", '#1e1e1e'))                                                          # Update it's value with the content of new data

            if counter_state:
                window["counterdown"].update(300 - len(price_Buffer["ADAUSDT"]))                                # Count current timer
            time.sleep(1)


    
    # ######################################################
    #       Main Logic
    # ------------------------------------------------------
    # Start Threading
    thread2 = threading.Thread(target=update_balance, args=(window, ), daemon=True)                             # Initialize the update balance thread
    thread2.start()                                                                                             # Start it
    price_thread = threading.Thread(target=read_prices, args=(), daemon=True)                                   # Initialize the read price thread
    price_thread.start()                                                                                        # Start it

    
    # Event handler
    while True:
        # Read window event infinitely
        event, values = window.read()

        # ######################################
        # Multi-threading event handler
        # --------------------------------------
        # works well, It receives therad event
        # with the update_dict's content
        # It updates the GUI content
        if event == "-balance-":
           
            # for p in _obj.currencies:                                                                         # check current currencies
            #     window[p].update(f"{float(values[event][p]):.3f}")                                            # Update it's value with the content of new data

            # prices = _obj.client.futures_mark_price()
            # for p in prices:
            #     # window[p].update(f"{float(values[event][p]):.3f}")                                        # Update it's value with the content of new data
            #     if p["symbol"] in _obj.currencies:
            #         if len(price_Buffer[p["symbol"]]) < 300:                                                # If the length of buffer is less than 5 min
            #             price_Buffer[p["symbol"]].append(float(p["markPrice"]))                             # append it
            #         else:       
            #             price_Buffer[p["symbol"]].pop(0)                                                    # Else, remove oldest node
            #             price_Buffer[p["symbol"]].append(float(p["markPrice"]))                             # and, input new node
            
            
            # # Calculate rate of change
            # cur_index = int(values["rate"]) if not values["min_rate"] else int(values["rate"])*60           # Read current rate value
            # pre_list = []   
            # cur_list = []   
            # for p in _obj.currencies:                                                                       # check current currencies
            #     window[p].update(f"{float(values[event][p]):.3f}")                                          # Update it's value with the content of new data
            #     # check validity of buffer data 
            #     if len(price_Buffer[p]) >= cur_index:                                                       # check current buffer length
            #         pre_list.append(price_Buffer[p][-cur_index])                                            # Get the item with current index
            #         cur_list.append(price_Buffer[p][-1])                                                    # Get the latest item

            # # If the data available, calculate percentage
            # if len(pre_list) != 0:                                                                          # If the data is exist
            #     percent = (np.array(cur_list) - np.array(pre_list))/np.array(pre_list) * 100                # Calculate percentage
            #     for i, c in enumerate(_obj.currencies):                                                     # Read current currency item
            #         window[c + str(i)].update("{}%".format(round(percent[i], 2)))                           # Update it's value with the content of new data
            # else:                                                                                           # If there is no data available yet, print  -.--%
            #     for i, c in enumerate(_obj.currencies):                                                     # Read current currency item
            #         window[c + str(i)].update("-.--%")                                                      # Update it's value with the content of new data

            
            # ################################
            # Update Left - Upper visiable item values
            updating=f'{float(values[event]["balance"]):.3f}'                                               # Get the balance vale
            window['balance'].update(updating)                                                              # Update GUI balance
            updating=f'{float(values[event]["totalMarginBalance"]):.3f}'                                    # Get the totalMarginBalance vale
            window['margin'].update(updating)                                                               # Update GUI totalMarginBalance
            updating = f'{float(values[event]["totalMaintMargin"]):.3f}'                                    # Get the totalMaintMargin vale
            window["maintence"].update(updating)                                                            # Update GUI totalMaintMargin
            updating = f'{float(values[event]["totalUnrealizedProfit"]):.3f}'                               # Get the totalUnrealizedProfit vale
            window["PNL"].update(updating)                                                                  # Update GUI totalUnrealizedProfit
            updating = f'{float(values[event]["liquidationPrice"]):.3f}'                                    # Get the liquidationPrice vale
            window["liquidationPrice"].update(updating)                                                     # Update GUI liquidationPrice

            # #########################################
            # Update "Long Total" and "Short total" content
            if all([v in values[event] for v in ["long_total", "short_total"]]):
                updating = f' {float(values[event]["long_total"]):.3f}' \
                    if not pd.isna(values[event]["long_total"]) else "/"                                    # Get the long total vale
                window["long_total"].update(updating)                                                       # Update the content of long text box
                long_color = ("green" if float(updating)>0 else "red") if updating != "/" else "blue"       # Set each color
                window["long_total"].update(background_color=long_color)                                    # Apply color setting

                updating = f'{float(values[event]["short_total"]):.3f}' \
                    if not pd.isna(values[event]["short_total"]) else "/"                                   # If the value of short total is not Nan
                                                                                                            # Set it's value
                window["short_total"].update(updating)                                                      # Update it's content
                short_color = ("green" if float(updating) >= 0 else "red") if updating != "/" else "blue"   # Get color setting
                window["short_total"].update(background_color=short_color)                                  # Update text box into current color
            
            # ##########################################
            # If there is no exists, filling with "/"
            else:
                window["long_total"].update("/")                                                            # Update long_total box into "/"
                window["long_total"].update(background_color="blue")                                        # Set color 
                window["short_total"].update("/")                                                           # Update short_total box into "/"
                window["short_total"].update(background_color="blue")                                       # Set color

            # ##########################################
            # If the "table" event occurs,
            # Paint table with Green & blue colour 
            if "table" in values[event]:                                                                    # If the "table" event occurs,
                update_df = values[event]["table"]                                                          # Get it's value
                if "live" in values[event]:                                                                 # If there is "live" event
                    row_colors = (
                        (idx, "green") if pnl > 0 else (idx, "red") \
                            for idx, pnl in enumerate(update_df.loc[:,"PNL"])                               # Set row color into green or red
                    )
                else:
                    row_colors = ((idx,"blue") for idx in range(len(update_df)))                            # Set row color into blue
                window["_tracker_"].update(values=update_df.values.tolist(), row_colors=row_colors)         # define colors based on sell

        
        # ##################################################
        # 1. API setting event, when the user presses
        # "File/API Setting" tab, then occurs
        # --------------------------------------------------
        # works well
        if event == "API Settings":
            window["apiframe"].update(visible=True)                                                                     # Display API setting
        
        
        # ##################################################
        # 2. Hide current api setting part
        # -------------------------------------------------
        # works well
        if event == "-hideapi-":
            window["apiframe"].update(visible=False)                                                                    # Hidden API setting

        
        # ##################################################
        # 3. If the current user inputs it's own apikey and
        # secret and press save button, then occurs
        # --------------------------------------------------
        # works well
        if event == "-saveapi-":
            key_settings = {"APIKey": values["apikey"], "APISecret": values["apisecret"], "testnet": values["testnet"]} # Read key setting
            json.dump(key_settings, open("utils/keys.conf", "wt"))                                                      # Write current setting
            _obj.client = Client(key_settings["APIKey"], key_settings["APISecret"], testnet=key_settings["testnet"])    # Initialize new object
        
        
        # ##############################################            
        # 5. when the user presses "File/Exit and Save"
        #  tab, it occurs. Save current settings
        if event == "Exit and Save":
            json.dump(values, open("utils/conf.json","wt"))                                                             # Save current conf dict
            _obj.df.to_csv("utils/orders.csv")                                                                          # Save current order 
            window.close()                                                                                              # Close main window
            break                                                                                                       # Break current loop
        
        
        # 7. Exit event
        if event == "Exit" or event == sg.WIN_CLOSED:
            window.close()                                                                                              # Close main window
            break                                                                                                       # Break current loop
        
        
        # ##############################################
        # 9. clear console window, working
        if event == "-clearmulti-":
            window["multi"].update("")                                                                                  # Clear current console
        
        
        # ######################################
        # 13. working : user presses Reset button, occurs
        if event in key_clear:
            key = key_clear[event]                                                                                      # Clear current content
            window[key]('')                                                                                             # Update current text box
        
        
        # ######################################
        # 14. When the user input current Symbol and
        #  press Change button, occurs
        # ---------------------------------------
        # works well
        if event =="-symbol-":
            all_symbols = [s["symbol"] for s in all_symbols_return["symbols"] if s["symbol"][-4:]=="USDT"]              #  and symbol information
            if values["symbol"].upper()+"USDT" in all_symbols:                                                          # Id the user input correctly 
                symb = values["symbol"].upper()                                     
                _obj.conf_dict["symbol"] = (symb + "USDT")                                                              # Update current conf_dict value
                json.dump(values, open("utils/conf.json", "wt"))                                                        # Save current symbol information
                print("Current Symbol: " + symb)                                        
            else:                                                                                                       # else, print wrong message
                window["symbol"].update(_obj.conf_dict["symbol"][:-4])                                                  # restore original symbol
                print("Warning! wrong input, please input correct symbol.")                                             # If it's not correct, print warning message
        
        
        
        # ######################################
        # 16. No more needs to exist, ignored
        if event == "-reverse-":
            # positions = _obj.client.futures_position_information(symbol=_obj.conf_dict["symbol"])
            # if not values["Isolated"] and len(positions)>0 and positions[0]['marginType'] =="cross":
            #     positions = _obj.client.futures_position_information(symbol=_obj.conf_dict["symbol"])
            #     position_amt = float(positions[0]["positionAmt"])
            #     params = {"symbol": _obj.conf_dict["symbol"], "side": "SELL" if position_amt > 0 else "BUY", "type": "MARKET",
            #             "quantity": position_amt*2}
            #     order = _obj.client.futures_create_order(**params)
            #     order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
            #     _obj.df = _obj.df.append(order_df, ignore_index=True)
            #     _obj.df.to_csv("utils/history" + str(time.time()) + ".csv")
            #     _obj.df = _obj.df.iloc[-1,:]
            #     _obj.df.to_csv("utils/orders.csv")
            #     print(f"ORDER {order['orderId']} executed")
            # else:
            #     print("Reverse position only works in cross-mode with an existing open position")
            print("This function is not completed yet.")

        
        # ######################################
        # 19. When the user selects "Market Lock"
        # --------------------------------------
        # works well
        if event == "market_lock":
            if values["market_lock"]:                                                                                       # If market_lock is selected
                window["radio_market"].update(False)                                                                        # fisable current radio
                window["radio_market"].update(disabled=True)                                                                # Disable current radio
            else:
                window["radio_market"].update(disabled=False)                                                               # Else, enable current radio
        
        
        # ######################################
        # 20. When the user clicks "Cancel" button
        # --------------------------------------
        if event in ["-cancel1-", "-cancel2-", "-cancel3-", "-cancel4-", "-cancel5-",]:
            entry_no = event[-2]                                                                                            # Get the current number    
            if entry_no in last_trade_dict:                                                                                 # If it exists
                try:
                    params = {                                                                                              # Make parameter dict
                        "symbol": _obj.conf_dict["symbol"], 
                        "side": "BUY" if last_trade_dict[entry_no][1]=="SELL" else "SELL", 
                        "type": "MARKET",
                        "quantity": last_trade_dict[entry_no][2]
                    }
                    order = _obj.client.futures_create_order(**params)                                                      # Create order
                    print("Order canceled")
                    if len(_obj.df)>0:
                        _obj.df.drop(_obj.df.index[_obj.df["orderId"].eq(last_trade_dict[entry_no][0])], inplace=True)      # if there is exists duplicate, remove it
                    last_trade_dict.pop(entry_no)
                except BinanceAPIException as e:
                    print("Unexpected error:", e.message)                                                                   # If error is occurred, print message
        
        
        # ######################################
        # 21. When the user clicks "Long" or
        #  "Short" button, occurs
        # --------------------------------------
        # 
        if event in ["-long1-", "-long2-", "-long3-","-long4-","-short1-", "-short2-", "-short3-","-short4-"]:
            entry_no = event[-2]                                                                                            # Get the digit
            side = "BUY" if event[1:5] == "long" else "SELL"                                                                # Set the side, "BUY" or "SELL"
            json.dump(values, open("utils/conf.json", "wt"))                                                                # Open the conf.json file
            try:
                _obj.client.futures_change_leverage(symbol=_obj.conf_dict["symbol"], leverage=values["leverage"])           # Change user’s initial leverage of specific symbol market
                marginType = "ISOLATED" if values["Isolated"] else "CROSSED"                                                # Set margin type : "ISOLATED" or "CROSSED"
                _obj.client.futures_change_margin_type(symbol=_obj.conf_dict["symbol"], marginType=marginType)              # Change the margin type for a symbo
            except BinanceAPIException as e:
                if e.code==-4046:                                                                                           # if the exception is 4046
                    pass                                                                                                    # continue current loop
                else:
                    print("Unexpected error:", e.message)                                                                   # else, print error message
            params = {                                                                                                      # Construct current parameter
                "symbol": _obj.conf_dict["symbol"],
                "side": side,
                "quantity": values["qnty" + entry_no],
                "reduceOnly": values["reduce"]
            }
            key, order_type = next((k, v) for k, v in RADIO1_keys.items() if values[k])                                     # we get the selected radio button
            key = "_".join(key.split("_")[1:])                                                                              # Reconstruct key

            
            if not values["market_lock"] and order_type =="MARKET":                                                         # If the market_lock doesn't select & select market
                params["type"] = order_type
                order = _obj.client.futures_create_order(**params)                                                          # Send in a new order
                order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})                                       # Make new dataFrame with updated value
                _obj.df = _obj.df.append(order_df, ignore_index=True)                                                       # Update order dict
                print(f"ORDER {order['orderId']} executed")
                last_trade_dict[entry_no] = [order['orderId'], params["side"], params["quantity"]]
            else:
                if values["market_lock"]:                                                                                   # If the user selects market lock item
                    params["type"]="MARKET"                             
                    order = _obj.client.futures_create_order(**params)                                                      # Send in a new order
                    order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})                                   # Make new dataFrame with updated value
                    _obj.df = _obj.df.append(order_df, ignore_index=True)                                                   # Update order dict
                    print(f"ORDER {order['orderId']} executed")
                    last_trade_dict[entry_no] = [order['orderId'], params["side"], params["quantity"]]
                
                params["type"] = order_type                                                                                 # Update param type with selected item's value
                activation_type = next(k for k in _obj.RADIO2 if values[k])                                                 # Get the activation type : amount, percentage, price
                mark_price = float(next(p["markPrice"] for p in prices if p["symbol"] == _obj.conf_dict["symbol"]))
                
                if activation_type == "price_value":                                                                        # If the user selects "Price" item
                    if values["ap_"+ key]:
                        #the keys our value boxes have the same ending, but different prefix.
                        params["stopPrice"] = values["ap_" + key]                                                           # Update stopPrice value
                elif activation_type == "amount_value":                                                                     # If the user selects "Amount" item
                    if values["ap_" + key]:                             
                        amount = float(values["ap_" + key])                             
                        add = amount if values["check_sign"] else -amount                               
                        params["stopPrice"] = round(amount + mark_price, 4)                                                 # Update stopPrice value
                elif activation_type == "percentage_value":                                                                 # If the user selects "Percentage" item
                    add = (float(values["percentage_" + key])/100) * mark_price                             
                    add = add if values["check_sign"] else -add                             
                    params["stopPrice"] = round((mark_price + add), 2)                                                      # Update stopPrice value

                if order_type == "TRAILING_STOP_MARKET" and "stopPrice" in params:                                          # If the user selects "Trailing" & stopPrice
                    params["activationPrice"] = params["stopPrice"]                                                         # Update activationPrice and pop stopPrice
                    params.pop("stopPrice")                             

                try:                                
                    order = _obj.client.futures_create_order(**params)                                                      # Send in a new order
                    print(f"{order_type} ORDER {order['orderId']} executed")
                except BinanceAPIException as e:
                    print(e.message)
            _obj.df.to_csv("utils/orders.csv")                                                                              # Save current dataFrame 

        # ##########################
        #   Apply Rate Event handler
        if event == "-applyrate-":
            # applyRate_handler(window, values)                                                                             # Apply current rate
            # thread_state = False                                                                                          # Stop current thread
            # thread2.join()
            # print("Succefully applyed!")
            # thread_state = True
            # thread2 = threading.Thread(target=counterdown, args=(window, ), daemon=True)                                  # Restart thread2
            # thread2.start()
            price_Buffer = {i:[] for i in _obj.currencies}                                                                  # Reset current buffer



        # ###########################
        #   Current curriencies's
        #  event handler
        if event in ["-"+c+"-" for c in _obj.currencies] and not values["symbol_lock"]:                                     
            new_currency = event[1:-1]                                                                                      # Get the currency value
            position_info = _obj.client.futures_position_information()
            symbol_position = float(next(p["positionAmt"] for p in position_info if p["symbol"] == _obj.conf_dict["symbol"]))

            params = {}
            params["side"] = "BUY"  if symbol_position<0 else "SELL"
            params["quantity"] = round(abs(symbol_position), 3)
            params["symbol"] = _obj.conf_dict["symbol"]
            params["type"] = "MARKET"
            _obj.df.drop(_obj.df.index, inplace=True)
            if params["quantity"] != 0:
                #we make the opposite trade
                order = _obj.client.futures_create_order(**params)
                while True:
                    try:
                        order_info = _obj.client.futures_get_order(symbol=params["symbol"], orderId=order["orderId"])
                        #we iterate throught the loop until the status is FILLED, meaning the trade was executed.
                        if order_info["status"] == "FILLED":
                            break
                    except BinanceAPIException as e:
                        print(e.message)
                    time.sleep(0.1)

                trades = _obj.client.futures_account_trades()
                trades_df = pd.DataFrame.from_dict(trades)
                trades_df = trades_df.astype({"commission": float, "quoteQty": float})
                commission, val = trades_df.loc[trades_df["orderId"].eq(order_info["orderId"]) ,["commission", "quoteQty"]].sum()
                usdt_amount = abs(val) - commission

                new_price = float(next(p["markPrice"] for p in prices if p["symbol"] == new_currency))

                params["side"] = params["side"] if values["reverse_lock"] else "BUY" if params["side"] =="SELL" else "SELL"
                params["quantity"] = round((usdt_amount/new_price), currency_precision[new_currency])
                params["symbol"] = new_currency
                order = _obj.client.futures_create_order(**params)
                order_df = pd.DataFrame.from_dict({k: [v] for k, v in order.items()})
                _obj.df = _obj.df.append(order_df, ignore_index=True)

            _obj.conf_dict["symbol"] = new_currency
            window["symbol"].update(new_currency[:-4])
            json.dump(values, open("utils/conf.json", "wt"))

            _obj.df.to_csv("utils/orders.csv")

        # #################################
        #   Clear current tracker
        if event == "-cleartracker-":
            df = pd.DataFrame()
            window["_tracker_"].update(values=df.values.tolist())

            

        
        



