import tkinter as tk
from tkinter import ttk
import re
import styles
from art_styles import ART_STYLES

class PromptHelperTab:
    """Manages the Prompt Helper tag chip categories and tag insertion into the prompt."""
    def __init__(self, parent_frame, app):
        self.parent = parent_frame
        self.app = app
        self.bg_main = app.bg_main
        self.bg_card = app.bg_card
        self.bg_input = app.bg_input
        self.border_color = app.border_color
        self.accent_blue = app.accent_blue
        self.text_primary = app.text_primary
        self.text_secondary = app.text_secondary
        
        self.art_style_buttons = {}
        self.app.var_art_style.trace_add("write", lambda *args: self.update_art_style_highlights())
        
        self.build_ui()

    def build_ui(self):
        helper_header = tk.Frame(self.parent, bg=self.bg_card)
        helper_header.pack(fill=tk.X, padx=15, pady=(15, 8))
        
        tk.Label(helper_header, text="Prompt Tag Helper", bg=self.bg_card, fg=self.text_primary, font=styles.FONT_HEADER).pack(side=tk.LEFT)
        tk.Label(helper_header, text="Click any chip below to append to your active prompt", bg=self.bg_card, fg=self.text_secondary, font=styles.FONT_SMALL).pack(side=tk.LEFT, padx=15)
        
        cat_canvas = tk.Canvas(self.parent, bg=self.bg_card, highlightthickness=0, bd=0)
        cat_scroll = ttk.Scrollbar(self.parent, orient="vertical", command=cat_canvas.yview)
        cat_frame = tk.Frame(cat_canvas, bg=self.bg_card)
        
        cat_frame.bind("<Configure>", lambda e: cat_canvas.configure(scrollregion=cat_canvas.bbox("all")))
        canvas_win = cat_canvas.create_window((0, 0), window=cat_frame, anchor="nw")
        cat_canvas.bind("<Configure>", lambda e: cat_canvas.itemconfig(canvas_win, width=e.width))
        cat_canvas.configure(yscrollcommand=cat_scroll.set)
        
        cat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=5)
        cat_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        styles.enable_mousewheel_scrolling(self.parent, cat_canvas)
        
        # --- ART STYLES (from art-style-prompts.md) ---
        art_styles_card = tk.Frame(cat_frame, bg=self.bg_card, bd=1, relief=tk.SOLID, highlightbackground=self.border_color)
        art_styles_card.pack(fill=tk.X, expand=True, padx=5, pady=8)
        
        art_header_frame = tk.Frame(art_styles_card, bg=self.bg_card)
        art_header_frame.pack(fill=tk.X, padx=15, pady=(10, 6))
        
        tk.Label(art_header_frame, text="Art Styles", bg=self.bg_card, fg=self.accent_blue, font=styles.FONT_TITLE).pack(side=tk.LEFT)
        
        art_style_names = ["None"] + [name for name, _, _ in ART_STYLES]
        self.combo_art_style = ttk.Combobox(art_header_frame, textvariable=self.app.var_art_style, values=art_style_names, state="readonly", width=25, style='TCombobox')
        self.combo_art_style.pack(side=tk.LEFT, padx=(15, 10))
        self.combo_art_style.bind("<<ComboboxSelected>>", lambda e: self.app.generator_tab.update_cmd_preview() if hasattr(self.app, 'generator_tab') else None)
        
        art_styles_chips = tk.Frame(art_styles_card, bg=self.bg_card)
        art_styles_chips.pack(fill=tk.X, padx=15, pady=(0, 12))
        
        raw_art_style_names = [name for name, _, _ in ART_STYLES]
        self.populate_chips_wrapped(art_styles_chips, raw_art_style_names, is_art_style=True)
        
        # --- EXISTING CATEGORIES (harmonized) ---
        tag_categories = {
            "Aesthetic Tags": [
                "Photorealistic", "Cyberpunk", "3D Render", "Vector Art", 
                "Dark Fantasy", "Surrealism", "Minimalist", "Steampunk"
            ],
            "Lighting & Atmosphere": [
                "Cinematic Lighting", "Volumetric Rays", "Golden Hour", "Moody Lighting", 
                "Neon Glow", "Soft Studio Lighting", "Octane Render", "Ray Tracing", 
                "Dramatic Shadows", "Bioluminescence", "Sunlight", "Rim Lighting"
            ],
            "Camera & Shot Composition": [
                "Close-up Portrait", "Wide Angle Shot", "85mm Lens", "Macro Lens", 
                "Shallow Depth of Field", "Aerial Drone View", "Low Angle", "Bokeh Background", 
                "Eye Level Shot", "Panoramic Shot"
            ],
            "Quality & Detail Enhancers": [
                "8k resolution", "Masterpiece", "Highly Detailed", "Sharp Focus", 
                "Ultra-Detailed", "Flawless Texture", "Unreal Engine 5", "Professional Photography", 
                "Trending on ArtStation"
            ]
        }
        
        for cat_name, tags in tag_categories.items():
            card = tk.Frame(cat_frame, bg=self.bg_card, bd=1, relief=tk.SOLID, highlightbackground=self.border_color)
            card.pack(fill=tk.X, expand=True, padx=5, pady=8)
            
            tk.Label(card, text=cat_name, bg=self.bg_card, fg=self.accent_blue, font=styles.FONT_TITLE).pack(anchor='w', padx=15, pady=(10, 6))
            
            chips_frame = tk.Frame(card, bg=self.bg_card)
            chips_frame.pack(fill=tk.X, padx=15, pady=(0, 12))
            
            self.populate_chips_wrapped(chips_frame, tags, is_art_style=False)

    def update_art_style_highlights(self):
        selected_style = self.app.var_art_style.get()
        for tag, btn in list(self.art_style_buttons.items()):
            try:
                if not btn.winfo_exists():
                    continue
                if tag == selected_style:
                    btn.config(
                        bg=self.accent_blue,
                        fg="#ffffff",
                        text=f"✓ {tag}",
                        activebackground=self.accent_blue,
                        activeforeground="#ffffff"
                    )
                else:
                    btn.config(
                        bg=self.bg_input,
                        fg=self.text_primary,
                        text=f"+ {tag}",
                        activebackground="#374151",
                        activeforeground=self.text_primary
                    )
            except Exception:
                pass

    def populate_chips_wrapped(self, container, tags, is_art_style=False):
        def _layout(event=None):
            width = container.winfo_width()
            if width <= 50:
                return
            if getattr(container, '_last_width', None) == width:
                return
            container._last_width = width
            
            for child in container.winfo_children():
                child.destroy()
                
            if is_art_style:
                self.art_style_buttons.clear()

            current_row = tk.Frame(container, bg=self.bg_card)
            current_row.pack(fill=tk.X, anchor='w', pady=2)
            row_width = 0
            
            for tag in tags:
                if is_art_style:
                    btn = tk.Button(
                        current_row,
                        text=f"+ {tag}",
                        bg=self.bg_input,
                        fg=self.text_primary,
                        font=styles.FONT_SMALL,
                        bd=0,
                        padx=10,
                        pady=4,
                        activebackground="#374151",
                        activeforeground=self.text_primary,
                        cursor="hand2",
                        command=lambda t=tag: self.apply_art_style(t)
                    )
                    self.art_style_buttons[tag] = btn
                else:
                    btn = tk.Button(
                        current_row,
                        text=f"+ {tag}",
                        bg=self.bg_input,
                        fg=self.text_primary,
                        font=styles.FONT_SMALL,
                        bd=0,
                        padx=10,
                        pady=4,
                        activebackground="#374151",
                        activeforeground=self.text_primary,
                        cursor="hand2",
                        command=lambda t=tag: self.append_tag_to_prompt(t)
                    )
                btn_w = btn.winfo_reqwidth() + 8
                if row_width + btn_w > (width - 30) and row_width > 0:
                    current_row = tk.Frame(container, bg=self.bg_card)
                    current_row.pack(fill=tk.X, anchor='w', pady=2)
                    btn.destroy()
                    if is_art_style:
                        btn = tk.Button(
                            current_row,
                            text=f"+ {tag}",
                            bg=self.bg_input,
                            fg=self.text_primary,
                            font=styles.FONT_SMALL,
                            bd=0,
                            padx=10,
                            pady=4,
                            activebackground="#374151",
                            activeforeground=self.text_primary,
                            cursor="hand2",
                            command=lambda t=tag: self.apply_art_style(t)
                        )
                        self.art_style_buttons[tag] = btn
                    else:
                        btn = tk.Button(
                            current_row,
                            text=f"+ {tag}",
                            bg=self.bg_input,
                            fg=self.text_primary,
                            font=styles.FONT_SMALL,
                            bd=0,
                            padx=10,
                            pady=4,
                            activebackground="#374151",
                            activeforeground=self.text_primary,
                            cursor="hand2",
                            command=lambda t=tag: self.append_tag_to_prompt(t)
                        )
                    row_width = 0
                    
                btn.pack(side=tk.LEFT, padx=4, pady=2)
                row_width += btn_w
                
            if is_art_style:
                self.update_art_style_highlights()

        container.bind("<Configure>", _layout)

    def append_tag_to_prompt(self, tag):
        prompt_text_widget = self.app.generator_tab.entry_prompt
        current = prompt_text_widget.get("1.0", "end-1c").strip()
        if not current:
            prompt_text_widget.insert("1.0", tag)
        else:
            if current.endswith(","):
                prompt_text_widget.insert(tk.END, f" {tag}")
            else:
                prompt_text_widget.insert(tk.END, f", {tag}")
        self.app.generator_tab.on_prompt_change()
        self.app.show_toast(f"Added tag: {tag}")

    def apply_art_style(self, style_name):
        """Toggle or set selected art style state (injected automatically at submission time)."""
        current_style = self.app.var_art_style.get()
        if current_style == style_name:
            self.app.var_art_style.set("None")
            self.app.show_toast("Art style disabled")
        else:
            self.app.var_art_style.set(style_name)
            self.app.show_toast(f"Selected art style: {style_name}")
            
        if hasattr(self.app, 'generator_tab'):
            self.app.generator_tab.update_cmd_preview()
