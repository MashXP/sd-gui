import tkinter as tk
from tkinter import ttk

# Premium dark color palette
BG_MAIN = "#0b0f19"          # Deep dark slate background
BG_CARD = "#111827"          # Darker card container
BG_INPUT = "#1f2937"         # Input background
BORDER_COLOR = "#374151"     # Cool gray border
BORDER_FOCUS = "#38bdf8"     # Bright blue focus border
TEXT_PRIMARY = "#f3f4f6"     # Off-white primary text
TEXT_SECONDARY = "#9ca3af"   # Light gray secondary text
ACCENT_BLUE = "#38bdf8"      # Primary actions
BTN_GREEN = "#10b981"        # Success actions
BTN_RED = "#f43f5e"          # Danger actions
TERMINAL_BG = "#030712"      # Monospace terminal background
TERMINAL_FG = "#40f063"      # Cool green terminal text

# Preferred font families (in order of preference)
FONT_SANS_LIST = ["Inter", "Roboto", "Cantarell", "Ubuntu", "Noto Sans", "Liberation Sans", "DejaVu Sans", "sans-serif"]
FONT_MONO_LIST = ["JetBrains Mono", "Fira Code", "Fira Mono", "Hack", "DejaVu Sans Mono", "Liberation Mono", "monospace"]

FONT_SANS = "sans-serif"
FONT_MONO = "monospace"

FONT_MAIN = (FONT_SANS, 11)
FONT_BOLD = (FONT_SANS, 11, 'bold')
FONT_TITLE = (FONT_SANS, 12, 'bold')
FONT_HEADER = (FONT_SANS, 13, 'bold')
FONT_SMALL = (FONT_SANS, 10)
FONT_CODE = (FONT_MONO, 10)

_fonts_initialized = False

def init_fonts():
    global FONT_SANS, FONT_MONO, FONT_MAIN, FONT_BOLD, FONT_TITLE, FONT_HEADER, FONT_SMALL, FONT_CODE, _fonts_initialized
    if _fonts_initialized:
        return

    # Use fc-list — pure filesystem, no X11 requests.
    try:
        import subprocess
        result = subprocess.run(
            ['fc-list', '--format=%{family[0]}\n'],
            capture_output=True, text=True, timeout=3
        )
        available = {f.strip().lower() for f in result.stdout.splitlines() if f.strip()}
        for f in FONT_SANS_LIST:
            if f.lower() in available:
                FONT_SANS = f
                break
        for f in FONT_MONO_LIST:
            if f.lower() in available:
                FONT_MONO = f
                break
    except Exception:
        pass

    FONT_MAIN = (FONT_SANS, 11)
    FONT_BOLD = (FONT_SANS, 11, 'bold')
    FONT_TITLE = (FONT_SANS, 12, 'bold')
    FONT_HEADER = (FONT_SANS, 13, 'bold')
    FONT_SMALL = (FONT_SANS, 10)
    FONT_CODE = (FONT_MONO, 10)
    _fonts_initialized = True

def setup_combobox_scroll_fix(root):
    """Prevents comboboxes from changing values on mouse wheel scroll."""
    root.unbind_class("TCombobox", "<MouseWheel>")
    root.unbind_class("TCombobox", "<Button-4>")
    root.unbind_class("TCombobox", "<Button-5>")

def enable_mousewheel_scrolling(container, canvas):
    """Enables smooth mousewheel scrolling anywhere inside a container frame."""
    def _on_mousewheel(event):
        if event.num == 4:
            canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            canvas.yview_scroll(3, "units")
        elif event.delta:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

    def _unbind_mousewheel(event):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    container.bind("<Enter>", _bind_mousewheel)
    container.bind("<Leave>", _unbind_mousewheel)

