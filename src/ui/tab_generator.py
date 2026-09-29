import os
import sys
import glob
import shlex
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import styles
import resolution
from ui.widgets import CollapsibleFrame, setup_filterable_combobox
from ui.tab_gallery import GalleryTab
from ui.tab_prompt_helper import PromptHelperTab
from ui.tab_history import HistoryTab
from art_styles import ART_STYLES

# Megapixel budget stepping, matching ComfyUI's ResolutionSelector range
MP_MIN = 0.1
MP_MAX = 16.0
MP_STEP = 0.1

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

        self.latest_photo = None
        self.latest_image_path = None

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
        self.var_aspect_ratio = app.var_aspect_ratio
        self.var_megapixels = app.var_megapixels
        self.var_res_multiple = app.var_res_multiple
        self.var_steps = app.var_steps
        self.var_cfg = app.var_cfg
        self.var_guidance = app.var_guidance
        self.var_seed = app.var_seed
        self.var_batch_count = app.var_batch_count
        self.var_output_begin_idx = app.var_output_begin_idx
        self.var_max_vram = app.var_max_vram
        self.var_sampler = app.var_sampler
        self.var_scheduler = app.var_scheduler
        self.sampling_method_options = app.sampling_method_options
        self.scheduler_options = app.scheduler_options
        self.cache_mode_options = app.cache_mode_options
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
        self.var_lora_dir = app.var_lora_dir
        self.var_lora_apply_mode = app.var_lora_apply_mode
        self.var_lora_enabled = app.var_lora_enabled
        self.var_lora_strength = app.var_lora_strength
        
        self.var_vae_tiling = app.var_vae_tiling
        self.var_vae_conv_direct = app.var_vae_conv_direct
        self.var_offload = app.var_offload
        self.var_fa = app.var_fa
        self.var_circular = app.var_circular
        self.var_disable_metadata = app.var_disable_metadata

        # MiniMax-H3 & Ref2VA variables
        self.var_audio_vae = app.var_audio_vae
        self.var_llm_vision = app.var_llm_vision
        self.var_fps = app.var_fps
        self.var_video_seconds = app.var_video_seconds
        self.var_end_img = app.var_end_img
        self.var_ref_img = app.var_ref_img
        self.var_ref_video = app.var_ref_video
        self.var_ref_audio = app.var_ref_audio
        self.var_ref_video_audio = app.var_ref_video_audio

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
        
        # Lives in the header rather than the scrolling form so it stays
        # reachable without scrolling back to the top of the parameters.
        btn_reload = ttk.Button(header_profile, text="Reload", command=self.app.reload_workspace)
        btn_reload.pack(side=tk.RIGHT)
        
        profile_frame = tk.Frame(left_frame, bg=self.bg_card)
        profile_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.combo_profile = ttk.Combobox(profile_frame, width=15, state="readonly", style='TCombobox')
        self.combo_profile.pack(side=tk.LEFT, padx=(0, 6))
        self.combo_profile.bind("<<ComboboxSelected>>", self.app.on_profile_selected)
        
        self.entry_save_name = styles.create_custom_entry(profile_frame, width=14)
        self.entry_save_name.pack(side=tk.LEFT, padx=6, ipady=3)
        
        btn_save = ttk.Button(profile_frame, text="Save", command=self.app.save_profile)
        btn_save.pack(side=tk.LEFT, padx=6)
        
        btn_rename = ttk.Button(profile_frame, text="Rename", command=self.app.rename_profile)
        btn_rename.pack(side=tk.LEFT, padx=6)
        
        btn_delete = ttk.Button(profile_frame, text="Delete", command=self.app.delete_profile)
        btn_delete.pack(side=tk.LEFT, padx=6)
        
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
        
        styles.enable_mousewheel_scrolling(left_frame, self.form_canvas)
        
        row = 0
        tk.Label(scroll_frame, text="Base Generation", bg=self.bg_card, fg=self.accent_blue, font=styles.FONT_BOLD).grid(row=row, column=0, columnspan=2, sticky='w', pady=(5, 6))
        row += 1

        tk.Label(scroll_frame, text="Binary Mode", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        self.combo_binary = ttk.Combobox(scroll_frame, textvariable=self.var_binary, values=["sd-cli", "sd-server"], state="readonly", style='TCombobox')
        self.combo_binary.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.combo_binary.bind("<<ComboboxSelected>>", lambda e: self.update_layout_for_binary_mode())
        row += 1

        tk.Label(scroll_frame, text="Generation Mode (-M)", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        combo_mode = ttk.Combobox(scroll_frame, textvariable=self.var_mode, values=["img_gen", "adetailer", "vid_gen", "convert", "upscale", "metadata"], state="readonly", style='TCombobox')
        combo_mode.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        combo_mode.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="Backend Execution", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        combo_backend = ttk.Combobox(scroll_frame, textvariable=self.var_backend, values=["llm=cpu", "llm=gpu", "cpu", "gpu"], state="readonly", style='TCombobox')
        combo_backend.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        combo_backend.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="Diffusion Model", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        model_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        model_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.combo_model = ttk.Combobox(model_frame, textvariable=self.var_model, style='TCombobox')
        self.combo_model.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=3)
        setup_filterable_combobox(self.combo_model, lambda: self.app.scanned_models, lambda e=None: self.update_cmd_preview())
        btn_browse_model = ttk.Button(model_frame, text=">", width=2, command=self.browse_model)
        btn_browse_model.pack(side=tk.LEFT)
        row += 1
        
        tk.Label(scroll_frame, text="Text Encoder (T5XXL)", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        t5_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        t5_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.combo_t5xxl = ttk.Combobox(t5_frame, textvariable=self.var_t5xxl, style='TCombobox')
        self.combo_t5xxl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=3)
        setup_filterable_combobox(self.combo_t5xxl, lambda: self.app.scanned_models, lambda e=None: self.update_cmd_preview())
        btn_browse_t5xxl = ttk.Button(t5_frame, text=">", width=2, command=self.browse_t5xxl)
        btn_browse_t5xxl.pack(side=tk.LEFT)
        row += 1
        
        tk.Label(scroll_frame, text="Text Encoder (LLM)", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        llm_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        llm_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.combo_llm = ttk.Combobox(llm_frame, textvariable=self.var_llm, style='TCombobox')
        self.combo_llm.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=3)
        setup_filterable_combobox(self.combo_llm, lambda: self.app.scanned_models, lambda e=None: self.update_cmd_preview())
        btn_browse_llm = ttk.Button(llm_frame, text=">", width=2, command=self.browse_llm)
        btn_browse_llm.pack(side=tk.LEFT)
        row += 1
        
        tk.Label(scroll_frame, text="VAE Decoder", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        vae_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        vae_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.combo_vae = ttk.Combobox(vae_frame, textvariable=self.var_vae, style='TCombobox')
        self.combo_vae.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=3)
        setup_filterable_combobox(self.combo_vae, lambda: self.app.scanned_models, lambda e=None: self.update_cmd_preview())
        btn_browse_vae = ttk.Button(vae_frame, text=">", width=2, command=self.browse_vae)
        btn_browse_vae.pack(side=tk.LEFT)
        row += 1
        
        tk.Label(scroll_frame, text="LLM Vision Tower", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        llm_vision_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        llm_vision_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.combo_llm_vision = ttk.Combobox(llm_vision_frame, textvariable=self.var_llm_vision, style='TCombobox')
        self.combo_llm_vision.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=3)
        setup_filterable_combobox(self.combo_llm_vision, lambda: self.app.scanned_models, lambda e=None: self.update_cmd_preview())
        btn_browse_llm_vision = ttk.Button(llm_vision_frame, text=">", width=2, command=self.browse_llm_vision)
        btn_browse_llm_vision.pack(side=tk.LEFT)
        row += 1

        tk.Label(scroll_frame, text="Audio VAE Decoder", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        audio_vae_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        audio_vae_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        self.combo_audio_vae = ttk.Combobox(audio_vae_frame, textvariable=self.var_audio_vae, style='TCombobox')
        self.combo_audio_vae.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=3)
        setup_filterable_combobox(self.combo_audio_vae, lambda: self.app.scanned_models, lambda e=None: self.update_cmd_preview())
        btn_browse_audio_vae = ttk.Button(audio_vae_frame, text=">", width=2, command=self.browse_audio_vae)
        btn_browse_audio_vae.pack(side=tk.LEFT)
        row += 1
        
        # Art Style Row
        tk.Label(scroll_frame, text="Art Style", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        art_style_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        art_style_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        
        art_style_names = ["None"] + [name for name, _, _ in ART_STYLES]
        self.combo_art_style = ttk.Combobox(art_style_frame, textvariable=self.app.var_art_style, values=art_style_names, state="readonly", style='TCombobox')
        self.combo_art_style.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.combo_art_style.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        row += 1
        
        tk.Label(scroll_frame, text="Prompt", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='nw', pady=6)
        prompt_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        prompt_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        prompt_frame.columnconfigure(0, weight=1)
        self.entry_prompt = styles.create_custom_text(prompt_frame, height=3)
        self.entry_prompt.grid(row=0, column=0, sticky='nsew')
        prompt_scroll = tk.Scrollbar(prompt_frame, orient="vertical", command=self.entry_prompt.yview)
        prompt_scroll.grid(row=0, column=1, sticky='ns')
        self.entry_prompt.configure(yscrollcommand=prompt_scroll.set)
        self.entry_prompt.bind("<KeyRelease>", self.on_prompt_change)
        for seq in ("<Button-4>", "<Button-5>", "<MouseWheel>"):
            self.entry_prompt.bind(seq, self._scroll_text_widget, add="+")
        row += 1
        
        self.label_neg_prompt = tk.Label(scroll_frame, text="Negative Prompt", bg=self.bg_card, fg=self.text_secondary)
        self.label_neg_prompt.grid(row=row, column=0, sticky='nw', pady=6)
        neg_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        neg_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        neg_frame.columnconfigure(0, weight=1)
        self.entry_neg_prompt = styles.create_custom_text(neg_frame, height=2)
        self.entry_neg_prompt.grid(row=0, column=0, sticky='nsew')
        neg_scroll = tk.Scrollbar(neg_frame, orient="vertical", command=self.entry_neg_prompt.yview)
        neg_scroll.grid(row=0, column=1, sticky='ns')
        self.entry_neg_prompt.configure(yscrollcommand=neg_scroll.set)
        self.entry_neg_prompt.bind("<KeyRelease>", self.on_neg_prompt_change)
        for seq in ("<Button-4>", "<Button-5>", "<MouseWheel>"):
            self.entry_neg_prompt.bind(seq, self._scroll_text_widget, add="+")
        row += 1
        
        tk.Label(scroll_frame, text="Image Size (W / H)", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        size_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        size_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        
        combo_w = ttk.Combobox(size_frame, textvariable=self.var_width, values=["384", "512", "704", "768", "832", "896", "1024"], width=7, style='TCombobox')
        combo_w.pack(side=tk.LEFT, padx=(0, 8))
        combo_w.bind("<<ComboboxSelected>>", lambda e: self.on_size_change())
        combo_w.bind("<KeyRelease>", lambda e: self.on_size_change())
        
        combo_h = ttk.Combobox(size_frame, textvariable=self.var_height, values=["384", "480", "512", "704", "768", "896", "1024"], width=7, style='TCombobox')
        combo_h.pack(side=tk.LEFT)
        combo_h.bind("<<ComboboxSelected>>", lambda e: self.on_size_change())
        combo_h.bind("<KeyRelease>", lambda e: self.on_size_change())
        row += 1
        
        # Resolution picker: aspect ratio + megapixel budget -> width/height
        # Split across two rows; the sidebar is too narrow to fit the combobox,
        # the MP stepper and the step field on a single line.
        tk.Label(scroll_frame, text="Aspect Ratio", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        res_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        res_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        
        self.combo_aspect_ratio = ttk.Combobox(
            res_frame, textvariable=self.var_aspect_ratio,
            values=resolution.ASPECT_RATIO_LABELS, state="readonly",
            style='TCombobox'
        )
        self.combo_aspect_ratio.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.combo_aspect_ratio.bind("<<ComboboxSelected>>", lambda e: self.on_resolution_change())
        row += 1
        
        tk.Label(scroll_frame, text="Resolution", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        mp_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        mp_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        
        entry_mp = styles.create_custom_entry(mp_frame, textvariable=self.var_megapixels, width=5)
        entry_mp.pack(side=tk.LEFT, ipady=3)
        entry_mp.bind("<KeyRelease>", lambda e: self.on_resolution_change())
        entry_mp.bind("<FocusOut>", lambda e: self.on_resolution_change())
        
        btn_mp_down = ttk.Button(mp_frame, text="-", width=2, command=lambda: self.step_megapixels(-MP_STEP))
        btn_mp_down.pack(side=tk.LEFT, padx=(3, 2))
        btn_mp_up = ttk.Button(mp_frame, text="+", width=2, command=lambda: self.step_megapixels(MP_STEP))
        btn_mp_up.pack(side=tk.LEFT, padx=(0, 6))
        
        tk.Label(mp_frame, text="MP", bg=self.bg_card, fg=self.text_secondary, font=styles.FONT_SMALL).pack(side=tk.LEFT, padx=(0, 10))
        
        entry_mult = styles.create_custom_entry(mp_frame, textvariable=self.var_res_multiple, width=4)
        entry_mult.pack(side=tk.LEFT, ipady=3)
        entry_mult.bind("<KeyRelease>", lambda e: self.on_resolution_change())
        entry_mult.bind("<FocusOut>", lambda e: self.on_resolution_change())
        
        tk.Label(mp_frame, text="/ step", bg=self.bg_card, fg=self.text_secondary, font=styles.FONT_SMALL).pack(side=tk.LEFT, padx=(4, 0))
        
        self.label_mp_readout = tk.Label(mp_frame, text="", bg=self.bg_card, fg=self.accent_blue, font=styles.FONT_SMALL)
        self.label_mp_readout.pack(side=tk.RIGHT)
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
        
        tk.Label(scroll_frame, text="Seed", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        seed_frame = tk.Frame(scroll_frame, bg=self.bg_card)
        seed_frame.grid(row=row, column=1, sticky='we', pady=6, padx=(10, 0))
        
        self.entry_seed = styles.create_custom_entry(seed_frame, textvariable=self.var_seed, width=10)
        self.entry_seed.pack(side=tk.LEFT, padx=(0, 4), ipady=3)
        self.entry_seed.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        self.btn_reuse_seed = ttk.Button(seed_frame, text="Reuse", width=6, command=self.app.apply_previous_seed)
        self.btn_reuse_seed.pack(side=tk.LEFT, padx=(0, 8))
        
        self.chk_random_seed = tk.Checkbutton(
            seed_frame, text="Random", variable=self.app.var_random_seed,
            bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main,
            activebackground=self.bg_card, activeforeground=self.text_primary,
            font=styles.FONT_MAIN, command=self.on_random_seed_toggle
        )
        self.chk_random_seed.pack(side=tk.LEFT, padx=(0, 10))
        row += 1

        tk.Label(scroll_frame, text="Max VRAM", bg=self.bg_card, fg=self.text_secondary).grid(row=row, column=0, sticky='w', pady=6)
        entry_vram = styles.create_custom_entry(scroll_frame, textvariable=self.var_max_vram, width=8)
        entry_vram.grid(row=row, column=1, sticky='w', pady=6, padx=(10, 0), ipady=3)
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

        # --- ACCORDION COLLAPSIBLE SECTIONS (SD-SERVER ALIGNED SECTIONS) ---

        # 1. Section: Sample & Steps
        c_sample = CollapsibleFrame(scroll_frame, title="Sample & Steps", bg_card=self.bg_card, accent_blue=self.accent_blue, text_primary=self.text_primary, expanded=False, on_toggle=self.update_scrollregion)
        c_sample.grid(row=row, column=0, columnspan=2, sticky='we', pady=(8, 2))
        row += 1
        
        f_samp = c_sample.content
        f_samp.columnconfigure(1, weight=1)
        r_sub = 0

        tk.Label(f_samp, text="Sampling Method", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        self.combo_sampler = ttk.Combobox(f_samp, textvariable=self.var_sampler, values=self.sampling_method_options, state="readonly", style='TCombobox')
        self.combo_sampler.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        self.combo_sampler.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_samp, text="Scheduler", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        self.combo_sched = ttk.Combobox(f_samp, textvariable=self.var_scheduler, values=[""] + self.scheduler_options, state="readonly", style='TCombobox')
        self.combo_sched.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        self.combo_sched.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_samp, text="Flow Shift / Sec / Frames / FPS", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        vid_frame = tk.Frame(f_samp, bg=self.bg_card)
        vid_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        
        entry_flow = styles.create_custom_entry(vid_frame, textvariable=self.var_flow_shift, width=5)
        entry_flow.pack(side=tk.LEFT, padx=(0, 5), ipady=3)
        entry_flow.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_vsec = styles.create_custom_entry(vid_frame, textvariable=self.var_video_seconds, width=6)
        entry_vsec.pack(side=tk.LEFT, padx=(0, 5), ipady=3)
        entry_vsec.bind("<KeyRelease>", self.on_video_seconds_change)

        entry_vframes = styles.create_custom_entry(vid_frame, textvariable=self.var_video_frames, width=6)
        entry_vframes.pack(side=tk.LEFT, padx=(0, 5), ipady=3)
        entry_vframes.bind("<KeyRelease>", self.on_video_frames_change)

        entry_fps = styles.create_custom_entry(vid_frame, textvariable=self.var_fps, width=5)
        entry_fps.pack(side=tk.LEFT, ipady=3)
        entry_fps.bind("<KeyRelease>", self.on_fps_change)
        r_sub += 1

        # 2. Section: Guidance & SLG
        c_guidance = CollapsibleFrame(scroll_frame, title="Guidance & SLG", bg_card=self.bg_card, accent_blue=self.accent_blue, text_primary=self.text_primary, expanded=False, on_toggle=self.update_scrollregion)
        c_guidance.grid(row=row, column=0, columnspan=2, sticky='we', pady=(4, 2))
        row += 1

        f_guide = c_guidance.content
        f_guide.columnconfigure(1, weight=1)
        r_sub = 0

        tk.Label(f_guide, text="Distilled Guidance", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        entry_guidance = styles.create_custom_entry(f_guide, textvariable=self.var_guidance, width=10)
        entry_guidance.grid(row=r_sub, column=1, sticky='w', pady=4, padx=(8, 0), ipady=3)
        entry_guidance.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_guide, text="SLG Scale / Skip Layers", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        slg_frame = tk.Frame(f_guide, bg=self.bg_card)
        slg_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        
        entry_slg = styles.create_custom_entry(slg_frame, textvariable=self.var_slg_scale, width=7)
        entry_slg.pack(side=tk.LEFT, padx=(0, 8), ipady=3)
        entry_slg.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        entry_skip = styles.create_custom_entry(slg_frame, textvariable=self.var_skip_layers, width=10)
        entry_skip.pack(side=tk.LEFT, ipady=3)
        entry_skip.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        # 3. Section: LoRA Configuration
        c_lora = CollapsibleFrame(scroll_frame, title="LoRA Configuration", bg_card=self.bg_card, accent_blue=self.accent_blue, text_primary=self.text_primary, expanded=False, on_toggle=self.update_scrollregion)
        c_lora.grid(row=row, column=0, columnspan=2, sticky='we', pady=(4, 2))
        row += 1

        f_lora = c_lora.content
        f_lora.columnconfigure(1, weight=1)
        r_sub = 0

        tk.Label(f_lora, text="Enable / Strength", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        lora_top_frame = tk.Frame(f_lora, bg=self.bg_card)
        lora_top_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))

        chk_lora_en = tk.Checkbutton(
            lora_top_frame, text="Enable LoRA", variable=self.var_lora_enabled,
            bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main,
            activebackground=self.bg_card, activeforeground=self.text_primary,
            font=styles.FONT_MAIN, command=self.update_cmd_preview
        )
        chk_lora_en.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(lora_top_frame, text="Multiplier", bg=self.bg_card, fg=self.text_secondary).pack(side=tk.LEFT, padx=(0, 5))
        entry_lora_str = styles.create_custom_entry(lora_top_frame, textvariable=self.var_lora_strength, width=6)
        entry_lora_str.pack(side=tk.LEFT, ipady=3)
        entry_lora_str.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_lora, text="LoRA Directory / Model", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        lora_frame = tk.Frame(f_lora, bg=self.bg_card)
        lora_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        
        self.combo_lora_dir = ttk.Combobox(lora_frame, textvariable=self.var_lora_dir, style='TCombobox')
        self.combo_lora_dir.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
        setup_filterable_combobox(self.combo_lora_dir, lambda: ["lora"] + self.app.scanned_loras, lambda e=None: self.update_cmd_preview())
        
        btn_browse_lora = ttk.Button(lora_frame, text=">", width=2, command=self.browse_lora_dir)
        btn_browse_lora.pack(side=tk.LEFT)
        r_sub += 1

        tk.Label(f_lora, text="LoRA Apply Mode", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        combo_lora_mode = ttk.Combobox(f_lora, textvariable=self.var_lora_apply_mode, values=["", "auto", "immediately", "at_runtime"], state="readonly", style='TCombobox')
        combo_lora_mode.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        combo_lora_mode.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        r_sub += 1

        # 4. Section: Image-to-Image & Highres Fix
        c_hires = CollapsibleFrame(scroll_frame, title="Image-to-Image & Highres Fix", bg_card=self.bg_card, accent_blue=self.accent_blue, text_primary=self.text_primary, expanded=False, on_toggle=self.update_scrollregion)
        c_hires.grid(row=row, column=0, columnspan=2, sticky='we', pady=(4, 2))
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
        
        btn_browse_init = ttk.Button(init_frame, text=">", width=2, command=self.browse_init_image)
        btn_browse_init.pack(side=tk.LEFT)
        r_sub += 1

        tk.Label(f_hires, text="End Image (--end-img)", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        end_frame = tk.Frame(f_hires, bg=self.bg_card)
        end_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        
        entry_end = styles.create_custom_entry(end_frame, textvariable=self.var_end_img)
        entry_end.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
        entry_end.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        btn_browse_end = ttk.Button(end_frame, text=">", width=2, command=self.browse_end_image)
        btn_browse_end.pack(side=tk.LEFT)
        r_sub += 1

        tk.Label(f_hires, text="Denoise / Hires Fix", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        hires_act_frame = tk.Frame(f_hires, bg=self.bg_card)
        hires_act_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        
        entry_strength = styles.create_custom_entry(hires_act_frame, textvariable=self.var_strength, width=7)
        entry_strength.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        entry_strength.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        
        self.chk_hires = tk.Checkbutton(hires_act_frame, text="Enable Hires Fix", variable=self.var_hires, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=styles.FONT_MAIN, command=self.update_cmd_preview)
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

        # 5. Section: VAE & Performance Flags
        c_vae = CollapsibleFrame(scroll_frame, title="VAE & Performance Flags", bg_card=self.bg_card, accent_blue=self.accent_blue, text_primary=self.text_primary, expanded=False, on_toggle=self.update_scrollregion)
        c_vae.grid(row=row, column=0, columnspan=2, sticky='we', pady=(4, 2))
        row += 1

        f_vae = c_vae.content
        f_vae.columnconfigure(1, weight=1)
        r_sub = 0

        tk.Label(f_vae, text="VAE Tile Size", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        entry_vsize = styles.create_custom_entry(f_vae, textvariable=self.var_vae_tile_size)
        entry_vsize.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0), ipady=3)
        entry_vsize.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_vae, text="Performance Flags", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='nw', pady=6)
        chk_frame = tk.Frame(f_vae, bg=self.bg_card)
        chk_frame.grid(row=r_sub, column=1, sticky='we', pady=6, padx=(8, 0))
        
        self.chk_vae = tk.Checkbutton(chk_frame, text="VAE Tiling", variable=self.var_vae_tiling, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=styles.FONT_MAIN, command=self.update_cmd_preview)
        self.chk_vae.pack(anchor='w', pady=2)

        self.chk_vae_conv = tk.Checkbutton(chk_frame, text="VAE Conv Direct", variable=self.var_vae_conv_direct, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=styles.FONT_MAIN, command=self.update_cmd_preview)
        self.chk_vae_conv.pack(anchor='w', pady=2)
        
        self.chk_offload = tk.Checkbutton(chk_frame, text="Offload to CPU", variable=self.var_offload, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=styles.FONT_MAIN, command=self.update_cmd_preview)
        self.chk_offload.pack(anchor='w', pady=2)
        
        self.chk_fa = tk.Checkbutton(chk_frame, text="Diffusion FA", variable=self.var_fa, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=styles.FONT_MAIN, command=self.update_cmd_preview)
        self.chk_fa.pack(anchor='w', pady=2)

        self.chk_circular = tk.Checkbutton(chk_frame, text="Circular Padding", variable=self.var_circular, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=styles.FONT_MAIN, command=self.update_cmd_preview)
        self.chk_circular.pack(anchor='w', pady=2)
        
        self.chk_metadata = tk.Checkbutton(chk_frame, text="Disable Metadata", variable=self.var_disable_metadata, bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_main, activebackground=self.bg_card, activeforeground=self.text_primary, font=styles.FONT_MAIN, command=self.update_cmd_preview)
        self.chk_metadata.pack(anchor='w', pady=2)
        r_sub += 1

        # 6. Section: Reference Conditioning (Ref2VA / Multi-Modal)
        c_ref = CollapsibleFrame(scroll_frame, title="Reference Conditioning (Ref2VA)", bg_card=self.bg_card, accent_blue=self.accent_blue, text_primary=self.text_primary, expanded=False, on_toggle=self.update_scrollregion)
        c_ref.grid(row=row, column=0, columnspan=2, sticky='we', pady=(4, 2))
        row += 1

        f_ref = c_ref.content
        f_ref.columnconfigure(1, weight=1)
        r_sub = 0

        tk.Label(f_ref, text="Ref Image (-r / --ref-image)", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        ref_img_frame = tk.Frame(f_ref, bg=self.bg_card)
        ref_img_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        entry_ref_img = styles.create_custom_entry(ref_img_frame, textvariable=self.var_ref_img)
        entry_ref_img.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
        entry_ref_img.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        btn_browse_ref_img = ttk.Button(ref_img_frame, text=">", width=2, command=self.browse_ref_image)
        btn_browse_ref_img.pack(side=tk.LEFT)
        r_sub += 1

        tk.Label(f_ref, text="Ref Video (--ref-video)", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        ref_vid_frame = tk.Frame(f_ref, bg=self.bg_card)
        ref_vid_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        entry_ref_vid = styles.create_custom_entry(ref_vid_frame, textvariable=self.var_ref_video)
        entry_ref_vid.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
        entry_ref_vid.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        btn_browse_ref_vid = ttk.Button(ref_vid_frame, text=">", width=2, command=self.browse_ref_video)
        btn_browse_ref_vid.pack(side=tk.LEFT)
        r_sub += 1

        tk.Label(f_ref, text="Ref Audio (--ref-audio)", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        ref_aud_frame = tk.Frame(f_ref, bg=self.bg_card)
        ref_aud_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        entry_ref_aud = styles.create_custom_entry(ref_aud_frame, textvariable=self.var_ref_audio)
        entry_ref_aud.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
        entry_ref_aud.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        btn_browse_ref_aud = ttk.Button(ref_aud_frame, text=">", width=2, command=self.browse_ref_audio)
        btn_browse_ref_aud.pack(side=tk.LEFT)
        r_sub += 1

        tk.Label(f_ref, text="Ref Video Audio (--ref-video-audio)", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        ref_vaud_frame = tk.Frame(f_ref, bg=self.bg_card)
        ref_vaud_frame.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        entry_ref_vaud = styles.create_custom_entry(ref_vaud_frame, textvariable=self.var_ref_video_audio)
        entry_ref_vaud.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
        entry_ref_vaud.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        btn_browse_ref_vaud = ttk.Button(ref_vaud_frame, text=">", width=2, command=self.browse_ref_video_audio)
        btn_browse_ref_vaud.pack(side=tk.LEFT)
        r_sub += 1

        # 7. Section: Cache Settings
        c_cache = CollapsibleFrame(scroll_frame, title="Cache Settings", bg_card=self.bg_card, accent_blue=self.accent_blue, text_primary=self.text_primary, expanded=False, on_toggle=self.update_scrollregion)
        c_cache.grid(row=row, column=0, columnspan=2, sticky='we', pady=(4, 2))
        row += 1

        f_cache = c_cache.content
        f_cache.columnconfigure(1, weight=1)
        r_sub = 0

        tk.Label(f_cache, text="Cache Mode", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        self.combo_cache = ttk.Combobox(f_cache, textvariable=self.var_cache, values=["none"] + self.cache_mode_options, state="readonly", style='TCombobox')
        self.combo_cache.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0))
        self.combo_cache.bind("<<ComboboxSelected>>", lambda e: self.update_cmd_preview())
        r_sub += 1

        tk.Label(f_cache, text="Cache Options", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        entry_cache_opt = styles.create_custom_entry(f_cache, textvariable=self.var_cache_option)
        entry_cache_opt.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0), ipady=3)
        entry_cache_opt.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        # 7. Section: Advanced & Extra CLI Flags
        c_adv = CollapsibleFrame(scroll_frame, title="Advanced & Extra Flags", bg_card=self.bg_card, accent_blue=self.accent_blue, text_primary=self.text_primary, expanded=False, on_toggle=self.update_scrollregion)
        c_adv.grid(row=row, column=0, columnspan=2, sticky='we', pady=(4, 6))
        row += 1

        f_adv = c_adv.content
        f_adv.columnconfigure(1, weight=1)
        r_sub = 0

        tk.Label(f_adv, text="Extra CLI Flags", bg=self.bg_card, fg=self.text_secondary).grid(row=r_sub, column=0, sticky='w', pady=4)
        entry_extra = styles.create_custom_entry(f_adv, textvariable=self.var_extra_flags)
        entry_extra.grid(row=r_sub, column=1, sticky='we', pady=4, padx=(8, 0), ipady=3)
        entry_extra.bind("<KeyRelease>", lambda e: self.update_cmd_preview())
        r_sub += 1

        
        scroll_frame.columnconfigure(1, weight=1)

        # --- RIGHT PANE: PREVIEW & LOGS ---
        preview_label = tk.Label(right_frame, text="Generated Command", bg=self.bg_card, fg=self.accent_blue, font=styles.FONT_TITLE)
        preview_label.pack(anchor='w', padx=15, pady=(15, 4))
        
        self.text_cmd_preview = tk.Text(right_frame, bg=self.terminal_bg, fg=self.accent_blue, insertbackground=self.accent_blue, insertwidth=2, height=4, font=styles.FONT_CODE, bd=0, highlightthickness=1, highlightbackground=self.border_color, wrap=tk.WORD, padx=8, pady=6)
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
        
        # --- SUB-NOTEBOOK: OUTPUT & TERMINAL LOGS ---
        self.right_notebook = ttk.Notebook(right_frame)
        self.right_notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))

        # Sub-tab 1: Output Preview (Default Tab 0)
        self.sub_tab_preview = tk.Frame(self.right_notebook, bg=self.bg_card)
        self.right_notebook.add(self.sub_tab_preview, text="Output")

        prev_header = tk.Frame(self.sub_tab_preview, bg=self.bg_card)
        prev_header.pack(fill=tk.X, padx=4, pady=(4, 2))

        self.label_latest_title = tk.Label(prev_header, text="Generated Output", bg=self.bg_card, fg=self.text_primary, font=styles.FONT_TITLE)
        self.label_latest_title.pack(side=tk.LEFT)

        btn_open_latest = ttk.Button(prev_header, text="Open File", command=self.open_latest_image_external)
        btn_open_latest.pack(side=tk.RIGHT, padx=(4, 0))

        btn_open_folder = ttk.Button(prev_header, text="Open Folder", command=self.open_latest_folder_external)
        btn_open_folder.pack(side=tk.RIGHT)

        # Output Location Link Bar
        loc_frame = tk.Frame(self.sub_tab_preview, bg=self.bg_card)
        loc_frame.pack(fill=tk.X, padx=4, pady=(0, 4))
        
        tk.Label(loc_frame, text="Location: ", bg=self.bg_card, fg=self.text_secondary, font=styles.FONT_SMALL).pack(side=tk.LEFT)
        self.label_latest_path = tk.Label(
            loc_frame,
            text="No output file generated in this session yet.",
            bg=self.bg_card,
            fg=self.text_secondary,
            font=styles.FONT_SMALL,
            anchor="w"
        )
        self.label_latest_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

        preview_card = tk.Frame(self.sub_tab_preview, bg=self.bg_input, bd=1, relief=tk.SOLID, highlightbackground=self.border_color)
        preview_card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.label_latest_preview = tk.Label(
            preview_card,
            text="No images generated in this session yet.\n\nRun a generation to view the output image here.",
            bg=self.bg_input,
            fg=self.text_secondary,
            font=styles.FONT_MAIN,
            cursor="hand2"
        )
        self.label_latest_preview.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.label_latest_preview.bind("<Button-1>", lambda e: self.open_latest_image_external())

        # Sub-tab 2: Terminal Logs (Tab 1)
        self.sub_tab_logs = tk.Frame(self.right_notebook, bg=self.bg_card)
        self.right_notebook.add(self.sub_tab_logs, text="Terminal Logs")

        console_header = tk.Frame(self.sub_tab_logs, bg=self.bg_card)
        console_header.pack(fill=tk.X, padx=5, pady=(5, 5))

        tk.Label(console_header, text="Execution Terminal Logs", bg=self.bg_card, fg=self.text_primary, font=styles.FONT_TITLE).pack(side=tk.LEFT)

        btn_copy = ttk.Button(console_header, text="Copy Logs", command=self.app.copy_logs)
        btn_copy.pack(side=tk.RIGHT, padx=(5, 0))

        btn_clear = ttk.Button(console_header, text="Clear Logs", command=self.app.clear_logs)
        btn_clear.pack(side=tk.RIGHT)

        self.text_terminal = tk.Text(
            self.sub_tab_logs,
            bg=self.terminal_bg,
            fg=self.terminal_fg,
            insertbackground=self.terminal_fg,
            insertwidth=2,
            font=styles.FONT_CODE,
            wrap=tk.WORD,
            bd=0,
            highlightthickness=1,
            highlightbackground=self.border_color,
            padx=10,
            pady=10
        )
        self.text_terminal.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # Sub-tab 3: Output Gallery (Tab 2)
        self.tab_gallery_frame = tk.Frame(self.right_notebook, bg=self.bg_card)
        self.right_notebook.add(self.tab_gallery_frame, text="Output Gallery")
        self.gallery_tab = GalleryTab(self.tab_gallery_frame, self.app)

        # Sub-tab 4: Prompt Helper (Tab 3)
        self.tab_prompt_helper_frame = tk.Frame(self.right_notebook, bg=self.bg_card)
        self.right_notebook.add(self.tab_prompt_helper_frame, text="Prompt Helper")
        self.prompt_helper_tab = PromptHelperTab(self.tab_prompt_helper_frame, self.app)

        # Sub-tab 5: Execution History (Tab 4)
        self.tab_history_frame = tk.Frame(self.right_notebook, bg=self.bg_card)
        self.right_notebook.add(self.tab_history_frame, text="Execution History")
        self.history_tab = HistoryTab(self.tab_history_frame, self.app)

        # Apply initial random seed toggle state
        self.on_random_seed_toggle()

        # Show the megapixel readout for the starting width/height
        self.update_megapixel_readout()

        # Select Output (Tab 0) as default
        self.right_notebook.select(0)

        styles.setup_text_shortcuts(self.entry_prompt)
        styles.setup_text_shortcuts(self.entry_neg_prompt)
        styles.setup_text_shortcuts(self.text_cmd_preview)
        styles.setup_text_shortcuts(self.text_terminal)
        
        self.update_cmd_preview()

    def update_latest_output_preview(self, file_path=None):
        if not file_path:
            return

        if not os.path.exists(file_path):
            output_dir = self.app.OUTPUT_DIR
            if not os.path.exists(output_dir):
                return
            extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.mp4']
            files = []
            for ext in extensions:
                files.extend(glob.glob(os.path.join(output_dir, ext)))
            if not files:
                return
            files.sort(key=os.path.getmtime, reverse=True)
            file_path = files[0]

        abs_path = os.path.abspath(file_path)
        filename = os.path.basename(file_path)
        self.latest_image_path = abs_path
        
        self.label_latest_title.config(text=f"Output: {filename}")
        self.label_latest_path.config(text=abs_path, fg=self.accent_blue, cursor="hand2")
        self.label_latest_path.bind("<Button-1>", lambda e: self.open_latest_image_external())

        try:
            if file_path.lower().endswith('.mp4'):
                self.label_latest_preview.config(image="", text=f"VIDEO OUTPUT:\n{filename}\n\nPath: {abs_path}\n(Click to open media file)")
            else:
                img = Image.open(file_path)
                card_w = self.sub_tab_preview.winfo_width()
                card_h = self.sub_tab_preview.winfo_height()
                max_w = max(400, card_w - 20) if card_w > 50 else 700
                max_h = max(300, card_h - 80) if card_h > 50 else 500
                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.latest_photo = photo
                self.label_latest_preview.config(image=photo, text="")
        except Exception as e:
            self.label_latest_title.config(text=f"Error loading image: {e}")

    def open_latest_image_external(self):
        if not self.latest_image_path or not os.path.exists(self.latest_image_path):
            return
        path = self.latest_image_path
        try:
            if sys.platform.startswith('darwin'):
                subprocess.Popen(['open', path])
            elif os.name == 'nt':
                os.startfile(path)
            else:
                subprocess.Popen(['xdg-open', path])
        except Exception as e:
            pass

    def open_latest_folder_external(self):
        output_dir = self.app.OUTPUT_DIR
        if self.latest_image_path and os.path.exists(self.latest_image_path):
            output_dir = os.path.dirname(self.latest_image_path)
        os.makedirs(output_dir, exist_ok=True)
        try:
            if sys.platform.startswith('darwin'):
                subprocess.Popen(['open', output_dir])
            elif os.name == 'nt':
                os.startfile(output_dir)
            else:
                subprocess.Popen(['xdg-open', output_dir])
        except Exception as e:
            pass

    def on_canvas_configure(self, event):
        if hasattr(self, 'canvas_window'):
            self.form_canvas.itemconfig(self.canvas_window, width=event.width)
        self.update_scrollregion()

    def update_scrollregion(self):
        self.parent.update_idletasks()
        self.form_canvas.configure(scrollregion=self.form_canvas.bbox("all"))

    def browse_model(self):
        filename = filedialog.askopenfilename(
            title="Select Diffusion Model",
            filetypes=[("Model Files", "*.safetensors *.gguf *.ckpt"), ("All Files", "*.*")]
        )
        if filename:
            if filename.startswith(self.app.WORKSPACE_DIR):
                filename = os.path.relpath(filename, self.app.WORKSPACE_DIR)
            self.var_model.set(filename)
            self.update_cmd_preview()

    def browse_t5xxl(self):
        filename = filedialog.askopenfilename(
            title="Select T5XXL Text Encoder",
            filetypes=[("Model Files", "*.safetensors *.gguf *.ckpt"), ("All Files", "*.*")]
        )
        if filename:
            if filename.startswith(self.app.WORKSPACE_DIR):
                filename = os.path.relpath(filename, self.app.WORKSPACE_DIR)
            self.var_t5xxl.set(filename)
            self.update_cmd_preview()

    def browse_llm(self):
        filename = filedialog.askopenfilename(
            title="Select LLM Text Encoder",
            filetypes=[("Model Files", "*.safetensors *.gguf *.ckpt"), ("All Files", "*.*")]
        )
        if filename:
            if filename.startswith(self.app.WORKSPACE_DIR):
                filename = os.path.relpath(filename, self.app.WORKSPACE_DIR)
            self.var_llm.set(filename)
            self.update_cmd_preview()

    def browse_vae(self):
        filename = filedialog.askopenfilename(
            title="Select VAE Decoder",
            filetypes=[("Model Files", "*.safetensors *.gguf *.ckpt"), ("All Files", "*.*")]
        )
        if filename:
            if filename.startswith(self.app.WORKSPACE_DIR):
                filename = os.path.relpath(filename, self.app.WORKSPACE_DIR)
            self.var_vae.set(filename)
            self.update_cmd_preview()

    def browse_init_image(self):

        filename = filedialog.askopenfilename(
            title="Select Input Image for img2img",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All Files", "*.*")]
        )
        if filename:
            self.var_init_img.set(filename)
            if self.var_mode.get() in ["", "txt2img", "img_gen"]:
                self.var_mode.set("img_gen")
            self.update_cmd_preview()

    def browse_lora_dir(self):
        directory = filedialog.askdirectory(
            title="Select LoRA Model Directory"
        )
        if directory:
            self.var_lora_dir.set(directory)
            self.update_cmd_preview()

    def browse_llm_vision(self):
        filename = filedialog.askopenfilename(
            title="Select LLM Vision Tower",
            filetypes=[("Model Files", "*.safetensors *.gguf *.ckpt"), ("All Files", "*.*")]
        )
        if filename:
            if filename.startswith(self.app.WORKSPACE_DIR):
                filename = os.path.relpath(filename, self.app.WORKSPACE_DIR)
            self.var_llm_vision.set(filename)
            self.update_cmd_preview()

    def browse_audio_vae(self):
        filename = filedialog.askopenfilename(
            title="Select Audio VAE Decoder",
            filetypes=[("Model Files", "*.safetensors *.gguf *.ckpt"), ("All Files", "*.*")]
        )
        if filename:
            if filename.startswith(self.app.WORKSPACE_DIR):
                filename = os.path.relpath(filename, self.app.WORKSPACE_DIR)
            self.var_audio_vae.set(filename)
            self.update_cmd_preview()

    def browse_end_image(self):
        filename = filedialog.askopenfilename(
            title="Select End Frame Image for FL2VA",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All Files", "*.*")]
        )
        if filename:
            self.var_end_img.set(filename)
            self.update_cmd_preview()

    def browse_ref_image(self):
        filename = filedialog.askopenfilename(
            title="Select Reference Image (-r / --ref-image)",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All Files", "*.*")]
        )
        if filename:
            current = self.var_ref_img.get().strip()
            if current:
                self.var_ref_img.set(f"{current}, {filename}")
            else:
                self.var_ref_img.set(filename)
            self.update_cmd_preview()

    def browse_ref_video(self):
        directory = filedialog.askdirectory(
            title="Select Reference Video Directory (--ref-video)"
        )
        if directory:
            current = self.var_ref_video.get().strip()
            if current:
                self.var_ref_video.set(f"{current}, {directory}")
            else:
                self.var_ref_video.set(directory)
            self.update_cmd_preview()

    def browse_ref_audio(self):
        filename = filedialog.askopenfilename(
            title="Select Reference Audio File (--ref-audio)",
            filetypes=[("Audio Files", "*.wav *.mp3 *.flac *.ogg"), ("All Files", "*.*")]
        )
        if filename:
            current = self.var_ref_audio.get().strip()
            if current:
                self.var_ref_audio.set(f"{current}, {filename}")
            else:
                self.var_ref_audio.set(filename)
            self.update_cmd_preview()

    def browse_ref_video_audio(self):
        filename = filedialog.askopenfilename(
            title="Select Reference Video Audio File (--ref-video-audio)",
            filetypes=[("Audio Files", "*.wav *.mp3 *.flac *.ogg"), ("All Files", "*.*")]
        )
        if filename:
            current = self.var_ref_video_audio.get().strip()
            if current:
                self.var_ref_video_audio.set(f"{current}, {filename}")
            else:
                self.var_ref_video_audio.set(filename)
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
            
        cmd_string = shlex.join(preview_cmd)
        self.text_cmd_preview.delete("1.0", tk.END)
        self.text_cmd_preview.insert("1.0", cmd_string)

    def _scroll_text_widget(self, event):
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            event.widget.yview_scroll(-1, "units")
        else:
            event.widget.yview_scroll(1, "units")
        return "break"

    def on_random_seed_toggle(self):
        # The seed field always shows a concrete value. "Random" only controls
        # whether that value is re-rolled before each run; unchecking it locks
        # the current seed so a result can be reproduced exactly.
        if self.app.var_random_seed.get():
            self.app.roll_seed()
        else:
            self.update_cmd_preview()

    def step_megapixels(self, delta):
        """Nudges the megapixel budget by one step, clamped to the valid range.

        Tolerant of a blank or non-numeric field by restarting from MP_MIN, so
        the buttons always move somewhere sensible.
        """
        try:
            current = float(self.var_megapixels.get().strip())
        except (TypeError, ValueError):
            current = MP_MIN
        stepped = round(current + delta, 2)
        stepped = max(MP_MIN, min(MP_MAX, stepped))
        self.var_megapixels.set(f"{stepped:.1f}")
        self.on_resolution_change()

    def on_size_change(self, event=None):
        """Manual width/height edits refresh the megapixel readout."""
        self.update_megapixel_readout()
        self.update_cmd_preview()

    def on_resolution_change(self, event=None):
        """Recomputes width/height from the aspect ratio and megapixel budget.

        The "Custom" aspect ratio is a no-op so manually typed sizes are never
        silently overwritten.
        """
        label = self.var_aspect_ratio.get()
        if label == resolution.CUSTOM or not label:
            self.update_megapixel_readout()
            self.update_cmd_preview()
            return

        try:
            multiple = int(float(self.var_res_multiple.get().strip() or 8))
        except (TypeError, ValueError):
            multiple = 8
        if multiple < 1:
            multiple = 1

        try:
            width, height = resolution.resolution_from_megapixels(
                label, self.var_megapixels.get().strip() or 1.0, multiple
            )
        except ValueError:
            return

        self.var_width.set(str(width))
        self.var_height.set(str(height))
        # Readout last, so it reflects the dimensions just written above.
        self.update_megapixel_readout()
        self.update_cmd_preview()

    def update_megapixel_readout(self):
        """Shows the megapixels actually produced by the current width/height."""
        if not hasattr(self, "label_mp_readout"):
            return
        mp = resolution.megapixels_of(self.var_width.get(), self.var_height.get())
        if mp <= 0:
            self.label_mp_readout.config(text="")
        else:
            self.label_mp_readout.config(text=f"= {mp:.2f} MP")

    def on_prompt_change(self, event=None):
        self.update_cmd_preview()

    def on_neg_prompt_change(self, event=None):
        self.update_cmd_preview()

    def on_video_seconds_change(self, event=None):
        try:
            sec_str = self.var_video_seconds.get().strip()
            fps_str = self.var_fps.get().strip()
            fps = float(fps_str) if fps_str else 24.0
            if sec_str:
                sec = float(sec_str)
                frames = max(1, int(round(sec * fps)))
                if self.var_video_frames.get().strip() != str(frames):
                    self.var_video_frames.set(str(frames))
            else:
                self.var_video_frames.set("")
        except ValueError:
            pass
        self.update_cmd_preview()

    def on_video_frames_change(self, event=None):
        try:
            frames_str = self.var_video_frames.get().strip()
            fps_str = self.var_fps.get().strip()
            fps = float(fps_str) if fps_str else 24.0
            if frames_str:
                frames = int(frames_str)
                sec = round(frames / fps, 2)
                if self.var_video_seconds.get().strip() != str(sec):
                    self.var_video_seconds.set(str(sec))
            else:
                self.var_video_seconds.set("")
        except ValueError:
            pass
        self.update_cmd_preview()

    def on_fps_change(self, event=None):
        if self.var_video_seconds.get().strip():
            self.on_video_seconds_change()
        elif self.var_video_frames.get().strip():
            self.on_video_frames_change()
        self.update_cmd_preview()
