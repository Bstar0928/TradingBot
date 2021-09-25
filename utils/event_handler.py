import time
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import No, Window
import json
from binance import Client

# #####################################
#   API setting window
def api_setting(obj):
    layout2 = [                                                                                     # Define new layout2
        [
            sg.pin(
                sg.Frame("API settings", [
                    [
                        sg.Text("API key", size=(10, 1)),                                           # API key input panel
                        sg.Input(size=(70, 1), key="apikey")
                    ],
                    [
                        sg.Text("API Secret", size=(10, 1)),                                        # API secret panel
                        sg.Input(size=(70, 1), key="apisecret")
                    ],
                    [
                        sg.Checkbox("Testnet", key="testnet")                                       # Testnet setting
                    ],
                    [
                        sg.Button("Save keys", key="-saveapi-"),                                    # Save key button
                        sg.Button("Close", key="-hideapi-")                                         # Close botton
                    ]
                ], 
                key="apiframe",), shrink=True
            )
        ],
    ]

    sg.theme_background_color("#555555")
    api_window = sg.Window(title="API Setting", layout=layout2, modal=True)
    while True:
        event, values = api_window.read()
        if event == "Exit" or event == sg.WIN_CLOSED or event == "-hideapi-":
            api_window.close()
            break  
        if event == "-saveapi-":
            if len(values["apikey"]) == 0 or len(values["apisecret"]) == 0:
                print("Warning!, Please input correctly.")
            else:
                key_settings = {"APIKey": values["apikey"], "APISecret": values["apisecret"], "testnet": values["testnet"]} # Read key setting
                json.dump(key_settings, open("utils/keys.conf", "wt"))                                                      # Write current setting
                # obj.client = Client(key_settings["APIKey"], key_settings["APISecret"], testnet=key_settings["testnet"])    # Initialize new object
                print(json.dumps(key_settings, indent=2))




# #####################################
#   Return current rate value into sec
def get_interval(values):
    second = int(values["rate"])
    if not values["min_rate"]:                                              # Set the rate value 5 ~ 59 sec
        if second < 5:
            second = 5
            print("Warning! Please input 5 ~ 59 sec value.")
        elif second > 59:
            second = 59
            print("Warning! Please input 5 ~ 59 sec value.")
        
    else:                                                                   # Set the rate value 1 ~ 5 min
        if second < 1:
            second = 1
            print("Warning! Please input 1 ~ 5 min value.")
        elif second > 5:
            second = 5
            print("Warning! Please input 1 ~ 5 min value.")
        second *= 60
    return second


# ##################################################
#   Update apply rate content
def applyRate_handler(window, values):
    interval = get_interval(values)                                         # Get current rate value into seconds
    if not values["min_rate"]:
        window["rate"].update(interval)                                     # Update current rate into sec
    else:
        window["rate"].update(int(interval / 60))                           # Update current rate into min

    
    