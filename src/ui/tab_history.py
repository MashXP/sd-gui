import tkinter as tk
from tkinter import ttk
import styles

class HistoryTab:
    """Manages the Execution History database treeview table."""
    def __init__(self, parent_frame, app):
        self.parent = parent_frame
        self.app = app
        self.bg_main = app.bg_main
        self.bg_card = app.bg_card
        self.border_color = app.border_color
        self.accent_blue = app.accent_blue
        self.text_primary = app.text_primary
        self.text_secondary = app.text_secondary
        
        self.build_ui()

    def build_ui(self):
        hist_header = tk.Frame(self.parent, bg=self.bg_main)
        hist_header.pack(fill=tk.X, padx=15, pady=(15, 8))
        
        tk.Label(hist_header, text="Execution History Log", bg=self.bg_main, fg=self.text_primary, font=styles.FONT_HEADER).pack(side=tk.LEFT)
        tk.Label(hist_header, text="Double-click any entry to load settings into Generator", bg=self.bg_main, fg=self.text_secondary, font=styles.FONT_SMALL).pack(side=tk.LEFT, padx=15)
        
        btn_refresh = ttk.Button(hist_header, text="Refresh History", command=self.refresh_history_table)
        btn_refresh.pack(side=tk.RIGHT)
        
        tree_frame = tk.Frame(self.parent, bg=self.bg_card, bd=1, relief=tk.SOLID, highlightbackground=self.border_color)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        columns = ("id", "timestamp", "prompt", "size", "seed", "output")
        self.tree_history = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree_history.heading("id", text="ID")
        self.tree_history.heading("timestamp", text="Timestamp")
        self.tree_history.heading("prompt", text="Prompt")
        self.tree_history.heading("size", text="Size")
        self.tree_history.heading("seed", text="Seed")
        self.tree_history.heading("output", text="Output File")
        
        self.tree_history.column("id", width=40, anchor="center")
        self.tree_history.column("timestamp", width=140)
        self.tree_history.column("prompt", width=350)
        self.tree_history.column("size", width=80)
        self.tree_history.column("seed", width=100)
        self.tree_history.column("output", width=180)
        
        scroll_tree = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_history.yview)
        self.tree_history.configure(yscrollcommand=scroll_tree.set)
        
        self.tree_history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_tree.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_history.bind("<Double-1>", self.on_history_double_click)
        
        self.refresh_history_table()

    def refresh_history_table(self):
        for item in self.tree_history.get_children():
            self.tree_history.delete(item)
            
        rows = self.app.db.get_all()
        for r in rows:
            rec_id, ts, model, prompt, neg_p, w, h, seed, output_path, cmd_str = r
            size_str = f"{w}x{h}"
            self.tree_history.insert("", tk.END, values=(rec_id, ts, prompt, size_str, seed, output_path), tags=(str(rec_id),))

    def on_history_double_click(self, event):
        item = self.tree_history.selection()
        if not item:
            return
        vals = self.tree_history.item(item[0], "values")
        if not vals:
            return
            
        rec_id = vals[0]
        rows = self.app.db.get_all()
        target_row = next((r for r in rows if str(r[0]) == str(rec_id)), None)
        if target_row:
            rec_id, ts, model, prompt, neg_p, w, h, seed, output_path, cmd_str = target_row
            
            gen_tab = self.app.generator_tab
            gen_tab.var_model.set(model)
            gen_tab.entry_prompt.delete("1.0", tk.END)
            gen_tab.entry_prompt.insert("1.0", prompt)
            gen_tab.entry_neg_prompt.delete("1.0", tk.END)
            if neg_p:
                gen_tab.entry_neg_prompt.insert("1.0", neg_p)
            gen_tab.var_width.set(str(w))
            gen_tab.var_height.set(str(h))
            gen_tab.var_seed.set(str(seed))
            
            gen_tab.update_cmd_preview()
            self.app.notebook.select(0)
            self.app.show_toast(f"Loaded parameters from Run #{rec_id}")
