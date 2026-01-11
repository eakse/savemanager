import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import os
import py7zr
import json
from datetime import datetime
import time
import subprocess
from shutil import copytree, rmtree
from eakse.common import dump_args
from eakse.theme import apply_dark_theme


path_7zip = "" 
path_working = ""
slow_log_str = ""
slow_log_cnt = 0
slow_log_interval = 30
progress_cnt = 0
progress_max = 0


settings = {}
settings_filename = "./savemanager_settings.json"
# tkinter widgets
root = tk.Tk()
src_var = tk.StringVar()
dest_var = tk.StringVar()
app_path_var = tk.StringVar()
make_backup_var = tk.BooleanVar(value=True)
log_text = None
size_label = None
backups_listbox = None
run_app_btn = None
initializing = True



def create_gui():
    """Create the tkinter GUI and wire event handlers to wrapper functions."""
    global root, src_var, dest_var, app_path_var, make_backup_var, log_text, size_label, backups_listbox, run_app_btn

    root.title("Save Manager")
    try:
        result = apply_dark_theme(root)
        if result:
            log(result)
    except Exception:
        pass
    # Set default position from settings if present
    try:
        x = settings.get('X_POS', 0)
        y = settings.get('Y_POS', 0)
        root.geometry(f"+{x}+{y}")
    except Exception:
        pass

    # Top controls: Backup / Restore / Restore Latest / Create Backup checkbox / Size info
    top_frame = ttk.Frame(root)
    top_frame.pack(fill='x', padx=6, pady=6)

    backup_btn = ttk.Button(top_frame, text="BACKUP", command=on_backup)
    backup_btn.pack(side='left', padx=(0, 6))

    restore_btn = ttk.Button(top_frame, text="RESTORE", command=on_restore)
    restore_btn.pack(side='left', padx=(0, 6))

    restore_latest_btn = ttk.Button(top_frame, text="RESTORE LATEST", command=on_restore_latest)
    restore_latest_btn.pack(side='left', padx=(0, 6))

    make_backup_cb = ttk.Checkbutton(top_frame, text='CREATE BACKUP', variable=make_backup_var)
    make_backup_cb.pack(side='left', padx=(0, 6))

    # Run APP button moved to top-right, disabled by default; it will be enabled when a valid executable path is set.
    run_app_btn = ttk.Button(top_frame, text="RUN APP", command=on_run_app, state='disabled')
    run_app_btn.pack(side='right', padx=(6, 0))

    size_label = ttk.Label(top_frame, text='')
    size_label.pack(side='right')

    # Initialize run_app_btn state based on saved settings
    try:
        app_path = settings.get('APP_PATH')
        if app_path and os.path.exists(app_path) and os.access(app_path, os.X_OK):
            run_app_btn.config(state='normal')
        else:
            run_app_btn.config(state='disabled')
    except Exception:
        run_app_btn.config(state='disabled')

    # Backups list
    list_frame = ttk.Frame(root)
    list_frame.pack(fill='both', expand=False, padx=6)
    backups_listbox = tk.Listbox(list_frame, height=10, width=120)
    backups_listbox.pack(side='left', fill='x', expand=True)
    scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=backups_listbox.yview)
    scrollbar.pack(side='right', fill='y')
    backups_listbox.config(yscrollcommand=scrollbar.set)
    backups_listbox.bind('<Double-Button-1>', on_backup_double_click)
    # Apply dark styling to listbox (unselected background & selection colors)
    try:
        root._apply_dark_style(backups_listbox) # type: ignore
        backups_listbox.config(selectbackground='#0e639c', selectforeground='#ffffff')
    except Exception:
        backups_listbox.config(bg='#252526', fg='#d4d4d4', selectbackground='#0e639c', selectforeground='#ffffff')

    # Source / Destination / APP entries
    io_frame = ttk.Frame(root)
    io_frame.pack(fill='x', padx=6, pady=6)

    ttk.Label(io_frame, text='Source Folder').grid(row=0, column=0, sticky='w')
    src_entry = ttk.Entry(io_frame, textvariable=src_var, width=60)
    src_entry.grid(row=0, column=1, sticky='w')
    src_browse = ttk.Button(io_frame, text='Browse', command=on_browse_source)
    src_browse.grid(row=0, column=2, padx=(6,0))

    ttk.Label(io_frame, text='Destination Folder').grid(row=1, column=0, sticky='w')
    dest_entry = ttk.Entry(io_frame, textvariable=dest_var, width=60)
    dest_entry.grid(row=1, column=1, sticky='w')
    dest_browse = ttk.Button(io_frame, text='Browse', command=on_browse_dest)
    dest_browse.grid(row=1, column=2, padx=(6,0))

    ttk.Label(io_frame, text='Executable').grid(row=2, column=0, sticky='w')
    app_entry = ttk.Entry(io_frame, textvariable=app_path_var, width=60)
    app_entry.grid(row=2, column=1, sticky='w')
    app_browse = ttk.Button(io_frame, text='Browse', command=on_select_app)
    app_browse.grid(row=2, column=2, padx=(6,0))

    # Log output
    log_frame = ttk.Frame(root)
    log_frame.pack(fill='both', expand=True, padx=6, pady=(0,6))
    log_text = scrolledtext.ScrolledText(log_frame, height=slow_log_interval+1, wrap='word', state='disabled')
    log_text.pack(fill='both', expand=True)
    try:
        root._apply_dark_style(log_text) # type: ignore
    except Exception:
        log_text.config(bg='#3c3c3c', fg='#d4d4d4', insertbackground='#d4d4d4')

    # When entries change, update settings
    def on_src_changed(*args):
        settings['SOURCE_FOLDER'] = src_var.get()
        if initializing:
            return
        save_settings()

    def on_dest_changed(*args):
        settings['DEST_FOLDER'] = dest_var.get()
        if initializing:
            return
        save_settings()

    def on_app_changed(*args):
        settings['APP_PATH'] = app_path_var.get()
        if initializing:
            # still update run button state even during init
            try:
                path = app_path_var.get()
                if run_app_btn is not None:
                    run_app_btn.config(state='normal' if path and os.path.exists(path) and os.access(path, os.X_OK) else 'disabled')
            except Exception:
                pass
            return
        save_settings()
        try:
            path = app_path_var.get()
            if run_app_btn is not None:
                run_app_btn.config(state='normal' if path and os.path.exists(path) and os.access(path, os.X_OK) else 'disabled')
        except Exception:
            pass

    src_var.trace_add('write', on_src_changed)
    dest_var.trace_add('write', on_dest_changed)
    app_path_var.trace_add('write', on_app_changed)

    # Close handler
    def on_close():
        try:
            geom = root.winfo_geometry()
            # geometry looks like 'WxH+X+Y'
            if '+' in geom:
                parts = geom.split('+')
                settings['X_POS'] = int(parts[1])
                settings['Y_POS'] = int(parts[2])
                save_settings()
        except Exception:
            pass
        root.destroy()

    root.protocol('WM_DELETE_WINDOW', on_close)


