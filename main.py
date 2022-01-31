import __future__
import PySimpleGUI as sg
import os
import py7zr
import json
from datetime import datetime


def set_layout():
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
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Listbox(
                values=[], enable_events=True, size=(120, 10), key="-BACKUP LIST-"
            )
        ],
        [sg.HorizontalSeparator()],
        source,
        dest,
        [sg.HorizontalSeparator()],
        log_output,
    ]
    return layout


# sg.theme("Dark")  # Add a touch of color
sg.ChangeLookAndFeel("Dark")  # Add a touch of color
settings_filename = "./savemanager_settings.json"
window = sg.Window("Save Manager", set_layout())
window.Font = ("Consolas", 8)
window.finalize()


def now():
    return datetime.now().strftime("%H:%M:%S")


def log(text):
    window["-LOG-"].print(f"{now()} | {text}")
    window["-LOG-"].update()


def load_settings(filename=settings_filename):
    log(f"Loading settings from {filename}")
    with open(filename) as infile:
        settings = json.load(infile)
    log(f"SETTINGS = \n{json.dumps(settings, indent=4)}")
    return settings


def save_settings(settings, filename=settings_filename):
    log(f"Saving settings to {filename}")
    with open(filename, "w") as outfile:
        json.dump(settings, outfile, indent=4)
    log(f"SETTINGS = \n{json.dumps(settings, indent=4)}")


def settings_init():
    if os.path.exists(settings_filename):
        settings = load_settings()
    else:
        log("No settings file found, creating default settings...")
        settings = {
            "FILE_EXT": ".7z",
            "FILE_NAME": "BACKUP_",
            "FILE_ENU": "",
            "SOURCE_FOLDER": "./",
            "DEST_FOLDER": "./",
        }
        save_settings(settings)
    return settings


def create_backup(settings):
    log("\nStarted backup...")
    with py7zr.SevenZipFile(add_new_backup(settings), "w", ) as outfile:
        outfile.writeall(settings['SOURCE_FOLDER'])


def get_files_from_path(settings) -> list:
    result = []
    for subdir, dirs, files in os.walk(settings["DEST_FOLDER"]):
        for fname in files:
            filepath = f"{subdir}{os.sep}{fname}"
            if fname.lower().endswith(settings["FILE_EXT"].lower()) and fname.startswith(settings["FILE_NAME"]):
                result.append(filepath)
    if len(result) > 0:
        return result.sort()
    else:
        return [f"{settings['DEST_FOLDER']}{os.sep}{settings['FILE_NAME']}0{settings['FILE_EXT']}"]


def inc_filename(filename: str) -> str:
    # using my own answer from SO::
    ## https://stackoverflow.com/a/69054013/9267296
    if "." in filename:
        # set extension
        extension = f""".{filename.split(".")[-1]}"""
        # remove extension from filename
        filename = ".".join(filename.split(".")[:-1])
    else:
        # set extension to empty if not included
        extension = ""
    try:
        # try to set the number
        # it will throw a ValueError if it doesn't have _1
        number = int(filename.split("_")[-1]) + 1
        newfilename = "_".join(filename.split("_")[:-1])
    except ValueError:
        # catch the ValueError and set the number to 1
        number = 1
        newfilename = "_".join(filename.split("_"))
    return f"{newfilename}_{number}{extension}"


def add_new_backup(settings):
    filelist = get_files_from_path(settings)
    return inc_filename(filelist[-1])


def main():
    settings = settings_init()
    window["-SOURCE-"].update(settings["SOURCE_FOLDER"])
    window["-DEST-"].update(settings["DEST_FOLDER"])

    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        elif event == "-BACKUP-":
            # create BACKUP
            create_backup(settings)

        elif event == "-RESTORE-":
            # restore previous backupp
            pass

        elif event == "-EVENTGOESHERE-":
            pass

        elif event == "-EVENTGOESHERE-":
            pass

        elif event == "-SOURCE-":
            # set SOURCE folder
            settings["SOURCE_FOLDER"] = values["-SOURCE-"]
            save_settings(settings)

        elif event == "-DEST-":
            # set DEST folder
            settings["DEST_FOLDER"] = values["-DEST-"]
            save_settings(settings)

        elif event == "-BACKUP LIST-":  # A file was chosen from the listbox
            try:
                filename = os.path.join(values["-FOLDER-"], values["-FILE LIST-"][0])
                window["-TOUT-"].update(filename)
                window["-IMAGE-"].update(filename=filename)

            except:
                pass

    window.close()


if __name__ == "__main__":
    main()
