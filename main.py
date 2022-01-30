import PySimpleGUI as sg
import os
import py7zr

FILE_EXT = '.7z'
FILE_NAME = 'BACKUP_'
FILE_ENU = ''

sg.theme('Dark')   # Add a touch of color


source_list_column = [
    [
        sg.Text("Source Folder"),
        sg.In(size=(25, 1), enable_events=True, key="-SOURCE-"),
        sg.FolderBrowse(),
    ]
]

dest_list_column = [
    [
        sg.Text("Destination Folder"),
        sg.In(size=(25, 1), enable_events=True, key="-DEST-"),
        sg.FolderBrowse(),
    ],
    [sg.Listbox(values=[], enable_events=True, size=(40, 20), key="-BACKUP LIST-")],
]

log_output = [
    [
        sg.Multiline(key='-LOG-', autoscroll=True, disabled=True, size=(100,20))
    ]
]

# ----- Full layout -----
layout = [
    source_list_column,
    dest_list_column,
    [sg.HorizontalSeparator()],
    # [
    #     sg.Column(source_list_column),
    #     sg.VSeperator(),
    #     sg.Column(dest_list_column),
    # ],
    log_output
]


window = sg.Window("Save Manager", layout)


# Run the Event Loop
while True:
    event, values = window.read()
    if event == "Exit" or event == sg.WIN_CLOSED:
        break

    if event == "-SOURCE-":
        source_folder = values["-SOURCE-"]

    elif event == "-DEST-":
        dest_folder = values["-DEST-"]


    elif event == "-BACKUP LIST-":  # A file was chosen from the listbox
        try:
            filename = os.path.join(values["-FOLDER-"], values["-FILE LIST-"][0])
            window["-TOUT-"].update(filename)
            window["-IMAGE-"].update(filename=filename)

        except:
            pass

window.close()