# Wrapper event handlers -------------------------------------------------

def on_browse_source():
    folder = filedialog.askdirectory(initialdir=settings.get('SOURCE_FOLDER', './'))
    if folder:
        src_var.set(folder)


def on_browse_dest():
    folder = filedialog.askdirectory(initialdir=settings.get('DEST_FOLDER', './'))
    if folder:
        dest_var.set(folder)


def on_select_app():
    filename = filedialog.askopenfilename(title='Select executable',
                                          initialdir=os.path.dirname(settings.get('APP_PATH', '')) if settings.get('APP_PATH') else settings.get('SOURCE_FOLDER', './'))
    if filename:
        app_path_var.set(filename)
        log(f"Selected executable: {filename}")


def on_run_app():
    path = settings.get('APP_PATH', '')
    if not path:
        log('No executable selected. Please select an executable first.')
        return
    if not os.path.exists(path):
        log(f'Executable not found: {path}')
        try:
            if run_app_btn is not None:
                run_app_btn.config(state='disabled')
        except Exception:
            pass
        return
    if not os.access(path, os.X_OK):
        log(f'File is not executable: {path}')
        try:
            if run_app_btn is not None:
                run_app_btn.config(state='disabled')
        except Exception:
            pass
        return
    try:
        subprocess.Popen([path])  # start separate process
        log(f'Started executable: {path}')
    except Exception as e:
        log(f'Error starting executable: {e}')


def on_backup():
    # Ensure settings reflect entries
    settings['SOURCE_FOLDER'] = src_var.get()
    settings['DEST_FOLDER'] = dest_var.get()
    save_settings()
    add_new_backup()
    log('----------------------------------------------------------------------------------------------------------------------')


def on_restore():
    filename = filedialog.askopenfilename(initialdir=settings.get('DEST_FOLDER', './'), title='Select backup to restore')
    if filename:
        restore_backup(filename, make_backup_var.get())
        log('----------------------------------------------------------------------------------------------------------------------')


