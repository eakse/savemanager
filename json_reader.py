import json
import PySimpleGUI as sg
import os
from .eakse.common import dump_args


def set_layout():
    info = [
        [
            sg.Text('', key='-SIZE-', auto_size_text=True),

        ]
    ]

    source = [
        [
            sg.Text("Source Folder     "),
            sg.In(size=(40, 1), enable_events=True, key="-SOURCE-"),
            sg.FolderBrowse(),
        ]
    ]

    dest = [
        [
            sg.Text("Destination Folder"),
            sg.In(size=(40, 1), enable_events=True, key="-DEST-"),
            sg.FolderBrowse(),
        ]
    ]

    backup = [[sg.Button("BACKUP", enable_events=True, key="-BACKUP-")]]

    restore = [[sg.Button("RESTORE", enable_events=True, key="-RESTORE-")]]
    restore_latest = [[sg.Button("RESTORE LATEST", enable_events=True, key="-RESTORE_LATEST-")]]

    log_output = [
        [
            sg.Multiline(
                key="-LOG-",
                autoscroll=True,
                disabled=True,
                size=(120, 20),
            )
        ]
    ]

    # ----- Full layout -----
    layout = [
        [
            sg.Column(backup),
            sg.VSeperator(),
            sg.Column(restore),
            sg.VSeparator(),            
            sg.Column(restore_latest),
            sg.VSeparator(),
            sg.Column(info)
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Listbox(
                values=[],
                enable_events=True,
                size=(120, 20),
                key="-BACKUP LIST-",
                # autoscroll=True,
            )
        ],
        [sg.HorizontalSeparator()],
        source,
        dest,
        [sg.HorizontalSeparator()],
        log_output,
    ]
    return layout


settings = {}
sg.ChangeLookAndFeel("Black")
settings_filename = "./json_reader_settings.json"
window = sg.Window("JSON Browser", set_layout())
window.Font = ("Consolas", 8)
window.finalize()


