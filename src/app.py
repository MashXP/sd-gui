import os
import sys
import time
import subprocess
import queue
import tkinter as tk
from tkinter import ttk, messagebox

import styles
import profile_manager
from runner import ProcessRunner

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR = os.path.join(WORKSPACE_DIR, "profiles")
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "output")

# Path to the build binaries
CLI_PATH = os.path.expanduser("~/App/stable-diffusion.cpp/build/bin/sd-cli")
SERVER_PATH = os.path.expanduser("~/App/stable-diffusion.cpp/build/bin/sd-server")

class DesktopManager:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ SD-CLI Desktop Manager")
        self.root.geometry("1200x780")
        
        # Configure local directories
        os.makedirs(PROFILES_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Palette configuration (imported from styles)
        self.bg_main = styles.BG_MAIN
        self.bg_card = styles.BG_CARD
        self.bg_input = styles.BG_INPUT
        self.border_color = styles.BORDER_COLOR
        self.accent_blue = styles.ACCENT_BLUE
        self.btn_green = styles.BTN_GREEN
        self.btn_red = styles.BTN_RED
        self.terminal_bg = styles.TERMINAL_BG
        self.terminal_fg = styles.TERMINAL_FG
        self.text_primary = styles.TEXT_PRIMARY
        self.text_secondary = styles.TEXT_SECONDARY
        
        self.root.configure(bg=self.bg_main)
        
        # Apply standard styles
        self.style = ttk.Style()
        styles.apply_styles(self.root, self.style)
        
        # Process and logging queues
        self.log_queue = queue.Queue()
        self.runner = ProcessRunner(self.log_queue)
        self.start_time = None
        self.timer_running = False
        
        # Form field variables
        self.var_binary = tk.StringVar(value="sd-server")
        self.var_backend = tk.StringVar(value="llm=cpu")
        self.var_model = tk.StringVar()
        self.var_llm = tk.StringVar()
        self.var_vae = tk.StringVar()
        self.var_width = tk.StringVar(value="768")
        self.var_height = tk.StringVar(value="768")
        self.var_steps = tk.StringVar(value="4")
        self.var_cfg = tk.StringVar(value="1.0")
        self.var_guidance = tk.StringVar(value="")
        self.var_seed = tk.StringVar(value="-1")
        self.var_batch_count = tk.StringVar(value="1")
        self.var_output_begin_idx = tk.StringVar(value="")
        self.var_max_vram = tk.StringVar(value="-0.1")
        self.var_sampler = tk.StringVar(value="euler")
        self.var_scheduler = tk.StringVar(value="discrete")
        self.var_cache = tk.StringVar(value="none")
        self.var_cache_option = tk.StringVar(value="")
        self.var_output = tk.StringVar(value="output_%03d.png")
        
        # Server specific variables
        self.var_listen_ip = tk.StringVar(value="0.0.0.0")
        self.var_listen_port = tk.StringVar(value="1234")
        
        # Highres fix & Img2Img variables
        self.var_strength = tk.StringVar(value="0.75")
        self.var_hires = tk.BooleanVar(value=False)
        self.var_hires_scale = tk.StringVar(value="2.0")
        self.var_hires_denoise = tk.StringVar(value="0.7")
        self.var_hires_steps = tk.StringVar(value="0")
        
        # Advanced SLG & Tiling variables
        self.var_slg_scale = tk.StringVar(value="")
        self.var_skip_layers = tk.StringVar(value="")
        self.var_vae_tile_size = tk.StringVar(value="")
        
        # Boolean advanced flags
        self.var_vae_tiling = tk.BooleanVar(value=True)
        self.var_offload = tk.BooleanVar(value=True)
        self.var_fa = tk.BooleanVar(value=True)
        self.var_circular = tk.BooleanVar(value=False)
        self.var_disable_metadata = tk.BooleanVar(value=False)
        
        self.profile_list = []
        self.scanned_models = []
        
        self.build_ui()
        
        # Scan and load profile selections
        self.scan_workspace()
        self.load_profiles_list()
        
        # Setup polling logs queue
        self.root.after(100, self.poll_log_queue)
        
        # Handle close window
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def scan_workspace(self):
        self.scanned_models = []
        models_dir = os.path.join(WORKSPACE_DIR, "models")
        if os.path.exists(models_dir):
            for root, dirs, files in os.walk(models_dir):
                for file in files:
                    if file.endswith(('.safetensors', '.gguf', '.ckpt')):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, WORKSPACE_DIR)
                        self.scanned_models.append(rel_path)
        self.scanned_models.sort()
        
        for combo in [self.combo_model, self.combo_llm, self.combo_vae]:
            combo['values'] = [""] + self.scanned_models

    def load_profiles_list(self):
        self.profile_list = [f[:-4] for f in os.listdir(PROFILES_DIR) if f.endswith(".env")]
        self.profile_list.sort()
        self.combo_profile['values'] = self.profile_list

    def build_ui(self):
        # Window main wrapper layout
        main_frame = tk.Frame(self.root, bg=self.bg_main)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Configuration Left Pane
        left_frame = tk.Frame(main_frame, bg=self.bg_card, bd=1, relief=tk.SOLID, highlightbackground=self.border_color, width=550)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # Console Log Right Pane
        right_frame = tk.Frame(main_frame, bg=self.bg_card, bd=1, relief=tk.SOLID, highlightbackground=self.border_color)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # --- LEFT PANE: PROFILES MANAGER ---
        header_profile = tk.Frame(left_frame, bg=self.bg_card)
        header_profile.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        tk.Label(header_profile, text="📁 Profiles", bg=self.bg_card, fg=self.accent_blue, font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT)
        
        profile_frame = tk.Frame(left_frame, bg=self.bg_card)
        profile_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.combo_profile = ttk.Combobox(profile_frame, width=16, state="readonly", style='TCombobox')
        self.combo_profile.pack(side=tk.LEFT, padx=(0, 8))
        self.combo_profile.bind("<<ComboboxSelected>>", self.on_profile_selected)
        
        self.entry_save_name = styles.create_custom_entry(profile_frame, width=15)
        self.entry_save_name.pack(side=tk.LEFT, padx=8, ipady=3)
        
        btn_save = ttk.Button(profile_frame, text="Save Profile", command=self.save_profile)
        btn_save.pack(side=tk.LEFT, padx=8)
        
        # Divider Line
        div = tk.Frame(left_frame, height=1, bg=self.border_color)
        div.pack(fill=tk.X, padx=20, pady=10)
        
        # Settings Title
        header_settings = tk.Frame(left_frame, bg=self.bg_card)
        header_settings.pack(fill=tk.X, padx=20, pady=(5, 10))
        tk.Label(header_settings, text="⚙️ Parameters", bg=self.bg_card, fg=self.accent_blue, font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT)
        
        # Scrollable Settings panel
        form_canvas = tk.Canvas(left_frame, bg=self.bg_card, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=form_canvas.yview)
        scroll_frame = tk.Frame(form_canvas, bg=self.bg_card)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: form_canvas.configure(scrollregion=form_canvas.bbox("all"))
        )
        form_canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=500)
        form_canvas.configure(yscrollcommand=scrollbar.set)
        
        form_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 5), pady=(0, 20))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=(0, 20))
        
        row = 0
        
        # Section Header: Base Generation
        tk.Label(scroll_frame, text="🎯 Base Generation", bg=self.bg_card, fg=self.accent_blue, font=('Helvetica', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky='w', pady=(5, 8))
        row += 1

        # Binary Selector
        tk.Label(scroll_frame, text="Binary Mode", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        self.combo_binary = ttk.Combobox(scroll_frame, textvariable=self.var_binary, values=["sd-server", "sd-cli"], state="readonly", style='TCombobox')
        self.combo_binary.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        self.combo_binary.bind("<<ComboboxSelected>>", lambda e: self.update_layout_for_binary_mode())
        row += 1
        
        # Backend execution
        tk.Label(scroll_frame, text="Backend Execution", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        combo_backend = ttk.Combobox(scroll_frame, textvariable=self.var_backend, values=["llm=cpu", "llm=gpu", "cpu", "gpu"], state="readonly", style='TCombobox')
        combo_backend.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        combo_backend.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        row += 1
        
        # Model dropdown
        tk.Label(scroll_frame, text="Diffusion Model", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        self.combo_model = ttk.Combobox(scroll_frame, textvariable=self.var_model, style='TCombobox')
        self.combo_model.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        self.combo_model.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        self.combo_model.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1
        
        # LLM dropdown
        tk.Label(scroll_frame, text="Text Encoder (LLM)", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        self.combo_llm = ttk.Combobox(scroll_frame, textvariable=self.var_llm, style='TCombobox')
        self.combo_llm.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        self.combo_llm.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        self.combo_llm.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1
        
        # VAE dropdown
        tk.Label(scroll_frame, text="VAE Decoder", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        self.combo_vae = ttk.Combobox(scroll_frame, textvariable=self.var_vae, style='TCombobox')
        self.combo_vae.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        self.combo_vae.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        self.combo_vae.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1
        
        # Prompt TextArea (Dynamically Expandable)
        tk.Label(scroll_frame, text="Prompt", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='nw', pady=8)
        self.entry_prompt = styles.create_custom_text(scroll_frame, height=2)
        self.entry_prompt.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        self.entry_prompt.bind("<KeyRelease>", self.on_prompt_change)
        row += 1
        
        # Negative Prompt TextArea (Dynamically Expandable)
        self.label_neg_prompt = tk.Label(scroll_frame, text="Negative Prompt", bg=self.bg_card, fg=self.text_secondary)
        self.label_neg_prompt.grid(row=row, column=0, sticky='nw', pady=8)
        self.entry_neg_prompt = styles.create_custom_text(scroll_frame, height=2)
        self.entry_neg_prompt.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        self.entry_neg_prompt.bind("<KeyRelease>", self.on_neg_prompt_change)
        row += 1
        
        # Image Sizes
        tk.Label(scroll_frame, text="Image Size (W / H)", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        size_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        size_frame.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        
        combo_w = ttk.Combobox(size_frame, textvariable=self.var_width, values=["384", "512", "704", "768", "896", "1024"], width=7, state="readonly", style='TCombobox')
        combo_w.pack(side=tk.LEFT, padx=(0, 10))
        combo_w.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        
        combo_h = ttk.Combobox(size_frame, textvariable=self.var_height, values=["384", "512", "704", "768", "896", "1024"], width=7, state="readonly", style='TCombobox')
        combo_h.pack(side=tk.LEFT)
        combo_h.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        row += 1
        
        # Steps & CFG Scale
        tk.Label(scroll_frame, text="Steps / CFG Scale", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        steps_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        steps_frame.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        
        entry_steps = styles.create_custom_entry(steps_frame, textvariable=self.var_steps, width=7)
        entry_steps.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        entry_steps.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_cfg = styles.create_custom_entry(steps_frame, textvariable=self.var_cfg, width=7)
        entry_cfg.pack(side=tk.LEFT, ipady=3)
        entry_cfg.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1
        
        # Guidance Scale
        tk.Label(scroll_frame, text="Guidance Scale", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        entry_guidance = styles.create_custom_entry(scroll_frame, textvariable=self.var_guidance)
        entry_guidance.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0), ipady=3)
        entry_guidance.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1
        
        # Seed & Max VRAM
        tk.Label(scroll_frame, text="Seed / Max VRAM", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        seed_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        seed_frame.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        
        entry_seed = styles.create_custom_entry(seed_frame, textvariable=self.var_seed, width=7)
        entry_seed.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        entry_seed.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_vram = styles.create_custom_entry(seed_frame, textvariable=self.var_max_vram, width=10)
        entry_vram.pack(side=tk.LEFT, ipady=3)
        entry_vram.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1

        # Batch Count & Output Begin Index
        self.label_batch = tk.Label(scroll_frame, text="Batch Count / Begin Index", bg=self.bg_card, fg=self.text_secondary)
        self.label_batch.grid(row=row, column=0, sticky='w', pady=8)
        self.batch_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        self.batch_frame.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        
        entry_batch = styles.create_custom_entry(self.batch_frame, textvariable=self.var_batch_count, width=7)
        entry_batch.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        entry_batch.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_begin_idx = styles.create_custom_entry(self.batch_frame, textvariable=self.var_output_begin_idx, width=7)
        entry_begin_idx.pack(side=tk.LEFT, ipady=3)
        entry_begin_idx.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1

        # Output Field
        self.label_output = tk.Label(scroll_frame, text="Output Filename", bg=self.bg_card, fg=self.text_secondary)
        self.label_output.grid(row=row, column=0, sticky='w', pady=8)
        self.entry_output = styles.create_custom_entry(scroll_frame, textvariable=self.var_output)
        self.entry_output.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0), ipady=4)
        self.entry_output.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1

        # Listen IP / Port (Server only)
        self.label_listen = tk.Label(scroll_frame, text="Listen IP / Port", bg=self.bg_card, fg=self.text_secondary)
        self.label_listen.grid(row=row, column=0, sticky='w', pady=8)
        self.listen_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        self.listen_frame.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        
        self.entry_listen_ip = styles.create_custom_entry(self.listen_frame, textvariable=self.var_listen_ip, width=15)
        self.entry_listen_ip.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        self.entry_listen_ip.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        self.entry_listen_port = styles.create_custom_entry(self.listen_frame, textvariable=self.var_listen_port, width=7)
        self.entry_listen_port.pack(side=tk.LEFT, ipady=3)
        self.entry_listen_port.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1

        # Section Header: Highres Fix & Img2Img
        tk.Label(scroll_frame, text="✨ Highres Fix & Img2Img", bg=self.bg_card, fg=self.accent_blue, font=('Helvetica', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky='w', pady=(15, 8))
        row += 1
        
        # Strength & Enable Hires
        tk.Label(scroll_frame, text="Denoising / Hires Fix", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        hires_act_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        hires_act_frame.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        
        entry_strength = styles.create_custom_entry(hires_act_frame, textvariable=self.var_strength, width=7)
        entry_strength.pack(side=tk.LEFT, padx=(0, 15), ipady=3)
        entry_strength.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        self.chk_hires = tk.Checkbutton(hires_act_frame, text="Enable Hires Fix", variable=self.var_hires, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_hires.pack(side=tk.LEFT)
        row += 1
        
        # Hires Scale & Denoising Strength
        tk.Label(scroll_frame, text="Hires Scale / Denoise", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        hires_scale_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        hires_scale_frame.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        
        entry_hscale = styles.create_custom_entry(hires_scale_frame, textvariable=self.var_hires_scale, width=7)
        entry_hscale.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        entry_hscale.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_hdenoise = styles.create_custom_entry(hires_scale_frame, textvariable=self.var_hires_denoise, width=7)
        entry_hdenoise.pack(side=tk.LEFT, ipady=3)
        entry_hdenoise.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1
        
        # Hires Steps
        tk.Label(scroll_frame, text="Hires Steps", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        entry_hsteps = styles.create_custom_entry(scroll_frame, textvariable=self.var_hires_steps)
        entry_hsteps.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0), ipady=3)
        entry_hsteps.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1

        # Section Header: Sampler & Caching Options
        tk.Label(scroll_frame, text="🌀 Sampler & Cache Settings", bg=self.bg_card, fg=self.accent_blue, font=('Helvetica', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky='w', pady=(15, 8))
        row += 1
        
        # Sampler, Scheduler
        tk.Label(scroll_frame, text="Sampling Method", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        combo_sampler = ttk.Combobox(scroll_frame, textvariable=self.var_sampler, values=["euler", "er_sde", "dpm++2s_a", "euler_a", "dpm++2m_sde", "tcd", "lcm"], state="readonly", style='TCombobox')
        combo_sampler.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        combo_sampler.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="Scheduler", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        combo_sched = ttk.Combobox(scroll_frame, textvariable=self.var_scheduler, values=["discrete", "smoothstep", "karras", "flux2", "ays", "exponential"], state="readonly", style='TCombobox')
        combo_sched.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        combo_sched.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        row += 1
        
        # Cache Mode & Option
        tk.Label(scroll_frame, text="Cache Mode", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        combo_cache = ttk.Combobox(scroll_frame, textvariable=self.var_cache, values=["none", "spectrum", "easycache", "taylorseer", "dbcache"], state="readonly", style='TCombobox')
        combo_cache.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        combo_cache.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="Cache Options", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        entry_cache_opt = styles.create_custom_entry(scroll_frame, textvariable=self.var_cache_option)
        entry_cache_opt.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0), ipady=3)
        entry_cache_opt.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1

        # Section Header: Advanced Options
        tk.Label(scroll_frame, text="🛠️ Advanced & Performance", bg=self.bg_card, fg=self.accent_blue, font=('Helvetica', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky='w', pady=(15, 8))
        row += 1
        
        # VAE Tile Size
        tk.Label(scroll_frame, text="VAE Tile Size", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        entry_vsize = styles.create_custom_entry(scroll_frame, textvariable=self.var_vae_tile_size)
        entry_vsize.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0), ipady=3)
        entry_vsize.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1
        
        # SLG Scale & Skip Layers
        tk.Label(scroll_frame, text="SLG Scale / Skip Layers", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=8)
        slg_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        slg_frame.grid(row=row, column=1, sticky='we', pady=8, padx=(10, 0))
        
        entry_slg = styles.create_custom_entry(slg_frame, textvariable=self.var_slg_scale, width=7)
        entry_slg.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        entry_slg.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_skip = styles.create_custom_entry(slg_frame, textvariable=self.var_skip_layers, width=12)
        entry_skip.pack(side=tk.LEFT, ipady=3)
        entry_skip.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        row += 1

        # Boolean Toggles Group
        tk.Label(scroll_frame, text="Performance Flags", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='nw', pady=10)
        chk_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        chk_frame.grid(row=row, column=1, sticky='we', pady=10, padx=(10, 0))
        
        self.chk_vae = tk.Checkbutton(chk_frame, text="VAE Tiling", variable=self.var_vae_tiling, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_vae.pack(anchor='w', pady=2)
        
        self.chk_offload = tk.Checkbutton(chk_frame, text="Offload to CPU", variable=self.var_offload, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_offload.pack(anchor='w', pady=2)
        
        self.chk_fa = tk.Checkbutton(chk_frame, text="Diffusion FA", variable=self.var_fa, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_fa.pack(anchor='w', pady=2)

        self.chk_circular = tk.Checkbutton(chk_frame, text="Circular Padding (Seamless)", variable=self.var_circular, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_circular.pack(anchor='w', pady=2)
        
        self.chk_metadata = tk.Checkbutton(chk_frame, text="Disable Image Metadata", variable=self.var_disable_metadata, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=('Helvetica', 10), command=self.update_cmd_preview)
        self.chk_metadata.pack(anchor='w', pady=2)
        row += 1
        
        scroll_frame.columnconfigure(1, weight=1)
        
        # --- RIGHT PANE: PREVIEW & LOGS ---
        preview_label = tk.Label(right_frame, text="📋 Generated Command", bg=self.bg_card, fg=self.accent_blue, font=('Helvetica', 12, 'bold'))
        preview_label.pack(anchor='w', padx=20, pady=(20, 5))
        
        self.text_cmd_preview = tk.Text(right_frame, bg=self.terminal_bg, fg=self.accent_blue, insertbackground=self.accent_blue, height=4, font=('Courier', 10), bd=0, highlightthickness=1, highlightbackground=self.border_color, wrap=tk.WORD, padx=10, pady=8)
        self.text_cmd_preview.pack(fill=tk.X, padx=20, pady=5)
        
        # Action Buttons
        btn_frame = tk.Frame(right_frame, bg=self.bg_card)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.btn_copy = ttk.Button(btn_frame, text="📋 Copy Command", command=self.copy_command)
        self.btn_copy.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_start = tk.Button(
            btn_frame,
            text="▶️ Start Process",
            bg=self.btn_green,
            fg="#ffffff",
            font=('Helvetica', 10, 'bold'),
            command=self.start_process,
            bd=0,
            padx=18,
            pady=8,
            activebackground="#059669",
            activeforeground="#ffffff",
            cursor="hand2"
        )
        self.btn_start.pack(side=tk.LEFT, padx=10)
        
        self.btn_stop = tk.Button(
            btn_frame,
            text="⏹️ Stop Process",
            bg="#374151",
            fg=self.text_secondary,
            font=('Helvetica', 10, 'bold'),
            command=self.stop_process,
            bd=0,
            padx=18,
            pady=8,
            state=tk.DISABLED,
            activebackground="#111827",
            activeforeground=self.text_secondary
        )
        self.btn_stop.pack(side=tk.LEFT, padx=10)

        self.label_timer = tk.Label(
            btn_frame,
            text="",
            bg=self.bg_card,
            fg=self.text_secondary,
            font=('Helvetica', 10, 'bold')
        )
        self.label_timer.pack(side=tk.LEFT, padx=15)
        
        # Terminal Header
        console_title_frame = tk.Frame(right_frame, bg=self.bg_card)
        console_title_frame.pack(fill=tk.X, padx=20, pady=(15, 5))
        
        tk.Label(console_title_frame, text="💻 Console Log", bg=self.bg_card, fg=self.accent_blue, font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT)
        
        btn_clear = tk.Button(
            console_title_frame,
            text="Clear Logs",
            bg=self.bg_input,
            fg=self.text_primary,
            activebackground="#374151",
            activeforeground=self.text_primary,
            bd=0,
            padx=10,
            pady=3,
            font=('Helvetica', 9),
            command=self.clear_logs,
            cursor="hand2"
        )
        btn_clear.pack(side=tk.RIGHT)
        
        btn_copy_log = tk.Button(
            console_title_frame,
            text="Copy Logs",
            bg=self.bg_input,
            fg=self.text_primary,
            activebackground="#374151",
            activeforeground=self.text_primary,
            bd=0,
            padx=10,
            pady=3,
            font=('Helvetica', 9),
            command=self.copy_logs,
            cursor="hand2"
        )
        btn_copy_log.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Terminal window
        self.text_terminal = tk.Text(
            right_frame,
            bg=self.terminal_bg,
            fg=self.terminal_fg,
            insertbackground=self.terminal_fg,
            font=('Courier', 9),
            bd=0,
            highlightthickness=1,
            highlightbackground=self.border_color,
            wrap=tk.CHAR,
            padx=10,
            pady=10
        )
        self.text_terminal.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        self.text_terminal.insert(tk.END, "Waiting for process output...\n")
        self.update_layout_for_binary_mode()

    def update_layout_for_binary_mode(self):
        binary = self.var_binary.get()
        if binary == "sd-server":
            # Hide CLI-specific widgets
            self.label_neg_prompt.grid_remove()
            self.entry_neg_prompt.grid_remove()
            self.label_batch.grid_remove()
            self.batch_frame.grid_remove()
            self.label_output.grid_remove()
            self.entry_output.grid_remove()
            
            # Show Server-specific widgets
            self.label_listen.grid()
            self.listen_frame.grid()
        else:
            # Hide Server-specific widgets
            self.label_listen.grid_remove()
            self.listen_frame.grid_remove()
            
            # Show CLI-specific widgets
            self.label_neg_prompt.grid()
            self.entry_neg_prompt.grid()
            self.label_batch.grid()
            self.batch_frame.grid()
            self.label_output.grid()
            self.entry_output.grid()
            
        self.update_cmd_preview()

    def on_prompt_change(self, event):
        text = self.entry_prompt.get("1.0", "end-1c")
        num_lines = len(text.split("\n"))
        try:
            num_display_lines = int(self.entry_prompt.tk.call(self.entry_prompt._w, "count", "-displaylines", "1.0", "end"))
        except Exception:
            num_display_lines = num_lines
            
        new_height = min(max(num_display_lines, 2), 6)
        self.entry_prompt.configure(height=new_height)
        self.update_cmd_preview()

    def on_neg_prompt_change(self, event):
        text = self.entry_neg_prompt.get("1.0", "end-1c")
        num_lines = len(text.split("\n"))
        try:
            num_display_lines = int(self.entry_neg_prompt.tk.call(self.entry_neg_prompt._w, "count", "-displaylines", "1.0", "end"))
        except Exception:
            num_display_lines = num_lines
            
        new_height = min(max(num_display_lines, 2), 5)
        self.entry_neg_prompt.configure(height=new_height)
        self.update_cmd_preview()

    def build_command_list(self):
        binary = self.var_binary.get()
        binary_path = SERVER_PATH if binary == "sd-server" else CLI_PATH
        
        cmd = [binary_path]
        
        model = self.var_model.get().strip()
        vae = self.var_vae.get().strip()
        llm = self.var_llm.get().strip()
        
        if model:
            if not vae and not llm:
                cmd += ["-m", model]
            else:
                cmd += ["--diffusion-model", model]
                
        if vae:
            cmd += ["--vae", vae]
        if llm:
            cmd += ["--llm", llm]
            
        backend = self.var_backend.get()
        if backend:
            cmd += ["--backend", backend]
            
        prompt = self.entry_prompt.get("1.0", "end-1c").strip()
        if prompt:
            cmd += ["-p", prompt]
            
        if binary == "sd-cli":
            neg_prompt = self.entry_neg_prompt.get("1.0", "end-1c").strip()
            if neg_prompt:
                cmd += ["-n", neg_prompt]
            
        steps = self.var_steps.get().strip()
        if steps:
            cmd += ["--steps", steps]
            
        cfg = self.var_cfg.get().strip()
        if cfg:
            cmd += ["--cfg-scale", cfg]
            
        guidance = self.var_guidance.get().strip()
        if guidance:
            cmd += ["--guidance", guidance]
            
        seed = self.var_seed.get().strip()
        if seed:
            cmd += ["--seed", seed]
            
        if binary == "sd-cli":
            batch_count = self.var_batch_count.get().strip()
            if batch_count and batch_count != "1":
                cmd += ["-b", batch_count]
                
            begin_idx = self.var_output_begin_idx.get().strip()
            if begin_idx:
                cmd += ["--output-begin-idx", begin_idx]
            
        w = self.var_width.get()
        if w:
            cmd += ["-W", w]
            
        h = self.var_height.get()
        if h:
            cmd += ["-H", h]
            
        vram = self.var_max_vram.get().strip()
        if vram:
            cmd += ["--max-vram", vram]
            
        sampler = self.var_sampler.get()
        if sampler:
            cmd += ["--sampling-method", sampler]
            
        sched = self.var_scheduler.get()
        if sched:
            cmd += ["--scheduler", sched]
            
        cache = self.var_cache.get()
        if cache != "none":
            cmd += ["--cache-mode", cache]
            
        cache_opt = self.var_cache_option.get().strip()
        if cache_opt:
            cmd += ["--cache-option", cache_opt]
            
        strength = self.var_strength.get().strip()
        if strength:
            cmd += ["--strength", strength]
            
        if self.var_hires.get():
            cmd += ["--hires"]
            
        hscale = self.var_hires_scale.get().strip()
        if hscale:
            cmd += ["--hires-scale", hscale]
            
        hdenoise = self.var_hires_denoise.get().strip()
        if hdenoise:
            cmd += ["--hires-denoising-strength", hdenoise]
            
        hsteps = self.var_hires_steps.get().strip()
        if hsteps:
            cmd += ["--hires-steps", hsteps]
            
        slg = self.var_slg_scale.get().strip()
        if slg:
            cmd += ["--slg-scale", slg]
            
        skip = self.var_skip_layers.get().strip()
        if skip:
            cmd += ["--skip-layers", skip]
            
        vsize = self.var_vae_tile_size.get().strip()
        if vsize:
            cmd += ["--vae-tile-size", vsize]
            
        if self.var_vae_tiling.get():
            cmd += ["--vae-tiling"]
        if self.var_offload.get():
            cmd += ["--offload-to-cpu"]
        if self.var_fa.get():
            cmd += ["--diffusion-fa"]
        if self.var_circular.get():
            cmd += ["--circular"]
        if self.var_disable_metadata.get():
            cmd += ["--disable-image-metadata"]
            
        if binary == "sd-cli":
            out = self.var_output.get().strip()
            if out:
                if out.startswith("output/"):
                    cmd += ["-o", out]
                else:
                    clean_out = out.lstrip("/")
                    cmd += ["-o", f"output/{clean_out}"]
        elif binary == "sd-server":
            ip = self.var_listen_ip.get().strip()
            if ip:
                cmd += ["--listen-ip", ip]
            port = self.var_listen_port.get().strip()
            if port:
                cmd += ["--listen-port", port]
                
        return cmd

    def update_cmd_preview(self):
        cmd = self.build_command_list()
        
        # Replace executable paths with short names for preview readability
        preview_cmd = list(cmd)
        if len(preview_cmd) > 0:
            preview_cmd[0] = self.var_binary.get()
            
        cmd_string = " ".join(preview_cmd)
        self.text_cmd_preview.delete("1.0", tk.END)
        self.text_cmd_preview.insert("1.0", cmd_string)

    def copy_command(self):
        cmd = self.build_command_list()
        self.copy_to_clipboard(" ".join(cmd))
        self.show_toast("📋 Command copied to clipboard!")

    def on_profile_selected(self, event):
        name = self.combo_profile.get()
        if not name:
            return
            
        profile_path = os.path.join(PROFILES_DIR, f"{name}.env")
        config = profile_manager.parse_env_file(profile_path)
        
        # Fill inputs
        if "BINARY" in config: self.var_binary.set(config["BINARY"])
        if "MODEL" in config: self.var_model.set(config["MODEL"])
        if "VAE" in config: self.var_vae.set(config["VAE"])
        if "LLM" in config: self.var_llm.set(config["LLM"])
        if "BACKEND" in config: self.var_backend.set(config["BACKEND"])
        
        # Prompt
        self.entry_prompt.delete("1.0", tk.END)
        if "PROMPT" in config:
            self.entry_prompt.insert("1.0", config["PROMPT"])
        self.on_prompt_change(None)
            
        # Negative Prompt
        self.entry_neg_prompt.delete("1.0", tk.END)
        if "NEGATIVE_PROMPT" in config:
            self.entry_neg_prompt.insert("1.0", config["NEGATIVE_PROMPT"])
        self.on_neg_prompt_change(None)
            
        if "WIDTH" in config: self.var_width.set(config["WIDTH"])
        if "HEIGHT" in config: self.var_height.set(config["HEIGHT"])
        if "STEPS" in config: self.var_steps.set(config["STEPS"])
        if "CFG_SCALE" in config: self.var_cfg.set(config["CFG_SCALE"])
        if "GUIDANCE" in config: self.var_guidance.set(config["GUIDANCE"])
        if "SEED" in config: self.var_seed.set(config["SEED"])
        if "BATCH_COUNT" in config: self.var_batch_count.set(config["BATCH_COUNT"])
        if "OUTPUT_BEGIN_IDX" in config: self.var_output_begin_idx.set(config["OUTPUT_BEGIN_IDX"])
        if "MAX_VRAM" in config: self.var_max_vram.set(config["MAX_VRAM"])
        if "SAMPLING_METHOD" in config: self.var_sampler.set(config["SAMPLING_METHOD"])
        if "SCHEDULER" in config: self.var_scheduler.set(config["SCHEDULER"])
        if "CACHE_MODE" in config: self.var_cache.set(config["CACHE_MODE"])
        if "CACHE_OPTION" in config: self.var_cache_option.set(config["CACHE_OPTION"])
        
        if "STRENGTH" in config: self.var_strength.set(config["STRENGTH"])
        if "HIRES" in config: self.var_hires.set(config["HIRES"].lower() == "true")
        if "HIRES_SCALE" in config: self.var_hires_scale.set(config["HIRES_SCALE"])
        if "HIRES_DENOISING_STRENGTH" in config: self.var_hires_denoise.set(config["HIRES_DENOISING_STRENGTH"])
        if "HIRES_STEPS" in config: self.var_hires_steps.set(config["HIRES_STEPS"])
        
        if "SLG_SCALE" in config: self.var_slg_scale.set(config["SLG_SCALE"])
        if "SKIP_LAYERS" in config: self.var_skip_layers.set(config["SKIP_LAYERS"])
        if "VAE_TILE_SIZE" in config: self.var_vae_tile_size.set(config["VAE_TILE_SIZE"])
        
        if "CIRCULAR" in config: self.var_circular.set(config["CIRCULAR"].lower() == "true")
        if "DISABLE_IMAGE_METADATA" in config: self.var_disable_metadata.set(config["DISABLE_IMAGE_METADATA"].lower() == "true")
        
        if "OUTPUT" in config: 
            out = config["OUTPUT"]
            if out.startswith("output/"):
                out = out[7:]
            self.var_output.set(out)
        
        if "VAE_TILING" in config: self.var_vae_tiling.set(config["VAE_TILING"].lower() == "true")
        if "OFFLOAD_TO_CPU" in config: self.var_offload.set(config["OFFLOAD_TO_CPU"].lower() == "true")
        if "DIFFUSION_FA" in config: self.var_fa.set(config["DIFFUSION_FA"].lower() == "true")
        
        if "LISTEN_IP" in config: self.var_listen_ip.set(config["LISTEN_IP"])
        if "LISTEN_PORT" in config: self.var_listen_port.set(config["LISTEN_PORT"])
        
        self.entry_save_name.delete(0, tk.END)
        self.entry_save_name.insert(0, name)
        
        self.update_layout_for_binary_mode()

    def save_profile(self):
        name = self.entry_save_name.get().strip()
        if not name:
            messagebox.showwarning("⚠️ Name Required", "Please enter a profile name first.")
            return
            
        out_val = self.var_output.get().strip()
        if out_val and not out_val.startswith("output/"):
            out_val = f"output/{out_val}"

        config = {
            "BINARY": self.var_binary.get(),
            "MODEL": self.var_model.get(),
            "VAE": self.var_vae.get(),
            "LLM": self.var_llm.get(),
            "BACKEND": self.var_backend.get(),
            "PROMPT": self.entry_prompt.get("1.0", "end-1c").strip(),
            "NEGATIVE_PROMPT": self.entry_neg_prompt.get("1.0", "end-1c").strip(),
            "WIDTH": self.var_width.get(),
            "HEIGHT": self.var_height.get(),
            "STEPS": self.var_steps.get(),
            "CFG_SCALE": self.var_cfg.get(),
            "GUIDANCE": self.var_guidance.get(),
            "SEED": self.var_seed.get(),
            "BATCH_COUNT": self.var_batch_count.get().strip(),
            "OUTPUT_BEGIN_IDX": self.var_output_begin_idx.get().strip(),
            "MAX_VRAM": self.var_max_vram.get(),
            "SAMPLING_METHOD": self.var_sampler.get(),
            "SCHEDULER": self.var_scheduler.get(),
            "CACHE_MODE": self.var_cache.get(),
            "CACHE_OPTION": self.var_cache_option.get().strip(),
            "STRENGTH": self.var_strength.get().strip(),
            "HIRES": str(self.var_hires.get()).lower(),
            "HIRES_SCALE": self.var_hires_scale.get().strip(),
            "HIRES_DENOISING_STRENGTH": self.var_hires_denoise.get().strip(),
            "HIRES_STEPS": self.var_hires_steps.get().strip(),
            "SLG_SCALE": self.var_slg_scale.get().strip(),
            "SKIP_LAYERS": self.var_skip_layers.get().strip(),
            "VAE_TILE_SIZE": self.var_vae_tile_size.get().strip(),
            "CIRCULAR": str(self.var_circular.get()).lower(),
            "DISABLE_IMAGE_METADATA": str(self.var_disable_metadata.get()).lower(),
            "OUTPUT": out_val,
            "VAE_TILING": str(self.var_vae_tiling.get()).lower(),
            "OFFLOAD_TO_CPU": str(self.var_offload.get()).lower(),
            "DIFFUSION_FA": str(self.var_fa.get()).lower(),
            "LISTEN_IP": self.var_listen_ip.get().strip(),
            "LISTEN_PORT": self.var_listen_port.get().strip(),
        }
        
        profile_path = os.path.join(PROFILES_DIR, f"{name}.env")
        profile_manager.write_env_file(profile_path, config)
        
        self.load_profiles_list()
        self.combo_profile.set(name)
        self.show_toast(f"💾 Profile '{name}' saved!")

    def clear_logs(self):
        self.text_terminal.delete("1.0", tk.END)

    def copy_logs(self):
        logs = self.text_terminal.get("1.0", tk.END)
        # Limit to last 50,000 characters to prevent clipboard bloat
        max_len = 50000
        if len(logs) > max_len:
            logs = f"[Logs truncated - showing last {max_len} characters]\n" + logs[-max_len:]
        self.copy_to_clipboard(logs.strip())
        if len(logs) > max_len:
            self.show_toast("📋 Logs copied (trimmed)!")
        else:
            self.show_toast("📋 Console logs copied!")

    def show_toast(self, message, duration=1500):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.configure(bg=self.bg_input)
        
        self.root.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        
        # Center horizontally, 85% down vertically
        tx = rx + (rw // 2) - 130
        ty = ry + (rh * 85 // 100) - 20
        toast.geometry(f"+{tx}+{ty}")
        
        label = tk.Label(
            toast,
            text=message,
            bg=self.bg_input,
            fg=self.accent_blue,
            font=('Helvetica', 10, 'bold'),
            padx=15,
            pady=8,
            bd=1,
            relief=tk.SOLID,
            highlightbackground=self.border_color,
            highlightthickness=1
        )
        label.pack()
        toast.after(duration, toast.destroy)

    def copy_to_clipboard(self, text):
        """Safely copy to system clipboard by directly invoking wl-copy (Wayland)."""
        try:
            p = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE, text=True)
            p.communicate(input=text)
        except Exception as e:
            print(f"Error copying to clipboard via wl-copy: {e}", file=sys.stderr)

    def start_process(self):
        if self.runner.is_running:
            return
            
        cmd = self.build_command_list()
        binary_path = cmd[0]
        
        if not os.path.exists(binary_path):
            messagebox.showerror("❌ Error", f"Binary not found at:\n{binary_path}\nPlease build stable-diffusion.cpp first.")
            return
            
        self.clear_logs()
        self.text_terminal.insert(tk.END, f"🚀 Launching subprocess: {' '.join(cmd)}\n\n")
        
        self.btn_start.configure(state=tk.DISABLED, bg="#1f2937", fg=self.text_secondary)
        self.btn_stop.configure(state=tk.NORMAL, bg=self.btn_red, fg="#ffffff", cursor="hand2")
        
        # Start elapsed timer
        self.start_time = time.time()
        self.timer_running = True
        self.label_timer.configure(text="⏱️ 0.0s", fg=self.accent_blue)
        self.root.after(100, self.update_timer)
        
        # Start subprocess
        self.runner.start(cmd, WORKSPACE_DIR)

    def stop_process(self):
        self.runner.stop()

    def poll_log_queue(self):
        try:
            while True:
                line = self.log_queue.get_nowait()
                if line == "__PROCESS_DONE__":
                    self.btn_start.configure(state=tk.NORMAL, bg=self.btn_green, fg="#ffffff")
                    self.btn_stop.configure(state=tk.DISABLED, bg="#374151", fg=self.text_secondary, cursor="")
                    
                    self.timer_running = False
                    if self.start_time:
                        elapsed = time.time() - self.start_time
                        self.label_timer.configure(text=f"⏱️ Finished in {elapsed:.1f}s", fg=self.btn_green)
                else:
                    self.text_terminal.insert(tk.END, line)
                    self.text_terminal.see(tk.END)
        except queue.Empty:
            pass
        self.root.after(100, self.poll_log_queue)

    def update_timer(self):
        if self.runner.is_running and self.timer_running and self.start_time:
            elapsed = time.time() - self.start_time
            self.label_timer.configure(text=f"⏱️ {elapsed:.1f}s")
            self.root.after(100, self.update_timer)

    def on_close(self):
        if self.runner.is_running:
            if messagebox.askokcancel("Quit", "A model generation process is currently running. Do you want to terminate it and quit?"):
                self.runner.kill_force()
                self.root.destroy()
        else:
            self.root.destroy()