def apply_styles(root, style):
    """Enables and configures the Ttk clam theme and Listbox drop-down options."""
    init_fonts()
    style.theme_use('clam')
    setup_combobox_scroll_fix(root)
    
    # Configure option database for Listbox drop-downs and Entry/Text/Combobox blinking caret cursor
    root.option_add('*TCombobox*Listbox.background', BG_INPUT)
    root.option_add('*TCombobox*Listbox.foreground', TEXT_PRIMARY)
    root.option_add('*TCombobox*Listbox.selectBackground', ACCENT_BLUE)
    root.option_add('*TCombobox*Listbox.selectForeground', BG_MAIN)
    root.option_add('*TCombobox*Listbox.font', FONT_MAIN)
    root.option_add('*TCombobox*insertColor', ACCENT_BLUE)
    root.option_add('*TCombobox*insertBackground', ACCENT_BLUE)
    root.option_add('*TCombobox*insertWidth', 2)
    root.option_add('*Entry.insertBackground', ACCENT_BLUE)
    root.option_add('*Entry.insertColor', ACCENT_BLUE)
    root.option_add('*Entry.insertWidth', 2)
    root.option_add('*Text.insertBackground', ACCENT_BLUE)
    root.option_add('*Text.insertColor', ACCENT_BLUE)
    root.option_add('*Text.insertWidth', 2)
    
    # Ttk widget styling definitions
    style.configure('.',
        background=BG_CARD,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_INPUT,
        bordercolor=BORDER_COLOR,
        lightcolor=BORDER_COLOR,
        darkcolor=BORDER_COLOR,
        insertcolor=ACCENT_BLUE,
        insertwidth=2,
        font=FONT_MAIN
    )
    style.configure('TFrame', background=BG_CARD)
    style.configure('TLabel', background=BG_CARD, foreground=TEXT_PRIMARY, font=FONT_MAIN)
    style.configure('TEntry', insertcolor=ACCENT_BLUE, insertwidth=2)
    
    # Configure Ttk Combobox style
    style.configure('TCombobox',
        fieldbackground=BG_INPUT,
        background=BG_INPUT,
        foreground=TEXT_PRIMARY,
        bordercolor=BORDER_COLOR,
        arrowcolor=TEXT_PRIMARY,
        lightcolor=BORDER_COLOR,
        darkcolor=BORDER_COLOR,
        insertcolor=ACCENT_BLUE,
        insertwidth=2,
        padding=5
    )
    style.map('TCombobox',
        fieldbackground=[('readonly', BG_INPUT), ('active', BG_INPUT)],
        foreground=[('readonly', TEXT_PRIMARY)],
        bordercolor=[('focus', ACCENT_BLUE), ('active', ACCENT_BLUE)],
        insertcolor=[('focus', ACCENT_BLUE), ('active', ACCENT_BLUE)]
    )
    
    # Configure Ttk Button style
    style.configure('TButton',
        background=BG_INPUT,
        foreground=TEXT_PRIMARY,
        bordercolor=BORDER_COLOR,
        font=FONT_BOLD,
        lightcolor="#374151",
        darkcolor="#111827",
        padding=(12, 6)
    )
    style.map('TButton',
        background=[('pressed', '#0284c7'), ('active', ACCENT_BLUE)],
        foreground=[('pressed', BG_MAIN), ('active', BG_MAIN)],
        bordercolor=[('active', ACCENT_BLUE)]
    )
    
    # Configure Scrollbar (dark flat styling)
    style.configure('Vertical.TScrollbar',
        background=BG_INPUT,
        troughcolor=BG_CARD,
        bordercolor=BORDER_COLOR,
        lightcolor=BG_INPUT,
        darkcolor=BG_INPUT,
        arrowcolor=TEXT_PRIMARY,
        arrowsize=10
    )
    style.map('Vertical.TScrollbar',
        background=[('active', '#4b5563'), ('pressed', ACCENT_BLUE)]
    )

    # Configure Treeview dark mode style
    style.configure('Treeview',
        background=BG_INPUT,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_INPUT,
        bordercolor=BORDER_COLOR,
        rowheight=30,
        font=FONT_MAIN
    )
    style.map('Treeview',
        background=[('selected', '#374151'), ('active', '#1f2937')],
        foreground=[('selected', ACCENT_BLUE), ('active', TEXT_PRIMARY)]
    )
    style.configure('Treeview.Heading',
        background=BG_CARD,
        foreground=ACCENT_BLUE,
        bordercolor=BORDER_COLOR,
        lightcolor=BG_CARD,
        darkcolor=BG_CARD,
        font=FONT_BOLD,
        padding=(8, 6)
    )
    style.map('Treeview.Heading',
        background=[('active', BG_INPUT)],
        foreground=[('active', TEXT_PRIMARY)]
    )

    # Configure TNotebook style
    style.configure('TNotebook',
        background=BG_MAIN,
        bordercolor=BG_MAIN,
        lightcolor=BG_MAIN,
        darkcolor=BG_MAIN,
        tabmargins=[2, 2, 2, 0]
    )
    style.configure('TNotebook.Tab',
        background=BG_CARD,
        foreground=TEXT_SECONDARY,
        padding=(16, 8),
        font=FONT_BOLD,
        bordercolor=BORDER_COLOR,
        lightcolor=BG_CARD,
        darkcolor=BG_CARD
    )
    style.map('TNotebook.Tab',
        background=[('selected', BG_INPUT), ('active', '#1f2937')],
        foreground=[('selected', ACCENT_BLUE), ('active', TEXT_PRIMARY)],
        bordercolor=[('selected', ACCENT_BLUE)]
    )

