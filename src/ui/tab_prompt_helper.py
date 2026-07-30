import tkinter as tk
from tkinter import ttk
import styles

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
        
        self.build_ui()

    def build_ui(self):
        helper_header = tk.Frame(self.parent, bg=self.bg_main)
        helper_header.pack(fill=tk.X, padx=15, pady=(15, 8))
        
        tk.Label(helper_header, text="Prompt Tag Helper", bg=self.bg_main, fg=self.text_primary, font=styles.FONT_HEADER).pack(side=tk.LEFT)
        tk.Label(helper_header, text="Click any chip below to append to your active prompt", bg=self.bg_main, fg=self.text_secondary, font=styles.FONT_SMALL).pack(side=tk.LEFT, padx=15)
        
        cat_canvas = tk.Canvas(self.parent, bg=self.bg_main, highlightthickness=0, bd=0)
        cat_scroll = ttk.Scrollbar(self.parent, orient="vertical", command=cat_canvas.yview)
        cat_frame = tk.Frame(cat_canvas, bg=self.bg_main)
        
        cat_frame.bind("<Configure>", lambda e: cat_canvas.configure(scrollregion=cat_canvas.bbox("all")))
        cat_canvas.create_window((0, 0), window=cat_frame, anchor="nw")
        cat_canvas.configure(yscrollcommand=cat_scroll.set)
        
        cat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=5)
        cat_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        tag_categories = {
            "Art Styles & Aesthetics": [
                "Anime Style", "Photorealistic", "Cyberpunk", "Oil Painting", "Watercolor", 
                "3D Render", "Studio Ghibli", "Vector Art", "Concept Art", "Pixel Art", 
                "Dark Fantasy", "Surrealism", "Minimalist", "Ukiyo-e", "Steampunk"
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
            
            for tag in tags:
                btn = tk.Button(
                    chips_frame,
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
                btn.pack(side=tk.LEFT, padx=4, pady=4)

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
