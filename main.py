from xmlrpc.client import Boolean
import PySimpleGUI as sg
import os
import py7zr
import json
from datetime import datetime
import time
from shutil import copytree, rmtree
from eakse.common import dump_args
from eakse.quickcopy import FastCopy


path_7zip = r"C:/Program Files/7-Zip/7z.exe"
path_working = r"C:/###VS Projects/###TMP"
slow_log_str = ""
slow_log_cnt = 0
slow_log_interval = 30
progress_cnt = 0
progress_max = 0


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
    make_backup = [[sg.Checkbox('CREATE BACKUP', default=True, key="-MAKE_BACKUP-")]]


    log_output = [
        [
            sg.Multiline(
                key="-LOG-",
                autoscroll=True,
                disabled=True,
                size=(120, slow_log_interval+1),
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
            sg.Column(make_backup),
            sg.VSeparator(),
            sg.Column(info)
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Listbox(
                values=[],
                enable_events=True,
                size=(120, 10),
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
settings_filename = "./savemanager_settings.json"
window = sg.Window("Save Manager", set_layout())
window.Font = ("Consolas", 8)
window.finalize()


@dump_args
def now():
    return datetime.now().strftime("%H:%M:%S")


@dump_args
def log(text, debug=False):
    if debug == False or (debug == True and settings['SHOW_DEBUG'] == True):
        lines = text.split("\n")
        window["-LOG-"].print(f"{now()} | {lines[0]}")
        for line in lines[1:]:
            window["-LOG-"].print(f"         | {line}")
        window["-LOG-"].update()
        window.refresh()


def slow_log(text):
    global slow_log_str
    global slow_log_cnt
    slow_log_cnt += 1
    if slow_log_str == '':
        slow_log_str = text
    else:
        slow_log_str = f"{slow_log_str}\n{text}"
    if slow_log_cnt == slow_log_interval:
        slow_log_cnt = 0
        log(slow_log_str)
        slow_log_str = ''


@dump_args
def sizeof_fmt(num, suffix="B"):
    # https://stackoverflow.com/a/1094933/9267296
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


@dump_args
def update_size():
    size = 0
    for path, dirs, files in os.walk(settings['SOURCE_FOLDER']):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    window['-SIZE-'].update(f'Folder size: {sizeof_fmt(size)}')


@dump_args
def load_settings(filename=settings_filename):
    global settings
    log(f"Loading settings from {filename}")
    with open(filename) as infile:
        settings = json.load(infile)
    log('------------------------------------------------------------------------------------------------------------------------')
    # log(f"SETTINGS = \n{json.dumps(settings, indent=4)}")


@dump_args
def save_settings(filename=settings_filename):
    log(f"Saving settings to {filename}")
    with open(filename, "w") as outfile:
        json.dump(settings, outfile, indent=4)
    log('------------------------------------------------------------------------------------------------------------------------')
    # log(f"SETTINGS = \n{json.dumps(settings, indent=4)}")


@dump_args
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
            "SHOW_DEBUG": True,
            "X_POS": 0,
            "Y_POS": 0,
            "SAFETY_BACKUP": "SAFETY_BACKUP.7z"
        }
        save_settings()


@dump_args
def create_backup(filename, extralog=""):
    logstr = "Starting backup, application might freeze a bit..."
    rootdir = os.path.basename(settings["SOURCE_FOLDER"])
    dirname = os.path.normpath(rootdir)
    directory = f'./TMP_savemanager/{dirname}'
    #create dirs to be safe
    os.makedirs(rootdir, exist_ok=True)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if extralog != "":
        logstr = extralog + "\n" + logstr
    log(logstr)
    log("Making TMP copy of existing directory.")
    copytree(settings["SOURCE_FOLDER"], directory)
    log("Done.\nCreating 7z file...")
    # directory = settings["SOURCE_FOLDER"]
    with py7zr.SevenZipFile(filename, "w") as archive:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                parentpath = os.path.relpath(filepath, directory)
                arcname = os.path.join(rootdir, parentpath)
                slow_log(f"Adding: {filepath}")
                archive.write(filepath, arcname)
    log("Done.\nRemoving TMP copy.")
    rmtree(directory)
    log("Done")
    get_current_backups()


@dump_args
def add_new_backup():
    newbackupname = increase(get_current_highest())
    start = time.time()
    create_backup(
        f"{settings['DEST_FOLDER']}{os.sep}{newbackupname}",
        extralog=f"Creating new backup with filename:\n  {newbackupname}",
    )
    log(f"Backup done.\nTime elapsed: {time.time()-start:.2f} seconds")


@dump_args
def restore_backup(filename: str, do_backup: bool):
    start = time.time()
    if os.path.exists(filename):
        if do_backup:
            if os.path.exists(f"{settings['DEST_FOLDER']}{os.sep}{settings['SAFETY_BACKUP']}"):
                os.remove(f"{settings['DEST_FOLDER']}{os.sep}{settings['SAFETY_BACKUP']}")
            create_backup(f"{settings['DEST_FOLDER']}{os.sep}{settings['SAFETY_BACKUP']}", extralog=f'Creating safety backup: {settings["SAFETY_BACKUP"]}')
        else:
            log("Skipping safety backup.")
    else:
        log(f"File: {filename} not found.")
        return
    log(f"Deleting existing directory: {settings['SOURCE_FOLDER']}")
    # print(f"Deleting existing directory: {settings['SOURCE_FOLDER']}")
    # exit(0)
    try:
        rmtree(settings['SOURCE_FOLDER'])
    except Exception as e:
        log(e)
    log(f"Restoring backup: {filename}")
    old_cwd = os.getcwd()
    os.chdir(f"{settings['SOURCE_FOLDER']}{os.sep}..")
    # print(os.getcwd())
    with py7zr.SevenZipFile(f"{filename}", 'r') as archive:
        archive.extractall()
    log(f"Backup restored.\nTime elapsed: {time.time()-start:.2f} seconds")
    os.chdir(old_cwd)




@dump_args
def get_current_backups() -> list:
    result = [
        filename
        for filename in next(os.walk(settings["DEST_FOLDER"]), (None, None, []))[2]
        if (
            filename.startswith(settings["FILE_NAME"])
            and filename.lower().endswith(settings["FILE_EXT"].lower())
        )
    ]
    result.sort(reverse=True)
    if os.path.exists(f"{settings['DEST_FOLDER']}{os.sep}{settings['SAFETY_BACKUP']}"):
        result.insert(0, settings['SAFETY_BACKUP'])
    window["-BACKUP LIST-"].update(result)
    update_size()
    window.refresh()
    return result


@dump_args
def get_number(filename: str) -> int:
    return filename.split(settings["FILE_NAME"])[1].split(settings["FILE_EXT"])[0]


@dump_args
def increase(filename: str) -> str:
    nr = 1 + int(
        filename.split(settings["FILE_NAME"])[1].split(settings["FILE_EXT"])[0]
    )
    return f"{filename.split(settings['FILE_NAME'])[0]}{settings['FILE_NAME']}{nr:03}{settings['FILE_EXT']}"


@dump_args
def get_current_highest() -> str:
    highest = f"{settings['FILE_NAME']}-1{settings['FILE_EXT']}"
    filelist = get_current_backups()
    if settings['SAFETY_BACKUP'] in filelist:
        filelist.remove(settings['SAFETY_BACKUP'])
    for filename in filelist:
        if get_number(filename) > get_number(highest):
            highest = filename
    return highest


@dump_args
def main():
    global settings
    settings_init()
    window["-SOURCE-"].update(settings["SOURCE_FOLDER"])
    window["-DEST-"].update(settings["DEST_FOLDER"])
    get_current_backups()
    # window.current_location((settings['X_POS'], settings['Y_POS']))

    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            # settings['X_POS'] = window.current_location()[0]
            # settings['Y_POS'] = window.current_location()[1]
            break

        elif event == "-BACKUP-":
            # create BACKUP
            add_new_backup()
            log('------------------------------------------------------------------------------------------------------------------------')

        elif event == "-RESTORE-":
            # restore previous backup
            file = sg.popup_get_file("Select backup to restore", initial_folder=settings['DEST_FOLDER'], no_window=True)#, file_types=settings['FILE_EXT']
            restore_backup(file, values["-MAKE_BACKUP-"]) 
            log('------------------------------------------------------------------------------------------------------------------------')

        elif event == "-RESTORE_LATEST-":
            restore_backup(f"{settings['DEST_FOLDER']}{os.sep}{get_current_highest()}", values["-MAKE_BACKUP-"])
            log('------------------------------------------------------------------------------------------------------------------------')
            
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