def setup_text_shortcuts(widget):
    """Enables Ctrl+A (Select All), Ctrl+Del (Delete Word Next), and Ctrl+Backspace (Delete Word Prev)."""
    is_entry = isinstance(widget, tk.Entry)

    def select_all(event):
        if is_entry:
            event.widget.select_range(0, tk.END)
            event.widget.icursor(tk.END)
        else:
            event.widget.tag_remove(tk.SEL, "1.0", tk.END)
            event.widget.tag_add(tk.SEL, "1.0", "end-1c")
            event.widget.mark_set(tk.INSERT, "end-1c")
            event.widget.see(tk.INSERT)
        return "break"

    def delete_word_forward(event):
        if is_entry:
            idx = event.widget.index(tk.INSERT)
            val = event.widget.get()
            end = idx
            while end < len(val) and val[end].isspace(): end += 1
            while end < len(val) and not val[end].isspace(): end += 1
            event.widget.delete(idx, end)
        else:
            event.widget.delete(tk.INSERT, "insert wordend")
        return "break"

    def delete_word_backward(event):
        if is_entry:
            idx = event.widget.index(tk.INSERT)
            val = event.widget.get()
            start = idx
            while start > 0 and val[start - 1].isspace(): start -= 1
            while start > 0 and not val[start - 1].isspace(): start -= 1
            event.widget.delete(start, idx)
        else:
            event.widget.delete("insert -1c wordstart", tk.INSERT)
        return "break"

    def _push_to_native_clipboard(text):
        """Push text to the native Wayland or X11 clipboard directly,
        bypassing Tkinter's XWayland clipboard bridge which crashes Electron/Antigravity."""
        import subprocess, os
        try:
            if os.environ.get("WAYLAND_DISPLAY"):
                proc = subprocess.Popen(
                    ['wl-copy'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    start_new_session=True  # isolate from all process groups
                )
                proc.stdin.write(text)
                proc.stdin.close()
            elif os.environ.get("DISPLAY"):
                proc = subprocess.Popen(
                    ['xclip', '-selection', 'clipboard'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    start_new_session=True
                )
                proc.stdin.write(text)
                proc.stdin.close()
        except Exception:
            pass

    def copy_via_wayland(event):
        try:
            if is_entry:
                if event.widget.select_present():
                    sel = event.widget.selection_get()
                    _push_to_native_clipboard(sel)
            else:
                try:
                    sel = event.widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                    _push_to_native_clipboard(sel)
                except tk.TclError:
                    pass
        except Exception:
            pass
        return "break"

    def cut_via_wayland(event):
        try:
            if is_entry:
                if event.widget.select_present():
                    sel = event.widget.selection_get()
                    _push_to_native_clipboard(sel)
                    event.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                try:
                    sel = event.widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                    if sel:
                        _push_to_native_clipboard(sel)
                        event.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                except tk.TclError:
                    pass
        except Exception:
            pass
        return "break"

    widget.bind("<Control-a>", select_all)
    widget.bind("<Control-A>", select_all)
    widget.bind("<Control-c>", copy_via_wayland)
    widget.bind("<Control-C>", copy_via_wayland)
    widget.bind("<Control-x>", cut_via_wayland)
    widget.bind("<Control-X>", cut_via_wayland)
    widget.bind("<Control-Delete>", delete_word_forward)
    widget.bind("<Control-BackSpace>", delete_word_backward)

def create_custom_entry(parent, textvariable=None, **kwargs):
    """Creates a custom modern entry box with focus border highlights."""
    entry = tk.Entry(
        parent,
        textvariable=textvariable,
        bg=BG_INPUT,
        fg=TEXT_PRIMARY,
        insertbackground=ACCENT_BLUE,
        insertwidth=2,
        bd=0,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
        highlightcolor=BORDER_FOCUS,
        font=FONT_MAIN,
        **kwargs
    )
    setup_text_shortcuts(entry)
    return entry

def create_custom_text(parent, height=2, **kwargs):
    """Creates a custom modern text area with focus border highlights."""
    text_area = tk.Text(
        parent,
        bg=BG_INPUT,
        fg=TEXT_PRIMARY,
        insertbackground=ACCENT_BLUE,
        insertwidth=2,
        bd=0,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
        highlightcolor=BORDER_FOCUS,
        font=FONT_MAIN,
        height=height,
        wrap=tk.WORD,
        padx=5,
        pady=4,
        undo=True,
        **kwargs
    )
    setup_text_shortcuts(text_area)
    return text_area
