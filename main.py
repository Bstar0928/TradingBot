
from binance import Client
from binance.exceptions import BinanceAPIException
from utils.layout import GUI_object
from utils.process import Process
import threading
import PySimpleGUI as sg
from win10toast import ToastNotifier



# Initialize the key and secret variables
api_key="4qwMmtjwUaA85tiIAGl8ypfnxd4IKp89sOUO9Chpmkf8AwIc0ONgou6QoQISPtrH"
api_secret="9oFz2ym2f2B3KecOlcmhTaZMWWk9O3qTCZgRHtJiqgpisdEK5UyfV5H1B5AV3inM"

# Initialize the several file names
conf_filename = "utils/conf.json" 
order_filename = "utils/orders.csv"
trades_history_filename = "utils/trades_history.csv"



def notification():
    # sg.popup_notify("Successfully Connected to the Binance.", title="Congratulation!",)
    ToastNotifier().show_toast(title="Congratulation!", msg="Successfully Connected to the Binance.")

# ###########################################################
#       Main.py file
# -----------------------------------------------------------
# It makes client instance with key and secret
# and load main - window
if __name__ == "__main__":

    try:
        client = Client(api_key, api_secret)                                                    # Create client instance
    except BinanceAPIException as e:
        print("Binance Exception : ", e.message)
    else:
        obj = GUI_object(client, conf_filename, order_filename, trades_history_filename)        # Create Main window instance
        threading.Thread(target=notification, args=(), daemon=True).start()                     # Create notificatioln
        Process(obj)                                                                            # Process main logic

        



