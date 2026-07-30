import tkinter as tk
from tkinter import ttk
import styles

class CollapsibleFrame(tk.Frame):
    """A clean, cross-platform accordion dropdown section for Tkinter."""
    def __init__(self, parent, title="Advanced Settings", bg_card="#111827", accent_blue="#38bdf8", text_primary="#f3f4f6", expanded=False, on_toggle=None):
        super().__init__(parent, bg=bg_card)
        self.expanded = expanded
        self.bg_card = bg_card
        self.accent_blue = accent_blue
        self.text_primary = text_primary
        self.title_text = title
        self.on_toggle = on_toggle

        # Header Bar
        self.header = tk.Frame(self, bg=bg_card, cursor="hand2")
        self.header.pack(fill=tk.X, expand=True, pady=(8, 2))

        lbl_text = f"[-] {title}" if expanded else f"[+] {title}"
        self.toggle_btn = tk.Label(
            self.header,
            text=lbl_text,
            bg=bg_card,
            fg=accent_blue,
            font=styles.FONT_BOLD,
            anchor='w'
        )
        self.toggle_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Content Container
        self.content = tk.Frame(self, bg=bg_card)
        if self.expanded:
            self.content.pack(fill=tk.X, expand=True, padx=2, pady=4)

        # Bind toggle click
        self.header.bind("<Button-1>", self.toggle)
        self.toggle_btn.bind("<Button-1>", self.toggle)

    def toggle(self, event=None):
        self.expanded = not self.expanded
        if self.expanded:
            self.toggle_btn.config(text=f"[-] {self.title_text}")
            self.content.pack(fill=tk.X, expand=True, padx=2, pady=4)
        else:
            self.toggle_btn.config(text=f"[+] {self.title_text}")
            self.content.pack_forget()

        if self.on_toggle:
            self.on_toggle()
