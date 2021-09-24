import ctypes


# Check the current User's rights
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


print(is_admin())