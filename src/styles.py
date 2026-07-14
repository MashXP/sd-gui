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
TERMINAL_FG = "#34d399"      # Cool green terminal text

def apply_styles(root, style):
    """Enables and configures the Ttk clam theme and Listbox drop-down options."""
    style.theme_use('clam')
    
    # Configure option database for Listbox drop-downs
    root.option_add('*TCombobox*Listbox.background', BG_INPUT)
    root.option_add('*TCombobox*Listbox.foreground', TEXT_PRIMARY)
    root.option_add('*TCombobox*Listbox.selectBackground', ACCENT_BLUE)
    root.option_add('*TCombobox*Listbox.selectForeground', BG_MAIN)
    root.option_add('*TCombobox*Listbox.font', ('Helvetica', 10))
    
    # Ttk widget styling definitions
    style.configure('.',
        background=BG_CARD,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_INPUT,
        bordercolor=BORDER_COLOR,
        lightcolor=BORDER_COLOR,
        darkcolor=BORDER_COLOR,
        font=('Helvetica', 10)
    )
    style.configure('TFrame', background=BG_CARD)
    style.configure('TLabel', background=BG_CARD, foreground=TEXT_PRIMARY, font=('Helvetica', 10))
    
    # Configure Ttk Combobox style
    style.configure('TCombobox',
        fieldbackground=BG_INPUT,
        background=BG_INPUT,
        foreground=TEXT_PRIMARY,
        bordercolor=BORDER_COLOR,
        arrowcolor=TEXT_PRIMARY,
        lightcolor=BORDER_COLOR,
        darkcolor=BORDER_COLOR,
        padding=5
    )
    style.map('TCombobox',
        fieldbackground=[('readonly', BG_INPUT), ('active', BG_INPUT)],
        foreground=[('readonly', TEXT_PRIMARY)],
        bordercolor=[('focus', ACCENT_BLUE), ('active', ACCENT_BLUE)]
    )
    
    # Configure Ttk Button style
    style.configure('TButton',
        background=BG_INPUT,
        foreground=TEXT_PRIMARY,
        bordercolor=BORDER_COLOR,
        font=('Helvetica', 10, 'bold'),
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

def create_custom_entry(parent, textvariable=None, **kwargs):
    """Creates a custom modern entry box with focus border highlights."""
    entry = tk.Entry(
        parent,
        textvariable=textvariable,
        bg=BG_INPUT,
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        bd=0,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
        highlightcolor=BORDER_FOCUS,
        font=('Helvetica', 10),
        **kwargs
    )
    return entry

def create_custom_text(parent, height=2, **kwargs):
    """Creates a custom modern text area with focus border highlights."""
    text_area = tk.Text(
        parent,
        bg=BG_INPUT,
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        bd=0,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
        highlightcolor=BORDER_FOCUS,
        font=('Helvetica', 10),
        height=height,
        wrap=tk.WORD,
        padx=5,
        pady=4,
        undo=True,
        **kwargs
    )
    return text_area
