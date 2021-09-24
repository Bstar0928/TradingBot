
#!/usr/bin/python3
import threading
import time
import PySimpleGUI as sg
from PySimpleGUI.PySimpleGUI import No


total = 100     # number of units that are used with the progress bar
message = ''    # used by thread to send back a message to the main thread
progress = 0    # current progress up to a maximum of "total"


def long_operation_thread(seconds, stop):
    global message, progress

    print('Thread started - will sleep for {} seconds'.format(seconds))
    for i in range(int(seconds * 10)):
        time.sleep(.1)  # sleep for a while
        progress += total / (seconds * 10)
        print(progress)
        if stop():
            break

    message = f'*** The thread says.... "I am finished" ***'

def the_gui():
    global message, progress

    sg.theme('Light Brown 3')

    layout = [[sg.Text('Long task to perform example')],
              [sg.Text('Number of seconds your task will take'),
               sg.Input(key='-SECONDS-', size=(5, 1)),
               sg.Button('Do Long Task', bind_return_key=True),
               sg.CBox('ONE chunk, cannot break apart', key='-ONE CHUNK-')],
              [sg.Text('Work progress'), sg.ProgressBar(total, size=(20, 20), orientation='h', key='-PROG-')],
              [sg.Button('Click Me'), sg.Button('Exit')], ]
    layout1 = [[sg.Text('Long task to perform example')],
                  [sg.Text('Number of seconds your task will take'),
                   sg.Input(key='-SECONDS-', size=(5, 1)),
                   sg.Button('Do Long Task', bind_return_key=True),
                   sg.CBox('ONE chunk, cannot break apart', key='-ONE CHUNK-')],
                  [sg.Text('Work progress'), sg.ProgressBar(total, size=(20, 20), orientation='h', key='-PROG-')],
                  [sg.Button('Click Me'), sg.Button('Exit')], ]

    window = sg.Window('Multithreaded Demonstration Window', layout)

    thread = None

    # --------------------- EVENT LOOP ---------------------
    while True:
        event, values = window.read()
        if event in (None, 'Exit'):
            state = True
            # thread.join(timeout=1)
            window.close()
            break
        if event.startswith('Do') and not thread:
            print('Thread Starting! Long work....sending value of {} seconds'.format(float(values['-SECONDS-'])))
            state = False
            # thread = threading.Thread(target=long_operation_thread, args=(float(values['-SECONDS-']),), daemon=True)
            thread = threading.Thread(target=long_operation_thread, args=(float(values['-SECONDS-']), lambda:state, ))
            thread.start()
        if event == 'Click Me':
            print('Your GUI is alive and well')
            print(values)
            # window.write_event_value("-test-", None)

        if thread:                                          # If thread is running
            if values['-ONE CHUNK-']:                       # If one big operation, show an animated GIF
                sg.popup_animated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', transparent_color='white', time_between_frames=100)
            else:                                           # Not one big operation, so update a progress bar instead
                window['-PROG-'].update_bar(progress, total)
            
            if not thread.is_alive():                       # the thread finished
                print(f'message = {message}')
                sg.popup_animated(None)                     # stop animination in case one is running
                thread, message, progress = None, '', 0     # reset variables for next run
                window['-PROG-'].update_bar(0,0)            # clear the progress bar
        if event == "-test-":
            print("test")

    window.close()


if __name__ == '__main__':
    the_gui()
    print('Exiting Program')