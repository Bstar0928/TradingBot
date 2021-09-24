

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

    
    