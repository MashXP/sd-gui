import os
import sys
import re
import time
import subprocess
import queue
import tkinter as tk
from tkinter import ttk, messagebox

import styles
import profile_manager
from runner import ProcessRunner
from history_db import HistoryDB

from ui.tab_generator import GeneratorTab
from ui.tab_gallery import GalleryTab
from ui.tab_prompt_helper import PromptHelperTab
from ui.tab_history import HistoryTab

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR = os.path.join(WORKSPACE_DIR, "profiles")
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "output")
DB_PATH = os.path.join(WORKSPACE_DIR, "data.db")

# Path to the build binaries
CLI_PATH = os.path.expanduser("~/App/stable-diffusion.cpp/build/bin/sd-cli")
SERVER_PATH = os.path.expanduser("~/App/stable-diffusion.cpp/build/bin/sd-server")

class DesktopManager:
    """Master application coordinator for SD-GUI Desktop."""
    def __init__(self, root):
        self.root = root
        self.root.title("SD-CLI Desktop Manager")
        self.root.geometry("1280x820")
        self.root.configure(bg=styles.BG_MAIN)
        self.root.resizable(True, True)
        
        try:
            self.root.attributes('-type', 'normal')
        except Exception:
            pass

        # Configure local directories
        os.makedirs(PROFILES_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(os.path.join(WORKSPACE_DIR, "models"), exist_ok=True)
        
        self.WORKSPACE_DIR = WORKSPACE_DIR
        self.PROFILES_DIR = PROFILES_DIR
        self.OUTPUT_DIR = OUTPUT_DIR
        
        # Initialize Database and Process Runner
        self.db = HistoryDB(DB_PATH)
        self.log_queue = queue.Queue()
        self.runner = ProcessRunner(self.log_queue)
        
        # Styling Setup
        self.bg_main = styles.BG_MAIN
        self.bg_card = styles.BG_CARD
        self.bg_input = styles.BG_INPUT
        self.border_color = styles.BORDER_COLOR
        self.accent_blue = styles.ACCENT_BLUE
        self.text_primary = styles.TEXT_PRIMARY
        self.text_secondary = styles.TEXT_SECONDARY
        
        style = ttk.Style()
        styles.apply_styles(self.root, style)
        
        self.start_time = None
        self.timer_running = False
        
        # History recording toggle
        self.var_record_history = tk.BooleanVar(value=True)

        # Form field variables
        self.var_binary = tk.StringVar(value="sd-cli")
        self.var_mode = tk.StringVar(value="img_gen")
        self.var_backend = tk.StringVar(value="llm=cpu")
        self.var_model = tk.StringVar()
        self.var_t5xxl = tk.StringVar()
        self.var_llm = tk.StringVar()
        self.var_vae = tk.StringVar()
        self.var_width = tk.StringVar(value="768")
        self.var_height = tk.StringVar(value="768")
        self.var_steps = tk.StringVar(value="20")
        self.var_cfg = tk.StringVar(value="6.0")
        self.var_guidance = tk.StringVar(value="")
        self.var_seed = tk.StringVar(value="-1")
        self.var_random_seed = tk.BooleanVar(value=True)
        self.var_batch_count = tk.StringVar(value="1")
        self.var_output_begin_idx = tk.StringVar(value="")
        self.var_max_vram = tk.StringVar(value="-0.1")
        self.var_sampler = tk.StringVar(value="euler")
        self.var_scheduler = tk.StringVar(value="discrete")
        self.var_flow_shift = tk.StringVar(value="")
        self.var_video_frames = tk.StringVar(value="")
        self.var_cache = tk.StringVar(value="none")
        self.var_cache_option = tk.StringVar(value="")
        self.var_output = tk.StringVar(value="output_%03d.png")
        self.var_extra_flags = tk.StringVar(value="")
        
        # Server specific variables
        self.var_listen_ip = tk.StringVar(value="0.0.0.0")
        self.var_listen_port = tk.StringVar(value="1234")
        
        # Highres fix & Img2Img variables
        self.var_init_img = tk.StringVar(value="")
        self.var_strength = tk.StringVar(value="")
        self.var_hires = tk.BooleanVar(value=False)
        self.var_hires_scale = tk.StringVar(value="")
        self.var_hires_denoise = tk.StringVar(value="")
        self.var_hires_steps = tk.StringVar(value="")
        
        # Advanced SLG & Tiling & LoRA variables
        self.var_slg_scale = tk.StringVar(value="")
        self.var_skip_layers = tk.StringVar(value="")
        self.var_vae_tile_size = tk.StringVar(value="")
        self.var_lora_dir = tk.StringVar(value="")
        self.var_lora_apply_mode = tk.StringVar(value="")
        
        # Boolean advanced flags
        self.var_vae_tiling = tk.BooleanVar(value=True)
        self.var_vae_conv_direct = tk.BooleanVar(value=False)
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
        
        for combo in [self.generator_tab.combo_model, self.generator_tab.combo_t5xxl, self.generator_tab.combo_llm, self.generator_tab.combo_vae]:
            combo['values'] = [""] + self.scanned_models

    def load_profiles_list(self):
        self.profile_list = [f[:-4] for f in os.listdir(PROFILES_DIR) if f.endswith(".env")]
        self.profile_list.sort()
        self.generator_tab.combo_profile['values'] = self.profile_list

    def build_ui(self):
        # Main Application Container
        self.main_container = tk.Frame(self.root, bg=self.bg_main)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.generator_tab = GeneratorTab(self.main_container, self)
        
        # Expose sub-tabs and right notebook for application-level access
        self.gallery_tab = self.generator_tab.gallery_tab
        self.prompt_helper_tab = self.generator_tab.prompt_helper_tab
        self.history_tab = self.generator_tab.history_tab
        self.notebook = self.generator_tab.right_notebook

    def build_command_list(self, generator_tab=None):
        if generator_tab is None:
            generator_tab = getattr(self, 'generator_tab', None)
        if generator_tab is None:
            return []

        binary = self.var_binary.get()
        binary_path = SERVER_PATH if binary == "sd-server" else CLI_PATH
        
        cmd = [binary_path]
        
        mode = self.var_mode.get().strip()
        if mode and binary == "sd-cli":
            cmd += ["-M", mode]
            
        model = self.var_model.get().strip()
        vae = self.var_vae.get().strip()
        t5xxl = self.var_t5xxl.get().strip()
        llm = self.var_llm.get().strip()
        
        if model:
            if not vae and not llm and not t5xxl:
                cmd += ["-m", model]
            else:
                cmd += ["--diffusion-model", model]
                
        if vae:
            cmd += ["--vae", vae]
        if t5xxl:
            cmd += ["--t5xxl", t5xxl]
        if llm:
            cmd += ["--llm", llm]
            
        backend = self.var_backend.get()
        if backend:
            cmd += ["--backend", backend]
            
        prompt = generator_tab.entry_prompt.get("1.0", "end-1c").strip()
        if prompt:
            cmd += ["-p", prompt]
            
        if binary == "sd-cli":
            neg_prompt = generator_tab.entry_neg_prompt.get("1.0", "end-1c").strip()
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
            
        flow_shift = self.var_flow_shift.get().strip()
        if flow_shift:
            cmd += ["--flow-shift", flow_shift]

        video_frames = self.var_video_frames.get().strip()
        if video_frames:
            cmd += ["--video-frames", video_frames]
            
        init_img = self.var_init_img.get().strip()
        if init_img:
            cmd += ["-i", init_img]

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
            
        lora_dir = self.var_lora_dir.get().strip()
        if lora_dir:
            cmd += ["--lora-model-dir", lora_dir]
            
        lora_mode = self.var_lora_apply_mode.get().strip()
        if lora_mode:
            cmd += ["--lora-apply-mode", lora_mode]
            
        if self.var_vae_tiling.get():
            cmd += ["--vae-tiling"]
        if self.var_vae_conv_direct.get():
            cmd += ["--vae-conv-direct"]
        if self.var_offload.get():
            cmd += ["--offload-to-cpu"]
        if self.var_fa.get():
            cmd += ["--diffusion-fa"]
        if self.var_circular.get():
            cmd += ["--circular"]
        if self.var_disable_metadata.get():
            cmd += ["--disable-image-metadata"]
            
        extra = self.var_extra_flags.get().strip()
        if extra:
            cmd += extra.split()
            
        if binary == "sd-cli":
            out_val = self.var_output.get().strip()
            if out_val:
                if not out_val.startswith("output/"):
                    out_val = f"output/{out_val}"
                cmd += ["-o", out_val]
        else:
            ip = self.var_listen_ip.get().strip()
            if ip:
                cmd += ["--listen-ip", ip]
            port = self.var_listen_port.get().strip()
            if port:
                cmd += ["--listen-port", port]
                
        return cmd

    def copy_command(self):
        cmd = self.build_command_list()
        self.copy_to_clipboard(" ".join(cmd))
        self.show_toast("Command copied to clipboard!")

    def on_profile_selected(self, event):
        name = self.generator_tab.combo_profile.get()
        if not name:
            return
            
        profile_path = os.path.join(PROFILES_DIR, f"{name}.env")
        config = profile_manager.parse_env_file(profile_path)
        
        if "BINARY" in config: self.var_binary.set(config["BINARY"])
        if "MODE" in config: self.var_mode.set(config["MODE"])
        if "MODEL" in config: self.var_model.set(config["MODEL"])
        if "VAE" in config: self.var_vae.set(config["VAE"])
        if "T5XXL" in config: self.var_t5xxl.set(config["T5XXL"])
        if "LLM" in config: self.var_llm.set(config["LLM"])
        if "BACKEND" in config: self.var_backend.set(config["BACKEND"])
        
        self.generator_tab.entry_prompt.delete("1.0", tk.END)
        if "PROMPT" in config: self.generator_tab.entry_prompt.insert("1.0", config["PROMPT"])
        
        self.generator_tab.entry_neg_prompt.delete("1.0", tk.END)
        if "NEGATIVE_PROMPT" in config: self.generator_tab.entry_neg_prompt.insert("1.0", config["NEGATIVE_PROMPT"])
        
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
        if "FLOW_SHIFT" in config: self.var_flow_shift.set(config["FLOW_SHIFT"])
        if "VIDEO_FRAMES" in config: self.var_video_frames.set(config["VIDEO_FRAMES"])
        if "CACHE_MODE" in config: self.var_cache.set(config["CACHE_MODE"])
        if "CACHE_OPTION" in config: self.var_cache_option.set(config["CACHE_OPTION"])
        if "EXTRA_FLAGS" in config: self.var_extra_flags.set(config["EXTRA_FLAGS"])
        
        if "INIT_IMG" in config: self.var_init_img.set(config["INIT_IMG"])
        if "STRENGTH" in config: self.var_strength.set(config["STRENGTH"])
        if "HIRES" in config: self.var_hires.set(config["HIRES"].lower() == "true")
        if "HIRES_SCALE" in config: self.var_hires_scale.set(config["HIRES_SCALE"])
        if "HIRES_DENOISING_STRENGTH" in config: self.var_hires_denoise.set(config["HIRES_DENOISING_STRENGTH"])
        if "HIRES_STEPS" in config: self.var_hires_steps.set(config["HIRES_STEPS"])
        
        if "SLG_SCALE" in config: self.var_slg_scale.set(config["SLG_SCALE"])
        if "SKIP_LAYERS" in config: self.var_skip_layers.set(config["SKIP_LAYERS"])
        if "VAE_TILE_SIZE" in config: self.var_vae_tile_size.set(config["VAE_TILE_SIZE"])
        if "LORA_MODEL_DIR" in config: self.var_lora_dir.set(config["LORA_MODEL_DIR"])
        if "LORA_APPLY_MODE" in config: self.var_lora_apply_mode.set(config["LORA_APPLY_MODE"])
        
        if "CIRCULAR" in config: self.var_circular.set(config["CIRCULAR"].lower() == "true")
        if "DISABLE_IMAGE_METADATA" in config: self.var_disable_metadata.set(config["DISABLE_IMAGE_METADATA"].lower() == "true")
        
        if "OUTPUT" in config: 
            out = config["OUTPUT"]
            if out.startswith("output/"):
                out = out[7:]
            self.var_output.set(out)
        
        if "VAE_TILING" in config: self.var_vae_tiling.set(config["VAE_TILING"].lower() == "true")
        if "VAE_CONV_DIRECT" in config: self.var_vae_conv_direct.set(config["VAE_CONV_DIRECT"].lower() == "true")
        if "OFFLOAD_TO_CPU" in config: self.var_offload.set(config["OFFLOAD_TO_CPU"].lower() == "true")
        if "DIFFUSION_FA" in config: self.var_fa.set(config["DIFFUSION_FA"].lower() == "true")
        
        if "LISTEN_IP" in config: self.var_listen_ip.set(config["LISTEN_IP"])
        if "LISTEN_PORT" in config: self.var_listen_port.set(config["LISTEN_PORT"])
        
        self.generator_tab.entry_save_name.delete(0, tk.END)
        self.generator_tab.entry_save_name.insert(0, name)
        
        self.generator_tab.update_layout_for_binary_mode()

    def save_profile(self):
        name = self.generator_tab.entry_save_name.get().strip()
        if not name:
            messagebox.showwarning("Name Required", "Please enter a profile name first.")
            return
            
        out_val = self.var_output.get().strip()
        if out_val and not out_val.startswith("output/"):
            out_val = f"output/{out_val}"

        config = {
            "BINARY": self.var_binary.get(),
            "MODE": self.var_mode.get().strip(),
            "MODEL": self.var_model.get(),
            "VAE": self.var_vae.get(),
            "T5XXL": self.var_t5xxl.get(),
            "LLM": self.var_llm.get(),
            "BACKEND": self.var_backend.get(),
            "PROMPT": self.generator_tab.entry_prompt.get("1.0", "end-1c").strip(),
            "NEGATIVE_PROMPT": self.generator_tab.entry_neg_prompt.get("1.0", "end-1c").strip(),
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
            "FLOW_SHIFT": self.var_flow_shift.get().strip(),
            "VIDEO_FRAMES": self.var_video_frames.get().strip(),
            "CACHE_MODE": self.var_cache.get(),
            "CACHE_OPTION": self.var_cache_option.get().strip(),
            "INIT_IMG": self.var_init_img.get().strip(),
            "STRENGTH": self.var_strength.get().strip(),
            "HIRES": str(self.var_hires.get()).lower(),
            "HIRES_SCALE": self.var_hires_scale.get().strip(),
            "HIRES_DENOISING_STRENGTH": self.var_hires_denoise.get().strip(),
            "HIRES_STEPS": self.var_hires_steps.get().strip(),
            "SLG_SCALE": self.var_slg_scale.get().strip(),
            "SKIP_LAYERS": self.var_skip_layers.get().strip(),
            "VAE_TILE_SIZE": self.var_vae_tile_size.get().strip(),
            "LORA_MODEL_DIR": self.var_lora_dir.get().strip(),
            "LORA_APPLY_MODE": self.var_lora_apply_mode.get().strip(),
            "CIRCULAR": str(self.var_circular.get()).lower(),
            "DISABLE_IMAGE_METADATA": str(self.var_disable_metadata.get()).lower(),
            "OUTPUT": out_val,
            "VAE_TILING": str(self.var_vae_tiling.get()).lower(),
            "VAE_CONV_DIRECT": str(self.var_vae_conv_direct.get()).lower(),
            "OFFLOAD_TO_CPU": str(self.var_offload.get()).lower(),
            "DIFFUSION_FA": str(self.var_fa.get()).lower(),
            "LISTEN_IP": self.var_listen_ip.get().strip(),
            "LISTEN_PORT": self.var_listen_port.get().strip(),
        }
        
        profile_path = os.path.join(PROFILES_DIR, f"{name}.env")
        profile_manager.write_env_file(profile_path, config)
        
        self.load_profiles_list()
        self.generator_tab.combo_profile.set(name)
        self.show_toast(f"Profile '{name}' saved!")

    def clear_logs(self):
        self.generator_tab.text_terminal.delete("1.0", tk.END)

    def copy_logs(self):
        logs = self.generator_tab.text_terminal.get("1.0", tk.END)
        max_len = 50000
        if len(logs) > max_len:
            logs = f"[Logs truncated - showing last {max_len} characters]\n" + logs[-max_len:]
        self.copy_to_clipboard(logs.strip())
        if len(logs) > max_len:
            self.show_toast("Logs copied (trimmed)!")
        else:
            self.show_toast("Console logs copied!")

    def show_toast(self, message, duration=1500):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.configure(bg=self.bg_input)

        lbl = tk.Label(toast, text=message, bg=self.bg_input, fg=self.accent_blue, font=styles.FONT_TITLE, padx=15, pady=8)
        lbl.pack()

        self.root.update()
        toast.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        tw = toast.winfo_reqwidth()
        th = toast.winfo_reqheight()

        x = rx + (rw // 2) - (tw // 2)
        y = ry + rh - th - 40
        toast.geometry(f"+{x}+{y}")

        self.root.after(duration, toast.destroy)

    def copy_to_clipboard(self, text):
        if not text:
            return
        try:
            # Use wl-copy/xclip for actual Wayland/X11 clipboard integration.
            # start_new_session=True isolates wl-copy in its own process group so
            # it doesn't receive or send SIGTERM to/from Antigravity's ptyHost.
            if os.environ.get("WAYLAND_DISPLAY"):
                proc = subprocess.Popen(
                    ['wl-copy'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    start_new_session=True
                )
                proc.stdin.write(text)
                proc.stdin.close()
            elif os.environ.get("DISPLAY"):
                proc = subprocess.Popen(
                    ['xclip', '-selection', 'clipboard'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    start_new_session=True
                )
                proc.stdin.write(text)
                proc.stdin.close()
        except Exception:
            # Fallback to Tkinter clipboard (X11 only, but better than nothing)
            try:
                self.root.clipboard_append(text)
                self.root.update_idletasks()
            except Exception:
                pass

    def start_process(self):
        if self.runner.is_running:
            return
            
        cmd = self.build_command_list()
        binary_path = cmd[0]
        
        if not os.path.exists(binary_path):
            messagebox.showerror("Error", f"Binary not found at:\n{binary_path}\nPlease build stable-diffusion.cpp first.")
            return
            
        self.clear_logs()
        self.generator_tab.text_terminal.insert(tk.END, f"Launching subprocess: {' '.join(cmd)}\n\n")
        
        self.generator_tab.btn_start.configure(state=tk.DISABLED, bg="#1f2937", fg=self.text_secondary)
        self.generator_tab.btn_stop.configure(state=tk.NORMAL, bg=styles.BTN_RED, fg="#ffffff", cursor="hand2")
        
        self.start_time = time.time()
        self.timer_running = True
        self.generator_tab.label_timer.configure(text="0.0s", fg=self.accent_blue)
        self.root.after(100, self.update_timer)
        
        self.runner.start(cmd, WORKSPACE_DIR)

    def stop_process(self):
        self.runner.stop()

    def _extract_seed_from_terminal(self):
        text = self.generator_tab.text_terminal.get("1.0", "end-1c")
        for pat in (r'seed[:\s]*(\d+)', r'using seed[:\s]*(\d+)', r'seed\s*=\s*(\d+)'):
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return self.var_seed.get().strip() or "-1"

    def poll_log_queue(self):
        try:
            while True:
                line = self.log_queue.get_nowait()
                if line == "__PROCESS_DONE__":
                    self.generator_tab.btn_start.configure(state=tk.NORMAL, bg=styles.BTN_GREEN, fg="#ffffff")
                    self.generator_tab.btn_stop.configure(state=tk.DISABLED, bg="#374151", fg=self.text_secondary, cursor="")
                    
                    self.timer_running = False
                    if self.start_time:
                        elapsed = time.time() - self.start_time
                        self.generator_tab.label_timer.configure(text=f"Finished in {elapsed:.1f}s", fg=styles.BTN_GREEN)
                        
                        prompt = self.generator_tab.entry_prompt.get("1.0", "end-1c").strip()
                        neg_p = self.generator_tab.entry_neg_prompt.get("1.0", "end-1c").strip()
                        cmd_str = " ".join(self.build_command_list())
                        out_file = self.var_output.get().strip()
                        if not out_file.startswith("output/"):
                            out_file = f"output/{out_file}"
                        
                        actual_seed = self._extract_seed_from_terminal()
                        
                        mode = self.var_mode.get().strip() or None
                        steps = self.var_steps.get().strip()
                        steps = int(steps) if steps.isdigit() else None
                        cfg = self.var_cfg.get().strip()
                        cfg = float(cfg) if cfg else None
                        sampler = self.var_sampler.get().strip() or None
                        
                        if self.var_record_history.get():
                            try:
                                self.db.add_entry(
                                    model=self.var_model.get().strip(),
                                    prompt=prompt,
                                    negative_prompt=neg_p,
                                    width=int(self.var_width.get()),
                                    height=int(self.var_height.get()),
                                    seed=actual_seed,
                                    output_path=out_file,
                                    full_cmd=cmd_str,
                                    generation_time=round(elapsed, 2),
                                    mode=mode,
                                    steps=steps,
                                    cfg_scale=cfg,
                                    sampler=sampler,
                                )
                                self.history_tab.refresh_history_table()
                            except Exception as e:
                                print(f"Error logging run to database: {e}", file=sys.stderr)

                        self.gallery_tab.refresh_gallery()
                        self.generator_tab.update_latest_output_preview(out_file)
                        try:
                            self.generator_tab.right_notebook.select(0)
                        except Exception:
                            pass
                else:
                    self.generator_tab.text_terminal.insert(tk.END, line)
                    try:
                        num_lines = int(self.generator_tab.text_terminal.index("end-1c").split(".")[0])
                        if num_lines > 500:
                            self.generator_tab.text_terminal.delete("1.0", f"{num_lines - 400}.0")
                    except Exception:
                        pass
                    self.generator_tab.text_terminal.see(tk.END)
        except queue.Empty:
            pass
        self.root.after(100, self.poll_log_queue)

    def update_timer(self):
        if self.runner.is_running and self.timer_running and self.start_time:
            elapsed = time.time() - self.start_time
            self.generator_tab.label_timer.configure(text=f"{elapsed:.1f}s")
            self.root.after(100, self.update_timer)

    def on_close(self):
        if self.runner.is_running:
            if messagebox.askokcancel("Quit", "A model generation process is currently running. Do you want to terminate it and quit?"):
                self.runner.kill_force()
                self.root.destroy()
        else:
            self.root.destroy()
