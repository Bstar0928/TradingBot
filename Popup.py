import PySimpleGUI as sg

# set global options for window
background = '#F0F0F0'
sg.SetOptions(background_color=background,
              element_background_color=background,
              text_element_background_color=background,
              window_location=(0, 0),
              margins=(0, 0),
              text_color='Black',
              input_text_color='Black',
              button_color=('Black', 'gainsboro'))

layout = [[sg.Button('Ok'), sg.Button('Cancel')]]

window = sg.Window('Test Window',
                   layout,
                   grab_anywhere=False,
                   size=(800, 480),
                   return_keyboard_events=True,
                   finalize=True,
                   keep_on_top=True)

# window.Maximize()
window.BringToFront()
while True:
    event, values = window.read()
    if event in (None, 'Cancel'):
        break
    else:
        sg.Popup('Ok clicked', keep_on_top=True)