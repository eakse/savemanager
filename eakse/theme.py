def apply_theme_to_all(widget):
    """Recursively apply the helper style to a widget and all its children."""
    if hasattr(widget.winfo_toplevel(), '_apply_dark_style'):
        widget.winfo_toplevel()._apply_dark_style(widget)
    
    for child in widget.winfo_children():
        apply_theme_to_all(child)


def apply_dark_theme(root) -> str | None:
    """
    Apply a simple VS Code-like dark theme to a tkinter root and ttk styles.
    return a string describing any errors encountered, or None if successful.
    """
    result = None
    try:
        bg = '#1e1e1e'
        panel = '#252526'
        fg = '#d4d4d4'
        input_bg = '#3c3c3c'
        accent = '#0e639c'

        root.configure(bg=bg)
        try:
            from tkinter import ttk
            style = ttk.Style()
            # Use clam for better color control
            try:
                style.theme_use('clam')
            except Exception as e:
                if result:
                    result += f"ttk theme change failed. {e}\n"
                else:
                    result = f"ttk theme change failed. {e}\n"
            style.configure('TFrame', background=bg)
            style.configure('TLabel', background=bg, foreground=fg)
            style.configure('TButton', background=panel, foreground=fg)
            style.map('TButton', background=[('active', accent)])
            style.configure('TEntry', fieldbackground=input_bg, foreground=fg)
            style.configure('TCheckbutton', background=bg, foreground=fg)
            style.configure('Vertical.TScrollbar', troughcolor=bg, background=panel)
        except Exception as e:
            if result:
                result += f"ttk styling failed. {e}\n"
            else:
                result = f"ttk styling failed. {e}\n"

        # Some widgets need direct configuration
        def style_widget(w) -> None:
            # Apply common properties where supported; ignore errors for unsupported options
            try:
                w.configure(bg=input_bg, fg=fg)
            except Exception:
                pass
            try:
                w.configure(insertbackground=fg)
            except Exception:
                pass
            try:
                w.configure(highlightbackground=panel)
            except Exception:
                pass
            try:
                # For listboxes, set selection colors and active style
                w.configure(selectbackground=accent, selectforeground='#ffffff')
            except Exception:
                pass
            try:
                w.configure(activestyle='none')
            except Exception:
                pass
            return None

        # Provide a helper to style widgets externally
        root._apply_dark_style = style_widget
    except Exception as e:
        # Gentle fallback: ignore theming errors
        if result:
            result += f"apply_dark_theme failed. {e}\n"
        else:
            result = f"apply_dark_theme failed. {e}\n"
    return result