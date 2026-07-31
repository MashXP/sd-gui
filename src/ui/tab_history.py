import tkinter as tk
from tkinter import ttk, messagebox
import styles

class HistoryTab:
    def __init__(self, parent_frame, app):
        self.parent = parent_frame
        self.app = app
        self.bg_main = app.bg_main
        self.bg_card = app.bg_card
        self.border_color = app.border_color
        self.accent_blue = app.accent_blue
        self.text_primary = app.text_primary
        self.text_secondary = app.text_secondary
        self.selection = set()
        self.per_page = 20
        self.page = 1
        self.total_pages = 1
        self._anchor_index = None
        self.drag_entered = set()
        self.rows_data = []
        self._last_cell_value = None
        self._last_cell_col = None
        self.build_ui()

    def build_ui(self):
        hist_header = tk.Frame(self.parent, bg=self.bg_card)
        hist_header.pack(fill=tk.X, padx=15, pady=(15, 8))

        tk.Label(hist_header, text="Execution History Log", bg=self.bg_card,
                 fg=self.text_primary, font=styles.FONT_HEADER).pack(side=tk.LEFT)
        tk.Label(hist_header,                  text="Check rows to delete | Ctrl+C: copy cell | Ctrl+Click: toggle | Shift+Click: range | Drag: area | Double-click: load into Generator",
                 bg=self.bg_card, fg=self.text_secondary, font=styles.FONT_SMALL).pack(side=tk.LEFT, padx=15)

        btn_frame = tk.Frame(hist_header, bg=self.bg_card)
        btn_frame.pack(side=tk.RIGHT)

        self.btn_record = tk.Button(
            btn_frame, text="● Recording", fg="#34d399", bg=self.bg_card,
            font=styles.FONT_SMALL, bd=0, padx=8, cursor="hand2",
            activebackground=self.bg_card, activeforeground="#34d399",
            command=self.toggle_recording
        )
        self.btn_record.pack(side=tk.LEFT, padx=4)

        btn_delete_sel = ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected)
        btn_delete_sel.pack(side=tk.LEFT, padx=4)

        btn_delete_all = ttk.Button(btn_frame, text="Delete All", command=self.delete_all)
        btn_delete_all.pack(side=tk.LEFT, padx=4)

        btn_refresh = ttk.Button(btn_frame, text="Refresh", command=self.refresh_history_table)
        btn_refresh.pack(side=tk.LEFT, padx=4)

        tree_frame = tk.Frame(self.parent, bg=self.bg_card, bd=1, relief=tk.SOLID,
                              highlightbackground=self.border_color)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 0))

        columns = ("check", "id", "timestamp", "mode", "prompt", "size", "seed", "steps", "cfg", "time", "sampler", "output")
        self.tree_history = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")

        col_cfg = [
            ("check",     "[ ]",   50,  "center"),
            ("id",        "ID",    40,  "center"),
            ("timestamp", "Timestamp", 140, "w"),
            ("mode",      "Mode",  80,  "center"),
            ("prompt",    "Prompt", 320, "w"),
            ("size",      "Size",  70,  "center"),
            ("seed",      "Seed",  100, "w"),
            ("steps",     "Steps", 50,  "center"),
            ("cfg",       "CFG",   50,  "center"),
            ("time",      "Time",  70,  "center"),
            ("sampler",   "Sampler", 90, "w"),
            ("output",    "Output File", 180, "w"),
        ]
        for col_id, heading, width, anchor in col_cfg:
            self.tree_history.heading(col_id, text=heading)
            self.tree_history.column(col_id, width=width, anchor=anchor, minwidth=30)

        scroll_tree = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_history.yview)
        self.tree_history.configure(yscrollcommand=scroll_tree.set)

        self.tree_history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_tree.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_history.bind("<Button-1>", self.on_button_1)
        self.tree_history.bind("<ButtonRelease-1>", self.on_click)
        self.tree_history.bind("<B1-Motion>", self.on_drag_motion)
        self.tree_history.bind("<Double-1>", self.on_history_double_click)
        self.tree_history.bind("<Control-c>", self.on_ctrl_c)
        self.tree_history.bind("<Control-C>", self.on_ctrl_c)

        # Pagination bar
        nav_frame = tk.Frame(self.parent, bg=self.bg_main)
        nav_frame.pack(fill=tk.X, padx=15, pady=(8, 15))

        self.btn_prev = tk.Button(
            nav_frame, text="◀ Prev", bg=self.bg_main, fg=self.accent_blue,
            font=styles.FONT_SMALL, bd=0, padx=8, cursor="hand2",
            activebackground=self.bg_card, activeforeground=self.accent_blue,
            command=self.prev_page
        )
        self.btn_prev.pack(side=tk.LEFT, padx=(0, 8))

        self.lbl_page = tk.Label(
            nav_frame, text="Page 1/1", bg=self.bg_main, fg=self.text_secondary,
            font=styles.FONT_SMALL
        )
        self.lbl_page.pack(side=tk.LEFT, padx=8)

        self.btn_next = tk.Button(
            nav_frame, text="Next ▶", bg=self.bg_main, fg=self.accent_blue,
            font=styles.FONT_SMALL, bd=0, padx=8, cursor="hand2",
            activebackground=self.bg_card, activeforeground=self.accent_blue,
            command=self.next_page
        )
        self.btn_next.pack(side=tk.LEFT, padx=(8, 0))

        # Total count label on the right
        self.lbl_count = tk.Label(
            nav_frame, text="", bg=self.bg_main, fg=self.text_secondary,
            font=styles.FONT_SMALL
        )
        self.lbl_count.pack(side=tk.RIGHT)

        self.refresh_history_table()

    def refresh_history_table(self):
        for item in self.tree_history.get_children():
            self.tree_history.delete(item)
        self.selection.clear()
        self.drag_entered.clear()
        self.rows_data = []

        total = self.app.db.count_all()
        self.total_pages = max(1, (total + self.per_page - 1) // self.per_page)
        self.page = min(self.page, self.total_pages)

        offset = (self.page - 1) * self.per_page
        rows = self.app.db.get_all(limit=self.per_page, offset=offset)

        self.rows_data = rows
        for r in rows:
            (rec_id, ts, model, prompt, neg_p, w, h, seed, output_path, cmd_str,
             gen_time, mode, steps, cfg, sampler) = r
            size_str = f"{w}x{h}"
            steps_str = str(steps) if steps is not None else ""
            cfg_str = f"{cfg:.1f}" if cfg is not None else ""
            time_str = f"{gen_time:.1f}s" if gen_time is not None else ""
            mode_str = mode if mode else ""
            sampler_str = sampler if sampler else ""
            self.tree_history.insert("", tk.END, values=(
                "[ ]", rec_id, ts, mode_str, prompt, size_str, seed,
                steps_str, cfg_str, time_str, sampler_str, output_path
            ), tags=(str(rec_id),))

        self.lbl_page.config(text=f"Page {self.page}/{self.total_pages}")
        self.lbl_count.config(text=f"Total: {total}")
        self.btn_prev.config(state=tk.NORMAL if self.page > 1 else tk.DISABLED)
        self.btn_next.config(state=tk.NORMAL if self.page < self.total_pages else tk.DISABLED)

    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.refresh_history_table()

    def next_page(self):
        if self.page < self.total_pages:
            self.page += 1
            self.refresh_history_table()

    def _get_row_index(self, item):
        children = self.tree_history.get_children()
        try:
            return children.index(item)
        except ValueError:
            return -1

    def _toggle_item(self, item):
        vals = self.tree_history.item(item, "values")
        if not vals:
            return
        rec_id = vals[1]
        if rec_id in self.selection:
            self.selection.discard(rec_id)
            self.tree_history.set(item, "check", "[ ]")
        else:
            self.selection.add(rec_id)
            self.tree_history.set(item, "check", "[x]")

    def on_button_1(self, event):
        col = self.tree_history.identify_column(event.x)
        item = self.tree_history.identify_row(event.y)
        if item:
            vals = self.tree_history.item(item, "values")
            if vals:
                col_idx = int(col[1:]) - 1
                if 0 <= col_idx < len(vals):
                    self._last_cell_value = vals[col_idx]
                    self._last_cell_col = col
        if col == "#1":
            return "break"

    def on_click(self, event):
        col = self.tree_history.identify_column(event.x)
        item = self.tree_history.identify_row(event.y)
        if not item:
            return

        idx = self._get_row_index(item)
        if col == "#1" and idx < 0:
            return

        if col == "#1":
            ctrl = bool(event.state & 0x4)
            shift = bool(event.state & 0x1)

            if shift and self._anchor_index is not None:
                children = self.tree_history.get_children()
                start = min(self._anchor_index, idx)
                end = max(self._anchor_index, idx)
                for i in range(start, end + 1):
                    self._toggle_item(children[i])
            elif ctrl:
                self._toggle_item(item)
            else:
                self.selection.clear()
                for child in self.tree_history.get_children():
                    self.tree_history.set(child, "check", "[ ]")
                self._toggle_item(item)
                self._anchor_index = idx

    def on_drag_motion(self, event):
        col = self.tree_history.identify_column(event.x)
        if col != "#1":
            return

        item = self.tree_history.identify_row(event.y)
        if not item or item in self.drag_entered:
            return

        self.drag_entered.add(item)
        self._toggle_item(item)

    def toggle_recording(self):
        recording = self.app.var_record_history.get()
        self.app.var_record_history.set(not recording)
        if not recording:
            self.btn_record.config(text="● Recording", fg="#34d399")
        else:
            self.btn_record.config(text="○ Paused", fg=self.text_secondary)

    def on_ctrl_c(self, event):
        val = self._last_cell_value
        col = self._last_cell_col
        if val and col in ("#5", "#7"):
            self.app.copy_to_clipboard(val)
            col_name = "Prompt" if col == "#5" else "Seed"
            self.app.show_toast(f"Copied {col_name}: {val[:60]}{'...' if len(val) > 60 else ''}")
        return "break"

    def delete_selected(self):
        if not self.selection:
            messagebox.showinfo("Delete", "No entries selected. Click the [ ] checkbox to select rows.")
            return
        ids = list(self.selection)
        if not messagebox.askyesno("Confirm Delete",
                                   f"Delete {len(ids)} selected history entr{'y' if len(ids) == 1 else 'ies'}?"):
            return
        self.app.db.delete_entries([int(i) for i in ids])
        self.refresh_history_table()
        self.app.show_toast(f"Deleted {len(ids)} entr{'y' if len(ids) == 1 else 'ies'}")

    def delete_all(self):
        total = self.app.db.count_all()
        if total == 0:
            return
        if not messagebox.askyesno("Confirm Delete All",
                                   f"Delete ALL {total} history entries?\n\nThis cannot be undone."):
            return
        self.app.db.clear()
        self.refresh_history_table()
        self.app.show_toast("All history entries deleted")

    def on_history_double_click(self, event):
        col = self.tree_history.identify_column(event.x)
        if col == "#1":
            return
        item = self.tree_history.identify_row(event.y)
        if not item:
            return
        vals = self.tree_history.item(item, "values")
        if not vals:
            return

        rec_id = vals[1]
        target = next((r for r in self.rows_data if str(r[0]) == str(rec_id)), None)
        if not target:
            return

        (rec_id, ts, model, prompt, neg_p, w, h, seed, output_path, cmd_str,
         gen_time, mode, steps, cfg, sampler) = target

        gen_tab = self.app.generator_tab
        gen_tab.var_model.set(model or "")
        gen_tab.entry_prompt.delete("1.0", tk.END)
        gen_tab.entry_prompt.insert("1.0", prompt or "")
        gen_tab.entry_neg_prompt.delete("1.0", tk.END)
        if neg_p:
            gen_tab.entry_neg_prompt.insert("1.0", neg_p)
        gen_tab.var_width.set(str(w) if w else "512")
        gen_tab.var_height.set(str(h) if h else "512")
        gen_tab.var_seed.set(str(seed) if seed else "-1")

        if mode:
            gen_tab.var_mode.set(mode)
        if steps is not None:
            gen_tab.var_steps.set(str(steps))
        if cfg is not None:
            gen_tab.var_cfg.set(str(cfg))
        if sampler:
            gen_tab.var_sampler.set(sampler)

        gen_tab.update_cmd_preview()
        self.app.notebook.select(0)
        self.app.show_toast(f"Loaded parameters from Run #{rec_id}")
