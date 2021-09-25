import pandas as pd
from win10toast import ToastNotifier
###########     CSV test     #############
"""
update_df = pd.read_csv("training.csv")
# print(update_df.head())


cols = update_df.columns.tolist()
table_column_state = [True for _ in range(len(cols))]
print(cols)
print(table_column_state)
table_column_state[3] = False


item = [cols[i] for i,d in enumerate(table_column_state) if not d]
update_df[item] = ""
print(update_df)
"""

###########     coding test     #############

import PySimpleGUI as sg

event, values = sg.Window('Window Title').Layout([[sg.Input(key='_FILES_'), sg.FilesBrowse()], [sg.OK(), sg.Cancel()]]).Read()

print(values['_FILES_'].split(';'))





# for i,d in enumerate(table_column_state):
#     if not d:
#         update_df[cols[i]] = ""

# print(update_df)

# update_df[update_df_list[i]] = ["" for (i,d) in enumerate(table_column_state) if not d]

# print(update_df[1])
# new_df = pd.DataFrame(columns=cols)


# total_amount = update_df.loc[1:].apply(lambda x:  x["qty"] if x["side"] =="BUY" else x["qty"]*-1, axis=1).sum()
# print(total_amount)

# update_df["commission"] = update_df.groupby(by="orderId")["commission"].cumsum()        # Calculate each colum's sum, mean ...
# update_df["price"] = update_df.groupby(by="orderId")["price"].transform(lambda x: x.mean()) 
# update_df["qty"] = update_df.groupby(by="orderId")["qty"].transform(lambda x: x.sum())  # Calculate each colum's sum, mean ...




"""
    symbol  side   qty   price  commission  Mark Price  Exit Fee       PNL      Trade       orderId
2  XRPUSDT  SELL -10.0  0.9842    0.011810    0.989608  0.011875  0.030396  Close All           NaN
1  XRPUSDT   BUY  10.0  0.9843    0.003937    0.989608  0.003958  0.045185      Close  1.731155e+10
0  XRPUSDT  SELL  20.0  0.9841    0.007873    0.989608  0.007917 -0.125951      Close  1.731155e+10

    symbol  side   qty   price  commission  Mark Price  Exit Fee       PNL      Trade       orderId
1  XRPUSDT  SELL -10.0  0.9893    0.003957    0.989514  0.003958 -0.005780  Close All           NaN
0  XRPUSDT  SELL  10.0  0.9893    0.003957    0.989514  0.003958 -0.010051      Close  1.731202e+10

"""  