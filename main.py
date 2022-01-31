import __future__
from ast import dump
from msilib.schema import Directory
import PySimpleGUI as sg
import os
import py7zr
import json
from datetime import datetime
import time
import inspect


def dump_args(func):
    """
    Decorator to print function call details.

    This includes parameters names and effective values.
    """

    def wrapper(*args, **kwargs):
        func_args = inspect.signature(func).bind(*args, **kwargs).arguments
        func_args_str = ", ".join(map("{0[0]} = {0[1]!r}".format, func_args.items()))
        print(f"{func.__module__}.{func.__qualname__} ( {func_args_str} )")
        return func(*args, **kwargs)

    return wrapper


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
settings = {}
sg.ChangeLookAndFeel("Black")  # Add a touch of color
settings_filename = "./savemanager_settings.json"
window = sg.Window("Save Manager", set_layout())
window.Font = ("Consolas", 8)
window.finalize()


# @dump_args
def now():
    return datetime.now().strftime("%H:%M:%S")


# @dump_args
def log(text):
    lines = text.split("\n")
    window["-LOG-"].print(f"{now()} | {lines[0]}")
    for line in lines[1:]:
        window["-LOG-"].print(f"         | {line}")
    window["-LOG-"].update()
    window.refresh()


# @dump_args
def load_settings(filename=settings_filename):
    global settings
    log(f"Loading settings from {filename}")
    with open(filename) as infile:
        settings = json.load(infile)
    # log(f"SETTINGS = \n{json.dumps(settings, indent=4)}")


# @dump_args
def save_settings(filename=settings_filename):
    log(f"Saving settings to {filename}")
    with open(filename, "w") as outfile:
        json.dump(settings, outfile, indent=4)
    # log(f"SETTINGS = \n{json.dumps(settings, indent=4)}")


# @dump_args
def settings_init():
    if os.path.exists(settings_filename):
        load_settings()
    else:
        global settings
        log("No settings file found, creating default settings...")
        settings = {
            "FILE_EXT": ".7z",
            "FILE_NAME": "BACKUP_",
            "FILE_ENU": "",
            "SOURCE_FOLDER": "./",
            "DEST_FOLDER": "./",
        }
        save_settings()


# @dump_args
def create_backup(filename, extralog=""):
    logstr = "Starting backup, application might freeze a bit..."
    if extralog != "":
        logstr = extralog + "\n" + logstr
    log(logstr)
    directory = settings["SOURCE_FOLDER"]
    with py7zr.SevenZipFile(filename, "w") as outfile:
        rootdir = os.path.basename(directory)
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                parentpath = os.path.relpath(filepath, directory)
                arcname = os.path.join(rootdir, parentpath)
                # log(f"Adding: {filepath}")
                outfile.write(filepath, arcname)
    get_current_backups()


# @dump_args
def add_new_backup():
    newbackupname = increase(get_current_highest())
    start = time.time()
    create_backup(
        f"{settings['DEST_FOLDER']}{os.sep}{newbackupname}",
        extralog=f"Creating new backup with filename:\n  {newbackupname}",
    )
    log(f"Backup done.\nTime elapsed: {time.time()-start:.2f} seconds")


# @dump_args
def get_current_backups() -> list:
    result = [
        filename
        for filename in next(os.walk(settings["DEST_FOLDER"]), (None, None, []))[2]
        if (
            filename.startswith(settings["FILE_NAME"])
            and filename.lower().endswith(settings["FILE_EXT"].lower())
        )
    ]
    window["-BACKUP LIST-"].update(result)
    window.refresh()
    return result


# @dump_args
def get_number(filename: str) -> int:
    return filename.split(settings["FILE_NAME"])[1].split(settings["FILE_EXT"])[0]


# @dump_args
def increase(filename: str) -> str:
    nr = 1 + int(
        filename.split(settings["FILE_NAME"])[1].split(settings["FILE_EXT"])[0]
    )
    return f"{filename.split(settings['FILE_NAME'])[0]}{settings['FILE_NAME']}{nr}{settings['FILE_EXT']}"


# @dump_args
def get_current_highest() -> str:
    highest = f"{settings['FILE_NAME']}-1{settings['FILE_EXT']}"
    for filename in get_current_backups():
        if get_number(filename) > get_number(highest):
            highest = filename
    return highest


# @dump_args
def main():
    global settings
    settings_init()
    window["-SOURCE-"].update(settings["SOURCE_FOLDER"])
    window["-DEST-"].update(settings["DEST_FOLDER"])
    get_current_backups()

    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        elif event == "-BACKUP-":
            # create BACKUP
            add_new_backup()

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
            save_settings()

        elif event == "-DEST-":
            # set DEST folder
            settings["DEST_FOLDER"] = values["-DEST-"]
            save_settings()

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
