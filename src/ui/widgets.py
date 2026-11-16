import tkinter as tk
import tkinter.font as tkfont
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

class ResizableTextFrame(tk.Frame):
    """A text box with a drag-to-resize grip.

    The strip under the box is the grip: press it and drag vertically to change
    the box height in text lines. Double-clicking the grip resets to the
    starting height. on_height is called after every height change so the
    caller can refresh the scroll region, with committed=True on the release of
    a drag so the chosen height can be persisted.
    """
    def __init__(self, parent, height=3, min_lines=1, max_lines=16, on_height=None, bg_card=styles.BG_CARD):
        super().__init__(parent, bg=bg_card)
        self.min_lines = min_lines
        self.max_lines = max_lines
        # Height the double-click reset returns to.
        self._default_lines = height
        self.on_height = on_height
        self._drag_start_y = None
        self._drag_start_lines = None
        self._line_px = 0

        self.text = styles.create_custom_text(self, height=height)
        self.text.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=self.scrollbar.set)
        for seq in ("<Button-4>", "<Button-5>", "<MouseWheel>"):
            self.text.bind(seq, self._scroll_text, add="+")

        self.columnconfigure(0, weight=1)

        handle = tk.Frame(self, bg=bg_card)
        handle.grid(row=1, column=0, columnspan=2, sticky="we", pady=(2, 0))

        # The grip is the whole strip, not a small corner, so the handle never
        # has to be aimed at.
        self.grip = tk.Canvas(handle, height=14, highlightthickness=0, bd=0,
                              bg=bg_card, cursor="sizing")
        self.grip.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.grip.bind("<Configure>", self._draw_grip)
        self.grip.bind("<Button-1>", self._drag_start)
        self.grip.bind("<B1-Motion>", self._drag)
        self.grip.bind("<ButtonRelease-1>", self._drag_stop)
        self.grip.bind("<Double-Button-1>", self._reset)

    def _draw_grip(self, event):
        """Redraws the hatch marks in the bottom-right of the grip strip."""
        self.grip.delete("all")
        x = event.width
        for i in (4, 8, 12):
            self.grip.create_line(x - i, 12, x, 12 - i, fill=styles.TEXT_SECONDARY)

    def _line_height(self):
        """Pixels per text line, measured from the box's own font."""
        if not self._line_px:
            face = tkfont.Font(font=self.text["font"])
            self._line_px = face.metrics("linespace")
        return self._line_px

    def set_lines(self, lines, committed=False):
        """Sets the box height in lines, clamped to the min/max range."""
        lines = max(self.min_lines, min(int(lines), self.max_lines))
        if lines != int(self.text["height"]):
            self.text["height"] = lines
            if self.on_height:
                self.on_height(lines, committed)

    def _reset(self, event=None):
        self.set_lines(self._default_lines, committed=True)

    def _drag_start(self, event):
        self._drag_start_y = event.y_root
        self._drag_start_lines = int(self.text["height"])

    def _drag(self, event):
        if self._drag_start_lines is None:
            return
        delta = round((event.y_root - self._drag_start_y) / self._line_height())
        self.set_lines(self._drag_start_lines + delta)

    def _drag_stop(self, event):
        if self._drag_start_lines is None:
            return
        self._drag_start_lines = None
        self._drag_start_y = None
        # Reported directly, not through set_lines: set_lines skips its callback
        # when the height is unchanged, so a drag that lands on the min/max clamp
        # would never reach the commit and the dragged height would not persist.
        if self.on_height:
            self.on_height(int(self.text["height"]), True)

    def _scroll_text(self, event):
        if event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
            self.text.yview_scroll(-1, "units")
        else:
            self.text.yview_scroll(1, "units")
        return "break"

def setup_filterable_combobox(combo, get_full_list_func, on_change_callback=None):
    """
    Enables live auto-suggest filtering on a ttk.Combobox as the user types.
    Filters dropdown choices seamlessly based on current text without resetting when clicking the dropdown.
    """
    def _filter_values(event=None):
        if event and hasattr(event, 'keysym') and event.keysym in ("Up", "Down", "Return", "Escape", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Caps_Lock"):
            if on_change_callback:
                on_change_callback(event)
            return

        typed = combo.get().strip()
        full_list = get_full_list_func()
        
        if not typed:
            matches = [""] + list(full_list)
        else:
            typed_lower = typed.lower()
            matches = [item for item in full_list if typed_lower in item.lower()]
            curr = combo.get()
            if curr and curr not in matches:
                matches.insert(0, curr)

        combo['values'] = matches
        
        if on_change_callback:
            on_change_callback(event)

    combo.bind("<KeyRelease>", _filter_values)
    combo.bind("<<ComboboxSelected>>", lambda e: on_change_callback(e) if on_change_callback else None)

