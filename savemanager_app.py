import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import os
import py7zr
import json
from datetime import datetime
import time
from shutil import copytree, rmtree
import eakse
from eakse.util import dump_args # type: ignore
from eakse.theme import apply_dark_theme
from eakse.spawn_subprocess import start_executable
import tempfile


class SaveManagerApp:
    # Class constants
    settings_filename = "./savemanager_settings.json"
    slow_log_interval = 30
    settings = {
        "FILE_EXT": "",
        "FILE_NAME": "",
        "FILE_ENU": "",
        "SOURCE_FOLDER": "",
        "DEST_FOLDER": "",
        "APP_PATH": "",
        "SHOW_DEBUG": False,
        "X_POS": 0,
        "Y_POS": 0,
        "SAFETY_BACKUP": "SAFETY_BACKUP.7z,",
        "MAKE_BACKUP": True,
    }


    def __init__(self):
        # runtime state
        self.path_7zip = ""
        self.path_working = ""
        self.slow_log_str = ""
        self.slow_log_cnt = 0
        self.progress_cnt = 0
        self.progress_max = 0

        # tkinter root and variables
        self.root = tk.Tk()
        self.src_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.app_path_var = tk.StringVar()
        self.make_backup_var = tk.BooleanVar(value=True)

        # widget references
        self.log_text = None
        self.size_label = None
        self.backups_listbox = None
        self.run_app_btn = None

        self.initializing = True

        # Load settings before building GUI so initial state is known
        self.settings_init()
        self.debug = self.settings["SHOW_DEBUG"]
        eakse.util.debug = self.debug # type: ignore
        

        # Build GUI
        self.root.title("Save Manager")

        try:
            result = apply_dark_theme(self.root)
            if result:
                self.log(result)
        except Exception:
            pass

        # Set default position from settings if present
        try:
            x = self.settings["X_POS"]
            y = self.settings["Y_POS"]
            self.root.geometry(f"+{x}+{y}")
        except Exception:
            pass

        # Top controls: Backup / Restore / Restore Latest / Create Backup checkbox / Size info
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=6, pady=6)

        backup_btn = ttk.Button(top_frame, text="BACKUP", command=self.on_backup)
        backup_btn.pack(side="left", padx=(0, 6))

        restore_btn = ttk.Button(top_frame, text="RESTORE", command=self.on_restore)
        restore_btn.pack(side="left", padx=(0, 6))

        restore_latest_btn = ttk.Button(
            top_frame, text="RESTORE LATEST", command=self.on_restore_latest
        )
        restore_latest_btn.pack(side="left", padx=(0, 6))

        make_backup_cb = ttk.Checkbutton(
            top_frame, text="CREATE BACKUP", variable=self.make_backup_var
        )
        make_backup_cb.pack(side="left", padx=(0, 6))

        # Run APP button moved to top-right, disabled by default; it will be enabled when a valid executable path is set.
        self.run_app_btn = ttk.Button(
            top_frame, text="RUN APP", command=self.on_run_app, state="disabled"
        )
        self.run_app_btn.pack(side="right", padx=(6, 0))

        self.size_label = ttk.Label(top_frame, text="")
        self.size_label.pack(side="right")

        # Initialize run_app_btn state based on saved settings
        try:
            app_path = self.settings["APP_PATH"]
            if app_path and os.path.exists(app_path) and os.access(app_path, os.X_OK):
                self.run_app_btn.config(state="normal")
            else:
                self.run_app_btn.config(state="disabled")
        except Exception:
            self.run_app_btn.config(state="disabled")

        # Backups list
        # Use a Frame (ttk.Frame) so it follows the themed background
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill="both", expand=False, padx=6)
        self.backups_listbox = tk.Listbox(list_frame, height=10, width=120)
        self.backups_listbox.pack(side="left", fill="x", expand=True)
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.backups_listbox.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.backups_listbox.config(yscrollcommand=scrollbar.set)
        self.backups_listbox.bind("<Double-Button-1>", self.on_backup_double_click)
        # Apply dark styling to listbox (unselected background & selection colors)
        try:
            self.root._apply_dark_style(self.backups_listbox)  # type: ignore
            self.backups_listbox.config(
                selectbackground="#0e639c", selectforeground="#ffffff"
            )
        except Exception:
            self.backups_listbox.config(
                bg="#252526",
                fg="#d4d4d4",
                selectbackground="#0e639c",
                selectforeground="#ffffff",
            )

        # Source / Destination / APP entries
        io_frame = ttk.Frame(self.root)
        io_frame.pack(fill="x", padx=6, pady=6)

        ttk.Label(io_frame, text="Source Folder").grid(row=0, column=0, sticky="w")
        src_entry = ttk.Entry(io_frame, textvariable=self.src_var, width=60)
        src_entry.grid(row=0, column=1, sticky="w")
        src_browse = ttk.Button(io_frame, text="Browse", command=self.on_browse_source)
        src_browse.grid(row=0, column=2, padx=(6, 0))

        ttk.Label(io_frame, text="Destination Folder").grid(row=1, column=0, sticky="w")
        dest_entry = ttk.Entry(io_frame, textvariable=self.dest_var, width=60)
        dest_entry.grid(row=1, column=1, sticky="w")
        dest_browse = ttk.Button(io_frame, text="Browse", command=self.on_browse_dest)
        dest_browse.grid(row=1, column=2, padx=(6, 0))

        ttk.Label(io_frame, text="Executable").grid(row=2, column=0, sticky="w")
        app_entry = ttk.Entry(io_frame, textvariable=self.app_path_var, width=60)
        app_entry.grid(row=2, column=1, sticky="w")
        app_browse = ttk.Button(io_frame, text="Browse", command=self.on_select_app)
        app_browse.grid(row=2, column=2, padx=(6, 0))

        # Log output
        log_frame = ttk.Frame(self.root)
        log_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=self.slow_log_interval + 1, wrap="word", state="disabled"
        )
        self.log_text.pack(fill="both", expand=True)
        try:
            self.root._apply_dark_style(self.log_text)  # type: ignore
        except Exception:
            self.log_text.config(bg="#3c3c3c", fg="#d4d4d4", insertbackground="#d4d4d4")

        # When entries change, update settings
        self.src_var.trace_add("write", self.on_src_changed)
        self.dest_var.trace_add("write", self.on_dest_changed)
        self.app_path_var.trace_add("write", self.on_app_changed)

        # Close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # Entry change handlers (bound to tkinter variable traces)
    def on_src_changed(self, *args):
        self.settings["SOURCE_FOLDER"] = self.src_var.get()
        if self.initializing:
            return
        self.save_settings()

    def on_dest_changed(self, *args):
        self.settings["DEST_FOLDER"] = self.dest_var.get()
        if self.initializing:
            return
        self.save_settings()

    def on_app_changed(self, *args):
        self.settings["APP_PATH"] = self.app_path_var.get()
        if self.initializing:
            # still update run button state even during init
            try:
                path = self.app_path_var.get()
                if self.run_app_btn is not None:
                    self.run_app_btn.config(
                        state="normal"
                        if path and os.path.exists(path) and os.access(path, os.X_OK)
                        else "disabled"
                    )
            except Exception:
                pass
            return
        self.save_settings()
        try:
            path = self.app_path_var.get()
            if self.run_app_btn is not None:
                self.run_app_btn.config(
                    state="normal"
                    if path and os.path.exists(path) and os.access(path, os.X_OK)
                    else "disabled"
                )
        except Exception:
            pass

    def on_close(self):
        try:
            geom = self.root.winfo_geometry()
            # geometry looks like 'WxH+X+Y'
            if "+" in geom:
                parts = geom.split("+")
                self.settings["X_POS"] = int(parts[1])
                self.settings["Y_POS"] = int(parts[2])
                self.save_settings()
        except Exception:
            pass
        self.root.destroy()

    # Event handlers -----------------------------------------------------
    def on_browse_source(self):
        folder = filedialog.askdirectory(
            initialdir=self.settings["SOURCE_FOLDER"]
        )
        if folder:
            self.src_var.set(folder)

    def on_browse_dest(self):
        folder = filedialog.askdirectory(
            initialdir=self.settings["DEST_FOLDER"]
        )
        if folder:
            self.dest_var.set(folder)

    def on_select_app(self):
        filename = filedialog.askopenfilename(
            title="Select executable",
            initialdir=os.path.dirname(self.settings["APP_PATH"])
            if self.settings["APP_PATH"]
            else self.settings["SOURCE_FOLDER"]
        )
        if filename:
            self.app_path_var.set(filename)
            self.log(f"Selected executable: {filename}")

    def on_run_app(self):
        path = self.settings["APP_PATH"]
        if not path:
            self.log("No executable selected. Please select an executable first.")
            return
        if not os.path.exists(path):
            self.log(f"Executable not found: {path}")
            try:
                if self.run_app_btn is not None:
                    self.run_app_btn.config(state="disabled")
            except Exception:
                pass
            return
        if not os.access(path, os.X_OK):
            self.log(f"File is not executable: {path}")
            try:
                if self.run_app_btn is not None:
                    self.run_app_btn.config(state="disabled")
            except Exception:
                pass
            return
        try:
            start_executable([path])
            self.log(f"Started executable: {path}")
        except Exception as e:
            self.log(f"Error starting executable: {e}")

    def on_backup(self):
        # Ensure settings reflect entries
        self.settings["SOURCE_FOLDER"] = self.src_var.get()
        self.settings["DEST_FOLDER"] = self.dest_var.get()
        self.save_settings()
        self.add_new_backup()
        self.log(
            "----------------------------------------------------------------------------------------------------------------------"
        )

    def on_restore(self):
        filename = filedialog.askopenfilename(
            initialdir=self.settings["DEST_FOLDER"],
            title="Select backup to restore",
        )
        if filename:
            self.restore_backup(filename, self.make_backup_var.get())
            self.log(
                "----------------------------------------------------------------------------------------------------------------------"
            )

    def on_restore_latest(self):
        self.restore_backup(
            f"{self.settings['DEST_FOLDER']}{os.sep}{self.get_current_highest()}",
            self.make_backup_var.get(),
        )
        self.log(
            "----------------------------------------------------------------------------------------------------------------------"
        )

    def on_backup_double_click(self, event=None):
        sel = self.backups_listbox.curselection()  # type: ignore
        if not sel:
            return
        filename = self.backups_listbox.get(sel[0])  # type: ignore
        # if it's the safety backup, use full path
        fullpath = f"{self.settings['DEST_FOLDER']}{os.sep}{filename}"
        self.restore_backup(fullpath, self.make_backup_var.get())
        self.log(
            "----------------------------------------------------------------------------------------------------------------------"
        )

    # helpers / utilities -----------------------------------------------
    @dump_args
    def now(self):
        return datetime.now().strftime("%H:%M:%S")

    @dump_args
    def log(self, text, debug=False):
        if not debug or (debug and self.settings["SHOW_DEBUG"]) or self.debug:
            lines = text.split("\n")
            timestamp = self.now()
            if self.log_text is None:
                # Fallback to printing to stdout
                print(f"{timestamp} | {lines[0]}")
                for line in lines[1:]:
                    print(f"         | {line}")
                return
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, f"{timestamp} | {lines[0]}\n")
            for line in lines[1:]:
                self.log_text.insert(tk.END, f"         | {line}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
            try:
                self.root.update()
            except Exception:
                pass

    def slow_log(self, text):
        self.slow_log_cnt += 1
        if self.slow_log_str == "":
            self.slow_log_str = text
        else:
            self.slow_log_str = f"{self.slow_log_str}\n{text}"
        if self.slow_log_cnt == self.slow_log_interval:
            self.slow_log_cnt = 0
            self.log(self.slow_log_str)
            self.slow_log_str = ""

    @dump_args
    def sizeof_fmt(self, num, suffix="B"):
        # https://stackoverflow.com/a/1094933/9267296
        for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}Yi{suffix}"

    @dump_args
    def update_size(self):
        src = self.settings["SOURCE_FOLDER"]
        if not src or not os.path.exists(src):
            txt = "Source folder not found"
            if self.size_label is not None:
                self.size_label.config(text=txt)
            else:
                self.log(txt)
            return

        size = 0
        for path, _, files in os.walk(src):
            for f in files:
                fp = os.path.join(path, f)
                try:
                    size += os.path.getsize(fp)
                except Exception as e:
                    # Log debug info but continue counting other files
                    try:
                        self.log(f"Error getting size for {fp}: {e}", debug=True)
                    except Exception:
                        pass
        txt = f"Folder size: {self.sizeof_fmt(size)}"
        if self.size_label is not None:
            self.size_label.config(text=txt)
        else:
            self.log(txt)

    @dump_args
    def load_settings(self, filename=None):
        filename = filename or self.settings_filename
        self.log(f"Loading settings from {filename}")
        with open(filename) as infile:
            self.settings = json.load(infile)
        self.log(
            "----------------------------------------------------------------------------------------------------------------------"
        )

    @dump_args
    def save_settings(self, filename=None):
        filename = filename or self.settings_filename
        self.log(f"Saving settings to {filename}")
        with open(filename, "w") as outfile:
            json.dump(self.settings, outfile, indent=4)
        self.log(
            "----------------------------------------------------------------------------------------------------------------------"
        )

    @dump_args
    def settings_init(self):
        if os.path.exists(self.settings_filename):
            self.load_settings()
        else:
            self.log("No settings file found, creating default settings...")
            self.settings = {
                "FILE_EXT": ".7z",
                "FILE_NAME": "BACKUP_",
                "FILE_ENU": "",
                "SOURCE_FOLDER": "./",
                "DEST_FOLDER": "./",
                "APP_PATH": "",
                "SHOW_DEBUG": True,
                "X_POS": 0,
                "Y_POS": 0,
                "SAFETY_BACKUP": "SAFETY_BACKUP.7z",
            }
            self.save_settings()

    @dump_args
    def create_backup(self, filename, extralog=""):
        logstr = "Starting backup, application might freeze a bit..."
        rootdir = os.path.basename(self.settings["SOURCE_FOLDER"])
        # dirname = os.path.normpath(rootdir)
        tmp_directory = tempfile.mkdtemp(prefix="eakse_") #f"./TMP_savemanager/{dirname}"
        # create dirs to be safe
        os.makedirs(rootdir, exist_ok=True)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if extralog != "":
            logstr = extralog + "\n" + logstr
        self.log(logstr)
        self.log("Making TMP copy of existing directory.")
        try:
            copytree(self.settings["SOURCE_FOLDER"], tmp_directory, dirs_exist_ok=True)
            self.log("Done.\nCreating 7z file...")
            filecount = 0
            with py7zr.SevenZipFile(filename, "w") as archive:
                for dirpath, dirnames, filenames in os.walk(tmp_directory):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        parentpath = os.path.relpath(filepath, tmp_directory)
                        arcname = os.path.join(rootdir, parentpath)
                        self.slow_log(f"Adding: {filepath}")
                        archive.write(filepath, arcname)
                        filecount += 1
            self.log(f"Added {filecount} files.\nFinalizing 7z file...")
            self.log("Done.\nRemoving TMP copy.")
            rmtree(tmp_directory)
            self.log("Done")
        except Exception as e:
            self.log(f"Error during backup: {e}")
        self.get_current_backups()

    @dump_args
    def add_new_backup(self):
        newbackupname = self.increase(self.get_current_highest())
        start = time.time()
        self.create_backup(
            f"{self.settings['DEST_FOLDER']}{os.sep}{newbackupname}",
            extralog=f"Creating new backup with filename:\n  {newbackupname}",
        )
        self.log(f"Backup done.\nTime elapsed: {time.time() - start:.2f} seconds")

    @dump_args
    def restore_backup(self, filename: str, do_backup: bool):
        start = time.time()
        if os.path.exists(filename):
            if do_backup:
                if os.path.exists(
                    f"{self.settings['DEST_FOLDER']}{os.sep}{self.settings['SAFETY_BACKUP']}"
                ):
                    os.remove(
                        f"{self.settings['DEST_FOLDER']}{os.sep}{self.settings['SAFETY_BACKUP']}"
                    )
                os.makedirs(self.settings["SOURCE_FOLDER"], exist_ok=True)
                self.create_backup(
                    f"{self.settings['DEST_FOLDER']}{os.sep}{self.settings['SAFETY_BACKUP']}",
                    extralog=f"Creating safety backup: {self.settings['SAFETY_BACKUP']}",
                )
            else:
                self.log("Skipping safety backup.")
        else:
            self.log(f"File: {filename} not found.")
            return
        self.log(f"Deleting existing directory: {self.settings['SOURCE_FOLDER']}")
        try:
            rmtree(self.settings["SOURCE_FOLDER"])
        except Exception as e:
            self.log(f"Error deleting existing directory: {e}")
        self.log(f"Restoring backup: {filename}")
        old_cwd = os.getcwd()
        os.makedirs(self.settings["SOURCE_FOLDER"], exist_ok=True)
        os.chdir(f"{self.settings['SOURCE_FOLDER']}{os.sep}..")
        with py7zr.SevenZipFile(f"{filename}", "r") as archive:
            archive.extractall()
        self.log(f"Backup restored.\nTime elapsed: {time.time() - start:.2f} seconds")
        os.chdir(old_cwd)

    @dump_args
    def get_current_backups(self) -> list:
        result = [
            filename
            for filename in next(
                os.walk(self.settings["DEST_FOLDER"]), (None, None, [])
            )[2]
            if (
                filename.startswith(self.settings["FILE_NAME"])
                and filename.lower().endswith(self.settings["FILE_EXT"].lower())
            )
        ]
        result.sort(reverse=True)
        if os.path.exists(
            f"{self.settings['DEST_FOLDER']}{os.sep}{self.settings['SAFETY_BACKUP']}"
        ):
            result.insert(0, self.settings["SAFETY_BACKUP"])
        if self.backups_listbox is not None:
            self.backups_listbox.delete(0, tk.END)
            for r in result:
                self.backups_listbox.insert(tk.END, r)
        self.update_size()
        try:
            self.root.update()
        except Exception:
            pass
        return result

    @dump_args
    def get_number(self, filename: str) -> int:
        raw = filename.split(self.settings["FILE_NAME"])[1].split(self.settings["FILE_EXT"])[0]
        number = int("".join(ch for ch in raw if ch.isdigit()))
        return number

    @dump_args
    def increase(self, filename: str) -> str:
        nr = self.get_number(filename) +1
        return f"{filename.split(self.settings['FILE_NAME'])[0]}{self.settings['FILE_NAME']}{nr:03}{self.settings['FILE_EXT']}"

    @dump_args
    def get_current_highest(self) -> str:
        highest = f"{self.settings['FILE_NAME']}-1{self.settings['FILE_EXT']}"
        filelist = self.get_current_backups()
        if self.settings["SAFETY_BACKUP"] in filelist:
            filelist.remove(self.settings["SAFETY_BACKUP"])
        for filename in filelist:
            if self.get_number(filename) > self.get_number(highest):
                highest = filename
        return highest

    def run(self):
        # Initialization already performed in __init__ (settings loaded and GUI built).
        # Populate variable values from settings for the GUI.
        if self.src_var is not None:
            self.src_var.set(self.settings["SOURCE_FOLDER"])
        if self.dest_var is not None:
            self.dest_var.set(self.settings["DEST_FOLDER"])
        if self.app_path_var is not None:
            self.app_path_var.set(self.settings["APP_PATH"])
        if self.make_backup_var is not None:
            self.make_backup_var.set(self.settings["MAKE_BACKUP"])

        self.get_current_backups()

        # finished initialization - allow settings to be saved on change
        self.initializing = False

        # Enter tkinter main loop
        try:
            self.root.mainloop()
        except Exception as e:
            self.log(f"Error in GUI loop: {e}")
