import os
import sys
import subprocess
import glob
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import styles

class GalleryTab:
    """Manages the Output Gallery tab view, thumbnail grid, and image/video viewers."""
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
        
        self.thumbnail_cache = []
        self.build_ui()

    def build_ui(self):
        gallery_header = tk.Frame(self.parent, bg=self.bg_main)
        gallery_header.pack(fill=tk.X, padx=15, pady=(15, 8))
        
        tk.Label(gallery_header, text="Generated Outputs", bg=self.bg_main, fg=self.text_primary, font=styles.FONT_HEADER).pack(side=tk.LEFT)
        
        btn_refresh = ttk.Button(gallery_header, text="Refresh Gallery", command=self.refresh_gallery)
        btn_refresh.pack(side=tk.RIGHT, padx=(6, 0))
        
        btn_open_folder = ttk.Button(gallery_header, text="Open Folder", command=self.open_output_folder)
        btn_open_folder.pack(side=tk.RIGHT)
        
        self.gal_canvas = tk.Canvas(self.parent, bg=self.bg_main, highlightthickness=0, bd=0)
        gal_scroll = ttk.Scrollbar(self.parent, orient="vertical", command=self.gal_canvas.yview)
        self.gal_grid = tk.Frame(self.gal_canvas, bg=self.bg_main)
        
        self.gal_grid.bind("<Configure>", lambda e: self.gal_canvas.configure(scrollregion=self.gal_canvas.bbox("all")))
        self.gal_canvas.create_window((0, 0), window=self.gal_grid, anchor="nw")
        self.gal_canvas.configure(yscrollcommand=gal_scroll.set)
        
        self.gal_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=5)
        gal_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        styles.enable_mousewheel_scrolling(self.parent, self.gal_canvas)
        self.refresh_gallery()

    def open_output_folder(self):
        output_dir = self.app.OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        self.open_file_external(output_dir)

    def refresh_gallery(self):
        for widget in self.gal_grid.winfo_children():
            widget.destroy()
        self.thumbnail_cache.clear()
        
        output_dir = self.app.OUTPUT_DIR
        if not os.path.exists(output_dir):
            return
            
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.mp4']
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(output_dir, ext)))
            
        files.sort(key=os.path.getmtime, reverse=True)
        
        columns = 4
        row = 0
        col = 0
        
        for file_path in files:
            filename = os.path.basename(file_path)
            card = tk.Frame(self.gal_grid, bg=self.bg_card, bd=1, relief=tk.SOLID, highlightbackground=self.border_color, width=240, height=260)
            card.grid(row=row, column=col, padx=10, pady=10)
            card.pack_propagate(False)
            
            if file_path.lower().endswith('.mp4'):
                lbl_thumb = tk.Label(card, text="VIDEO\n" + filename, bg=self.bg_input, fg=self.accent_blue, font=styles.FONT_BOLD)
                lbl_thumb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            else:
                try:
                    img = Image.open(file_path)
                    img.thumbnail((220, 200))
                    photo = ImageTk.PhotoImage(img)
                    self.thumbnail_cache.append(photo)
                    lbl_thumb = tk.Label(card, image=photo, bg=self.bg_card, cursor="hand2")
                    lbl_thumb.pack(padx=8, pady=(8, 4))
                    lbl_thumb.bind("<Button-1>", lambda e, p=file_path: self.open_file_external(p))
                except Exception as e:
                    lbl_thumb = tk.Label(card, text="Image Error", bg=self.bg_card, fg=self.text_secondary)
                    lbl_thumb.pack(fill=tk.BOTH, expand=True)
                    
            lbl_name = tk.Label(card, text=filename, bg=self.bg_card, fg=self.text_secondary, font=styles.FONT_SMALL, wraplength=220)
            lbl_name.pack(pady=(0, 6))
            
            col += 1
            if col >= columns:
                col = 0
                row += 1

    def open_file_external(self, path):
        try:
            if sys.platform.startswith('darwin'):
                subprocess.Popen(['open', path])
            elif os.name == 'nt':
                os.startfile(path)
            else:
                subprocess.Popen(['xdg-open', path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")
