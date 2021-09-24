
from binance import Client
from binance.exceptions import BinanceAPIException
from utils.layout import GUI_object
from utils.process import Process




# Initialize the key and secret variables
api_key="4qwMmtjwUaA85tiIAGl8ypfnxd4IKp89sOUO9Chpmkf8AwIc0ONgou6QoQISPtrH"
api_secret="9oFz2ym2f2B3KecOlcmhTaZMWWk9O3qTCZgRHtJiqgpisdEK5UyfV5H1B5AV3inM"

# Initialize the several file names
conf_filename = "utils/conf.json" 
order_filename = "utils/orders.csv"
trades_history_filename = "utils/trades_history.csv"

# ###########################################################
#       Main.py file
# -----------------------------------------------------------
# It makes client instance with key and secret
# and load main - window
if __name__ == "__main__":

    # Main 
    client = Client(api_key, api_secret)                                                    # Create client instance
    obj = GUI_object(client, conf_filename, order_filename, trades_history_filename)        # Create Main window instance
    Process(obj)