def on_restore_latest():
    restore_backup(f"{settings['DEST_FOLDER']}{os.sep}{get_current_highest()}", make_backup_var.get())
    log('----------------------------------------------------------------------------------------------------------------------')


def on_backup_double_click(event=None):
    sel = backups_listbox.curselection() # type: ignore
    if not sel:
        return
    filename = backups_listbox.get(sel[0]) # type: ignore
    # if it's the safety backup, use full path
    fullpath = f"{settings['DEST_FOLDER']}{os.sep}{filename}"
    restore_backup(fullpath, make_backup_var.get())
    log('----------------------------------------------------------------------------------------------------------------------')



@dump_args
def now():
    return datetime.now().strftime("%H:%M:%S")


@dump_args
def log(text, debug=False):
    if not debug or (debug and settings.get('SHOW_DEBUG')):
        lines = text.split("\n")
        timestamp = now()
        if log_text is None:
            # Fallback to printing to stdout
            print(f"{timestamp} | {lines[0]}")
            for line in lines[1:]:
                print(f"         | {line}")
            return
        log_text.config(state='normal')
        log_text.insert(tk.END, f"{timestamp} | {lines[0]}\n")
        for line in lines[1:]:
            log_text.insert(tk.END, f"         | {line}\n")
        log_text.see(tk.END)
        log_text.config(state='disabled')
        try:
            root.update()
        except Exception:
            pass


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
    txt = f'Folder size: {sizeof_fmt(size)}'
    if size_label is not None:
        size_label.config(text=txt)
    else:
        print(txt)


@dump_args
def load_settings(filename=settings_filename):
    global settings
    log(f"Loading settings from {filename}")
    with open(filename) as infile:
        settings = json.load(infile)
    log('----------------------------------------------------------------------------------------------------------------------')
    # log(f"SETTINGS = \n{json.dumps(settings, indent=4)}")


@dump_args
def save_settings(filename=settings_filename):
    log(f"Saving settings to {filename}")
    with open(filename, "w") as outfile:
        json.dump(settings, outfile, indent=4)
    log('----------------------------------------------------------------------------------------------------------------------')
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
            "APP_PATH": "",
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
    try:
        copytree(settings["SOURCE_FOLDER"], directory)
        # directory = settings["SOURCE_FOLDER"]
        log("Done.\nCreating 7z file...")
        filecount = 0
        with py7zr.SevenZipFile(filename, "w") as archive:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    parentpath = os.path.relpath(filepath, directory)
                    arcname = os.path.join(rootdir, parentpath)
                    slow_log(f"Adding: {filepath}")
                    archive.write(filepath, arcname)
                    filecount += 1
        log(f"Added {filecount} files.\nFinalizing 7z file...")
        log("Done.\nRemoving TMP copy.")
        rmtree(directory)
        log("Done")
    except Exception as e:
        log(f"Error during backup: {e}")
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
            os.makedirs(settings['SOURCE_FOLDER'], exist_ok=True)
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
        log(f"Error deleting existing directory: {e}")
    log(f"Restoring backup: {filename}")
    old_cwd = os.getcwd()
    os.makedirs(settings['SOURCE_FOLDER'], exist_ok=True)
    os.chdir(f"{settings['SOURCE_FOLDER']}{os.sep}..")
    # os.chdir("..")
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
    if backups_listbox is not None:
        backups_listbox.delete(0, tk.END)
        for r in result:
            backups_listbox.insert(tk.END, r)
    update_size()
    try:
        root.update()
    except Exception:
        pass
    return result


@dump_args
def get_number(filename: str) -> int:
    return int(filename.split(settings["FILE_NAME"])[1].split(settings["FILE_EXT"])[0])


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

    # Create GUI and populate initial values
    create_gui()
    if src_var is not None:
        src_var.set(settings.get('SOURCE_FOLDER', './'))
    if dest_var is not None:
        dest_var.set(settings.get('DEST_FOLDER', './'))
    if app_path_var is not None:
        app_path_var.set(settings.get('APP_PATH', ''))
    if make_backup_var is not None:
        make_backup_var.set(settings.get('MAKE_BACKUP', True))

    get_current_backups()

    # finished initialization - allow settings to be saved on change
    global initializing
    initializing = False

    # Enter tkinter main loop
    try:
        root.mainloop()
    except Exception as e:
        log(f"Error in GUI loop: {e}")

    # saved on close via protocol handler


if __name__ == "__main__":
    main()
