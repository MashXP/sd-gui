import os
import tkinter as tk
from tkinter import ttk, filedialog
import styles
from ui.widgets import CollapsibleFrame

class GeneratorTab:
    """Manages the main Generator tab layout, parameter sidebar, collapsible sections, and preview/logs."""
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
        self.btn_green = styles.BTN_GREEN
        self.btn_red = styles.BTN_RED
        self.terminal_bg = styles.TERMINAL_BG
        self.terminal_fg = styles.TERMINAL_FG

        # Form Field Variables (delegated from app)
        self.var_binary = app.var_binary
        self.var_mode = app.var_mode
        self.var_backend = app.var_backend
        self.var_model = app.var_model
        self.var_t5xxl = app.var_t5xxl
        self.var_llm = app.var_llm
        self.var_vae = app.var_vae
        self.var_width = app.var_width
        self.var_height = app.var_height
        self.var_steps = app.var_steps
        self.var_cfg = app.var_cfg
        self.var_guidance = app.var_guidance
        self.var_seed = app.var_seed
        self.var_batch_count = app.var_batch_count
        self.var_output_begin_idx = app.var_output_begin_idx
        self.var_max_vram = app.var_max_vram
        self.var_sampler = app.var_sampler
        self.var_scheduler = app.var_scheduler
        self.var_flow_shift = app.var_flow_shift
        self.var_video_frames = app.var_video_frames
        self.var_cache = app.var_cache
        self.var_cache_option = app.var_cache_option
        self.var_output = app.var_output
        self.var_extra_flags = app.var_extra_flags
        
        self.var_listen_ip = app.var_listen_ip
        self.var_listen_port = app.var_listen_port
        
        self.var_init_img = app.var_init_img
        self.var_strength = app.var_strength
        self.var_hires = app.var_hires
        self.var_hires_scale = app.var_hires_scale
        self.var_hires_denoise = app.var_hires_denoise
        self.var_hires_steps = app.var_hires_steps
        
        self.var_slg_scale = app.var_slg_scale
        self.var_skip_layers = app.var_skip_layers
        self.var_vae_tile_size = app.var_vae_tile_size
        
        self.var_vae_tiling = app.var_vae_tiling
        self.var_vae_conv_direct = app.var_vae_conv_direct
        self.var_offload = app.var_offload
        self.var_fa = app.var_fa
        self.var_circular = app.var_circular
        self.var_disable_metadata = app.var_disable_metadata

        self.build_ui()

    def build_ui(self):
        paned_win = tk.PanedWindow(self.parent, orient=tk.HORIZONTAL, bg=self.bg_main, bd=0, sashwidth=6, sashrelief=tk.FLAT)
        paned_win.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = tk.Frame(paned_win, bg=self.bg_card, bd=1, relief=tk.SOLID, highlightbackground=self.border_color)
        right_frame = tk.Frame(paned_win, bg=self.bg_card, bd=1, relief=tk.SOLID, highlightbackground=self.border_color)
        
        paned_win.add(left_frame, minsize=400, stretch="always")
        paned_win.add(right_frame, minsize=420, stretch="always")
        
        # --- LEFT TILE: PROFILES & PARAMETERS ---
        header_profile = tk.Frame(left_frame, bg=self.bg_card)
        header_profile.pack(fill=tk.X, padx=15, pady=(15, 8))
        tk.Label(header_profile, text="Profiles", bg=self.bg_card, fg=self.accent_blue, font=styles.FONT_TITLE).pack(side=tk.LEFT)
        
        profile_frame = tk.Frame(left_frame, bg=self.bg_card)
        profile_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.combo_profile = ttk.Combobox(profile_frame, width=15, state="readonly", style='TCombobox')
        self.combo_profile.pack(side=tk.LEFT, padx=(0, 6))
        self.combo_profile.bind("<<ComboboxSelected>>", self.app.on_profile_selected)
        
        self.entry_save_name = styles.create_custom_entry(profile_frame, width=14)
        self.entry_save_name.pack(side=tk.LEFT, padx=6, ipady=3)
        
        btn_save = ttk.Button(profile_frame, text="Save Profile", command=self.app.save_profile)
        btn_save.pack(side=tk.LEFT, padx=6)
        
        div = tk.Frame(left_frame, height=1, bg=self.border_color)
        div.pack(fill=tk.X, padx=15, pady=8)
        
        header_settings = tk.Frame(left_frame, bg=self.bg_card)
        header_settings.pack(fill=tk.X, padx=15, pady=(5, 8))
        tk.Label(header_settings, text="Parameters", bg=self.bg_card, fg=self.accent_blue, font=styles.FONT_TITLE).pack(side=tk.LEFT)
        
        self.form_canvas = tk.Canvas(left_frame, bg=self.bg_card, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.form_canvas.yview)
        scroll_frame = tk.Frame(self.form_canvas, bg=self.bg_card)
        
        scroll_frame.bind("<Configure>", lambda e: self.update_scrollregion())
        self.canvas_window = self.form_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        self.form_canvas.bind("<Configure>", self.on_canvas_configure)
        self.form_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.form_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 5), pady=(0, 15))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8), pady=(0, 15))
        
        row = 0
        tk.Label(scroll_frame, text="Base Generation", bg=self.bg_card, fg=self.accent_blue, font=('Helvetica', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky='w', pady=(5, 6))
        row += 1

        tk.Label(scroll_frame, text="Binary Mode", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        self.combo_binary = ttk.Combobox(scroll_frame, textvariable=self.var_binary, values=["sd-cli", "sd-server"], state="readonly", style='TCombobox')
        self.combo_binary.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.combo_binary.bind("<<ComboboxSelected>>", lambda e: self.update_layout_for_binary_mode())
        row += 1

        tk.Label(scroll_frame, text="Generation Mode (-M)", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        combo_mode = ttk.Combobox(scroll_frame, textvariable=self.var_mode, values=["txt2img", "img2img", "vid_gen", "inpaint", "convert"], state="readonly", style='TCombobox')
        combo_mode.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        combo_mode.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="Backend Execution", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        combo_backend = ttk.Combobox(scroll_frame, textvariable=self.var_backend, values=["llm=cpu", "llm=gpu", "cpu", "gpu"], state="readonly", style='TCombobox')
        combo_backend.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        combo_backend.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="Diffusion Model", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        self.combo_model = ttk.Combobox(scroll_frame, textvariable=self.var_model, style='TCombobox')
        self.combo_model.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.combo_model.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        self.combo_model.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="Text Encoder (T5XXL)", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        self.combo_t5xxl = ttk.Combobox(scroll_frame, textvariable=self.var_t5xxl, style='TCombobox')
        self.combo_t5xxl.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.combo_t5xxl.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        self.combo_t5xxl.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="Text Encoder (LLM)", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        self.combo_llm = ttk.Combobox(scroll_frame, textvariable=self.var_llm, style='TCombobox')
        self.combo_llm.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.combo_llm.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        self.combo_llm.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="VAE Decoder", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        self.combo_vae = ttk.Combobox(scroll_frame, textvariable=self.var_vae, style='TCombobox')
        self.combo_vae.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.combo_vae.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        self.combo_vae.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="Prompt", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='nw', pady=6)
        self.entry_prompt = styles.create_custom_text(scroll_frame, height=3)
        self.entry_prompt.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.entry_prompt.bind("<KeyRelease>", self.on_prompt_change)
        row += 1
        
        self.label_neg_prompt = tk.Label(scroll_frame, text="Negative Prompt", bg=self.bg_card, fg=self.text_secondary)
        self.label_neg_prompt.grid(row=row, column=0, sticky='nw', pady=6)
        self.entry_neg_prompt = styles.create_custom_text(scroll_frame, height=2)
        self.entry_neg_prompt.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.entry_neg_prompt.bind("<KeyRelease>", self.on_neg_prompt_change)
        row += 1
        
        tk.Label(scroll_frame, text="Image Size (W / H)", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        size_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        size_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        
        combo_w = ttk.Combobox(size_frame, textvariable=self.var_width, values=["384", "512", "704", "768", "832", "896", "1024"], width=7, state="readonly", style='TCombobox')
        combo_w.pack(side=tk.LEFT, padx=(0, 8))
        combo_w.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        
        combo_h = ttk.Combobox(size_frame, textvariable=self.var_height, values=["384", "480", "512", "704", "768", "896", "1024"], width=7, state="readonly", style='TCombobox')
        combo_h.pack(side=tk.LEFT)
        combo_h.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="Steps / CFG Scale", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        steps_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        steps_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        
        entry_steps = styles.create_custom_entry(steps_frame, textvariable=self.var_steps, width=7)
        entry_steps.pack(side=tk.LEFT, padx=(0, 8), ipady=3)
        entry_steps.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_cfg = styles.create_custom_entry(steps_frame, textvariable=self.var_cfg, width=7)
        entry_cfg.pack(side=tk.LEFT, ipady=3)
        entry_cfg.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="Seed / Max VRAM", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        seed_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        seed_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        
        entry_seed = styles.create_custom_entry(seed_frame, textvariable=self.var_seed, width=10)
        entry_seed.pack(side=tk.LEFT, padx=(0, 8), ipady=3)
        entry_seed.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_vram = styles.create_custom_entry(seed_frame, textvariable=self.var_max_vram, width=8)
        entry_vram.pack(side=tk.LEFT, ipady=3)
        entry_vram.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1

        self.label_batch = tk.Label(scroll_frame, text="Batch Count / Index", bg=self.bg_card, fg=self.text_secondary)
        self.label_batch.grid(row=row, column=0, sticky='w', pady=6)
        self.batch_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        self.batch_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        
        entry_batch = styles.create_custom_entry(self.batch_frame, textvariable=self.var_batch_count, width=7)
        entry_batch.pack(side=tk.LEFT, padx=(0, 8), ipady=3)
        entry_batch.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_begin_idx = styles.create_custom_entry(self.batch_frame, textvariable=self.var_output_begin_idx, width=7)
        entry_begin_idx.pack(side=tk.LEFT, ipady=3)
        entry_begin_idx.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1

        self.label_output = tk.Label(scroll_frame, text="Output Filename", bg=self.bg_card, fg=self.text_secondary)
        self.label_output.grid(row=row, column=0, sticky='w', pady=6)
        self.entry_output = styles.create_custom_entry(scroll_frame, textvariable=self.var_output)
        self.entry_output.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0), ipady=3)
        self.entry_output.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1

        # Listen IP / Port (Server mode only)
        self.label_listen = tk.Label(scroll_frame, text="Listen IP / Port", bg=self.bg_card, fg=self.text_secondary)
        self.label_listen.grid(row=row, column=0, sticky='w', pady=6)
        self.listen_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        self.listen_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        
        self.entry_listen_ip = styles.create_custom_entry(self.listen_frame, textvariable=self.var_listen_ip, width=15)
        self.entry_listen_ip.pack(side=tk.LEFT, padx=(0, 8), ipady=3)
        self.entry_listen_ip.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        self.entry_listen_port = styles.create_custom_entry(self.listen_frame, textvariable=self.var_listen_port, width=7)
        self.entry_listen_port.pack(side=tk.LEFT, ipady=3)
        self.entry_listen_port.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1

        # --- ACCORDION COLLAPSIBLE SECTIONS (DELEGATED ADVANCED OPTIONS) ---

        # 1. Section: Image-to-Image & Highres Fix
        c_hires = CollapsibleFrame(scroll_frame, title="Image-to-Image & Highres Fix", bg_card=self.bg_card, accent_blue=self.accent_blue, text_primary=self.text_primary, expanded=False, on_toggle=self.update_scrollregion)
        c_hires.grid(row=row, column=0, columnspan=2, sticky='we', pady=(8, 2))
        row += 1
        
        f_hires = c_hires.content
        f_hires.columnconfigure(1, weight=1)
        r_sub = 0

        tk.Label(f_hires, text="Input Image (-i)", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        init_frame = tk.Frame(f_hires, bg=self.bg_card)
        init_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        
        entry_init = styles.create_custom_entry(init_frame, textvariable=self.var_init_img)
        entry_init.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
        entry_init.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        btn_browse_init = ttk.Button(init_frame, text="Browse...", command=self.browse_init_image)
        btn_browse_init.pack(side=tk.LEFT)
        r_sub += 1

        tk.Label(f_hires, text="Denoise / Hires Fix", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        hires_act_frame = tk.Frame(f_hires, bg=self.bg_card)
        hires_act_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        
        entry_strength = styles.create_custom_entry(hires_act_frame, textvariable=self.var_strength, width=7)
        entry_strength.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        entry_strength.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        self.chk_hires = tk.Checkbutton(hires_act_frame, text="Enable Hires Fix", variable=self.var_hires, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_hires.pack(side=tk.LEFT)
        r_sub += 1

        tk.Label(f_hires, text="Hires Scale / Denoise", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        hires_scale_frame = tk.Frame(f_hires, bg=self.bg_card)
        hires_scale_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        
        entry_hscale = styles.create_custom_entry(hires_scale_frame, textvariable=self.var_hires_scale, width=7)
        entry_hscale.pack(side=tk.LEFT, padx=(0, 8), ipady=3)
        entry_hscale.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_hdenoise = styles.create_custom_entry(hires_scale_frame, textvariable=self.var_hires_denoise, width=7)
        entry_hdenoise.pack(side=tk.LEFT, ipady=3)
        entry_hdenoise.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_hires, text="Hires Steps", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        entry_hsteps = styles.create_custom_entry(f_hires, textvariable=self.var_hires_steps, width=10)
        entry_hsteps.grid(row=r_sub, column=1, sticky='w', pady=4, padx=(8, 0), ipady=3)
        entry_hsteps.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        # 2. Section: Sampler & Scheduler Settings
        c_sampler = CollapsibleFrame(scroll_frame, title="Sampler & Scheduler Settings", bg_card=self.bg_card, accent_blue=self.accent_blue, text_primary=self.text_primary, expanded=False, on_toggle=self.update_scrollregion)
        c_sampler.grid(row=row, column=0, columnspan=2, sticky='we', pady=(4, 2))
        row += 1

        f_samp = c_sampler.content
        f_samp.columnconfigure(1, weight=1)
        r_sub = 0

        tk.Label(f_samp, text="Sampling Method", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        combo_sampler = ttk.Combobox(f_samp, textvariable=self.var_sampler, values=["euler", "er_sde", "dpm++2s_a", "euler_a", "dpm++2m_sde", "tcd", "lcm"], state="readonly", style='TCombobox')
        combo_sampler.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        combo_sampler.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_samp, text="Scheduler", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        combo_sched = ttk.Combobox(f_samp, textvariable=self.var_scheduler, values=["", "discrete", "smoothstep", "karras", "flux2", "ays", "exponential"], state="readonly", style='TCombobox')
        combo_sched.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        combo_sched.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        r_sub += 1

        # 3. Section: Advanced & Performance Settings
        c_adv = CollapsibleFrame(scroll_frame, title="Advanced & Performance Options", bg_card=self.bg_card, accent_blue=self.accent_blue, text_primary=self.text_primary, expanded=False, on_toggle=self.update_scrollregion)
        c_adv.grid(row=row, column=0, columnspan=2, sticky='we', pady=(4, 6))
        row += 1

        f_adv = c_adv.content
        f_adv.columnconfigure(1, weight=1)
        r_sub = 0

        tk.Label(f_adv, text="Flow Shift / Video Frames", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        vid_frame = tk.Frame(f_adv, bg=self.bg_card)
        vid_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        
        entry_flow = styles.create_custom_entry(vid_frame, textvariable=self.var_flow_shift, width=7)
        entry_flow.pack(side=tk.LEFT, padx=(0, 8), ipady=3)
        entry_flow.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_vframes = styles.create_custom_entry(vid_frame, textvariable=self.var_video_frames, width=10)
        entry_vframes.pack(side=tk.LEFT, ipady=3)
        entry_vframes.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_adv, text="Cache Mode", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        combo_cache = ttk.Combobox(f_adv, textvariable=self.var_cache, values=["none", "spectrum", "easycache", "taylorseer", "dbcache"], state="readonly", style='TCombobox')
        combo_cache.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        combo_cache.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_adv, text="Cache Options", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        entry_cache_opt = styles.create_custom_entry(f_adv, textvariable=self.var_cache_option)
        entry_cache_opt.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0), ipady=3)
        entry_cache_opt.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_adv, text="SLG Scale / Skip Layers", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        slg_frame = tk.Frame(f_adv, bg=self.bg_card)
        slg_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        
        entry_slg = styles.create_custom_entry(slg_frame, textvariable=self.var_slg_scale, width=7)
        entry_slg.pack(side=tk.LEFT, padx=(0, 8), ipady=3)
        entry_slg.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_skip = styles.create_custom_entry(slg_frame, textvariable=self.var_skip_layers, width=10)
        entry_skip.pack(side=tk.LEFT, ipady=3)
        entry_skip.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_adv, text="VAE Tile Size", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        entry_vsize = styles.create_custom_entry(f_adv, textvariable=self.var_vae_tile_size)
        entry_vsize.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0), ipady=3)
        entry_vsize.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_adv, text="Extra CLI Flags", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        entry_extra = styles.create_custom_entry(f_adv, textvariable=self.var_extra_flags)
        entry_extra.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0), ipady=3)
        entry_extra.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_adv, text="Performance Flags", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='nw', pady=6)
        chk_frame = tk.Frame(f_adv, bg=self.bg_card)
        chk_frame.grid(row=r_sub, column=1, sticky='we', pady=6, padx=(8, 0))
        
        self.chk_vae = tk.Checkbutton(chk_frame, text="VAE Tiling", variable=self.var_vae_tiling, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_vae.pack(anchor='w', pady=2)

        self.chk_vae_conv = tk.Checkbutton(chk_frame, text="VAE Conv Direct", variable=self.var_vae_conv_direct, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_vae_conv.pack(anchor='w', pady=2)
        
        self.chk_offload = tk.Checkbutton(chk_frame, text="Offload to CPU", variable=self.var_offload, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_offload.pack(anchor='w', pady=2)
        
        self.chk_fa = tk.Checkbutton(chk_frame, text="Diffusion FA", variable=self.var_fa, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_fa.pack(anchor='w', pady=2)

        self.chk_circular = tk.Checkbutton(chk_frame, text="Circular Padding", variable=self.var_circular, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_circular.pack(anchor='w', pady=2)
        
        self.chk_metadata = tk.Checkbutton(chk_frame, text="Disable Metadata", variable=self.var_disable_metadata, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_metadata.pack(anchor='w', pady=2)
        r_sub += 1
        
        scroll_frame.columnconfigure(1, weight=1)

        # --- RIGHT PANE: PREVIEW & LOGS ---
        preview_label = tk.Label(right_frame, text="Generated Command", bg=self.bg_card, fg=self.accent_blue, font=styles.FONT_TITLE)
        preview_label.pack(anchor='w', padx=15, pady=(15, 4))
        
        self.text_cmd_preview = tk.Text(right_frame, bg=self.terminal_bg, fg=self.accent_blue, insertbackground=self.accent_blue, height=4, font=styles.FONT_CODE, bd=0, highlightthickness=1, highlightbackground=self.border_color, wrap=tk.WORD, padx=8, pady=6)
        self.text_cmd_preview.pack(fill=tk.X, padx=15, pady=4)
        
        actions_frame = tk.Frame(right_frame, bg=self.bg_card)
        actions_frame.pack(fill=tk.X, padx=15, pady=8)
        
        btn_copy_cmd = ttk.Button(actions_frame, text="Copy Command", command=self.app.copy_command)
        btn_copy_cmd.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_start = tk.Button(
            actions_frame,
            text="Start Generation",
            bg=self.btn_green,
            fg="#ffffff",
            font=styles.FONT_BOLD,
            bd=0,
            padx=16,
            pady=8,
            activebackground="#059669",
            activeforeground="#ffffff",
            cursor="hand2",
            command=self.app.start_process
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_stop = tk.Button(
            actions_frame,
            text="Stop Process",
            bg="#374151",
            fg=self.text_secondary,
            font=styles.FONT_BOLD,
            bd=0,
            padx=16,
            pady=8,
            state=tk.DISABLED,
            command=self.app.stop_process
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 15))
        
        self.label_timer = tk.Label(actions_frame, text="Ready", bg=self.bg_card, fg=self.text_secondary, font=styles.FONT_BOLD)
        self.label_timer.pack(side=tk.LEFT)
        
        console_header = tk.Frame(right_frame, bg=self.bg_card)
        console_header.pack(fill=tk.X, padx=15, pady=(5, 5))
        
        tk.Label(console_header, text="Execution Terminal Logs", bg=self.bg_card, fg=self.text_primary, font=styles.FONT_TITLE).pack(side=tk.LEFT)
        
        btn_copy = ttk.Button(console_header, text="Copy Logs", command=self.app.copy_logs)
        btn_copy.pack(side=tk.RIGHT, padx=(5, 0))
        
        btn_clear = ttk.Button(console_header, text="Clear Logs", command=self.app.clear_logs)
        btn_clear.pack(side=tk.RIGHT)
        
        self.text_terminal = tk.Text(
            right_frame,
            bg=self.terminal_bg,
            fg=self.terminal_fg,
            insertbackground=self.terminal_fg,
            font=styles.FONT_CODE,
            wrap=tk.WORD,
            bd=0,
            highlightthickness=1,
            highlightbackground=self.border_color,
            padx=10,
            pady=10
        )
        self.text_terminal.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        styles.setup_text_shortcuts(self.entry_prompt)
        styles.setup_text_shortcuts(self.entry_neg_prompt)
        styles.setup_text_shortcuts(self.text_cmd_preview)
        styles.setup_text_shortcuts(self.text_terminal)
        
        self.update_cmd_preview()

    def on_canvas_configure(self, event):
        if hasattr(self, 'canvas_window'):
            self.form_canvas.itemconfig(self.canvas_window, width=event.width)
        self.update_scrollregion()

    def update_scrollregion(self):
        self.parent.update_idletasks()
        self.form_canvas.configure(scrollregion=self.form_canvas.bbox("all"))

    def browse_init_image(self):
        filename = filedialog.askopenfilename(
            title="Select Input Image for img2img",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All Files", "*.*")]
        )
        if filename:
            self.var_init_img.set(filename)
            if self.var_mode.get() in ["", "txt2img"]:
                self.var_mode.set("img2img")
            self.update_cmd_preview()

    def update_layout_for_binary_mode(self):
        binary = self.var_binary.get()
        if binary == "sd-server":
            self.label_neg_prompt.grid_remove()
            self.entry_neg_prompt.grid_remove()
            self.label_batch.grid_remove()
            self.batch_frame.grid_remove()
            self.label_output.grid_remove()
            self.entry_output.grid_remove()
            self.label_listen.grid()
            self.listen_frame.grid()
        else:
            self.label_neg_prompt.grid()
            self.entry_neg_prompt.grid()
            self.label_batch.grid()
            self.batch_frame.grid()
            self.label_output.grid()
            self.entry_output.grid()
            self.label_listen.grid_remove()
            self.listen_frame.grid_remove()
        self.update_cmd_preview()

    def update_cmd_preview(self):
        preview_cmd = self.app.build_command_list(generator_tab=self)
        if len(preview_cmd) > 0:
            preview_cmd[0] = self.var_binary.get()
            
        cmd_string = " ".join(preview_cmd)
        self.text_cmd_preview.delete("1.0", tk.END)
        self.text_cmd_preview.insert("1.0", cmd_string)

    def on_prompt_change(self, event=None):
        self.update_cmd_preview()

    def on_neg_prompt_change(self, event=None):
        self.update_cmd_preview()
