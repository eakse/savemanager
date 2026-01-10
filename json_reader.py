import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from eakse.common import dump_args
from eakse.theme import apply_dark_theme

settings = {}
settings_filename = "./json_reader_settings.json"


@dump_args
def create_gui():
    root = tk.Tk()
    root.title('JSON Browser')
    try:
        apply_dark_theme(root)
    except Exception:
        pass

    # Top info
    top = ttk.Frame(root)
    top.pack(fill='x', padx=6, pady=6)
    size_label = ttk.Label(top, text='')
    size_label.pack(side='right')

    # Buttons
    btn_frame = ttk.Frame(root)
    btn_frame.pack(fill='x', padx=6, pady=(0,6))
    ttk.Button(btn_frame, text='BACKUP').pack(side='left', padx=(0,6))
    ttk.Button(btn_frame, text='RESTORE').pack(side='left', padx=(0,6))
    ttk.Button(btn_frame, text='RESTORE LATEST').pack(side='left', padx=(0,6))

    # Listbox
    list_frame = ttk.Frame(root)
    list_frame.pack(fill='both', expand=False, padx=6)
    backups_listbox = tk.Listbox(list_frame, height=20, width=120)
    backups_listbox.pack(side='left', fill='x', expand=True)
    scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=backups_listbox.yview)
    scrollbar.pack(side='right', fill='y')
    backups_listbox.config(yscrollcommand=scrollbar.set)
    try:
        root._apply_dark_style(backups_listbox) # type: ignore
    except Exception:
        backups_listbox.config(bg='#252526', fg='#d4d4d4')

    # Source/Dest
    io_frame = ttk.Frame(root)
    io_frame.pack(fill='x', padx=6, pady=6)
    ttk.Label(io_frame, text='Source Folder').grid(row=0, column=0, sticky='w')
    src_var = tk.StringVar()
    ttk.Entry(io_frame, textvariable=src_var, width=60).grid(row=0, column=1, sticky='w')
    ttk.Button(io_frame, text='Browse', command=lambda: filedialog.askdirectory()).grid(row=0, column=2)

    ttk.Label(io_frame, text='Destination Folder').grid(row=1, column=0, sticky='w')
    dest_var = tk.StringVar()
    ttk.Entry(io_frame, textvariable=dest_var, width=60).grid(row=1, column=1, sticky='w')
    ttk.Button(io_frame, text='Browse', command=lambda: filedialog.askdirectory()).grid(row=1, column=2)

    # Log
    log_frame = ttk.Frame(root)
    log_frame.pack(fill='both', expand=True, padx=6, pady=(0,6))
    log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap='word', state='disabled')
    log_text.pack(fill='both', expand=True)
    try:
        root._apply_dark_style(log_text) # type: ignore
    except Exception:
        log_text.config(bg='#3c3c3c', fg='#d4d4d4')

    return root


if __name__ == '__main__':
    win = create_gui()
    win.mainloop()


