import __future__
import PySimpleGUI as sg
import os
import py7zr
import json

sg.theme("Dark")  # Add a touch of color
settings_filename = "./savemanager_settings.json"

def set_layout():
    left_column = [
        [
            sg.Text("Source Folder"),
            sg.In(size=(25, 1), enable_events=True, key="-DEST-"),
            sg.FolderBrowse(),
        ]
    ]

    right_column = [
        [
            sg.Text("Destination Folder"),
            sg.In(size=(25, 1), enable_events=True, key="-SOURCE-"),
            sg.FolderBrowse(),
        ]
    ]

    log_output = [
        [sg.Multiline(key="-LOG-", autoscroll=True, disabled=True, size=(120, 20))] # , font=('Consolas', 7)
    ]

    # ----- Full layout -----
    layout = [
        [
            sg.Column(left_column),
            sg.VSeperator(),
            sg.Column(right_column),
        ],
        [sg.HorizontalSeparator()],
        [sg.Listbox(values=[], enable_events=True, size=(120, 10), key="-BACKUP LIST-")],
        [sg.HorizontalSeparator()],
        # [
        #     sg.Column(source_list_column),
        #     sg.VSeperator(),
        #     sg.Column(dest_list_column),
        # ],
        log_output,
    ]
    return layout

window = sg.Window("Save Manager", set_layout())
window.finalize()

def log(text):
    window['-LOG-'].print(f'{text}\n')

def load_settings(filename=settings_filename):
    log(f'Loading settings from {filename}')
    with open(filename) as infile:
        settings = json.load(infile)
    log(f'{json.dumps(settings, indent=4)}')
    return settings


def save_settings(settings, filename=settings_filename):
    log(f'Saving settings to {filename}')
    with open(filename, "w") as outfile:
        json.dump(settings, outfile, indent=4)
    log(f'{json.dumps(settings, indent=4)}')

def settings_init():
    if os.path.exists(settings_filename):
        settings = load_settings()
    else:
        log('No settings file found, creating default settings...')
        settings = {
            "FILE_EXT": ".7z",
            "FILE_NAME": "BACKUP_",
            "FILE_ENU": "",
            "SOURCE_FOLDER": "./",
            "DEST_FOLDER": "./",
        }
        save_settings(settings)
    return settings


def main():
    settings = settings_init()

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


if __name__ == '__main__':
    main()