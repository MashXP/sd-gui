# SD-GUI: Tkinter Desktop Manager for stable-diffusion.cpp

A standalone Tkinter-based desktop interface to manage, configure, and execute `stable-diffusion.cpp` text-to-image processes.

## Requirements

1. **Python 3** with `tkinter` library.
2. **stable-diffusion.cpp** built binaries located in the default paths:
   - `~/App/stable-diffusion.cpp/build/bin/sd-cli`
   - `~/App/stable-diffusion.cpp/build/bin/sd-server`

## Directory Structure

- `src/`: Core Python files for UI styling, runner processes, and profile managers.
- `profiles/`: Environment configuration files (`*.env`) storing preset options (e.g. `anima.env`, `bonsai.env`).
- `models/`: Folder containing model weights (`.safetensors`, `.gguf`, `.ckpt`).
- `output/`: Folder where generated images are saved.

## Getting Started

1. **Place models**:
   Put your model files inside the `models/` directory. (You can also create symbolic links to your existing models).
   
2. **Configure profiles**:
   Save environment configuration presets as `.env` files in the `profiles/` directory.

3. **Launch the interface**:
   Run the launcher script from the repository root:
   ```bash
   python sd-gui.py
   ```

## Optimal Size Configs Reference

### 16:9 / 9:16 (Widescreen)
- 704 x 384 (or 384 x 704)
- 896 x 512 (or 512 x 896)
- 1024 x 576 (or 576 x 1024)

### 2:3 / 3:2 (Portrait / Landscape)
- 448 x 640 (or 640 x 448)
- 512 x 768 (or 768 x 512)
- 640 x 960 (or 960 x 640)

### 1:1 (Square)
- 448 x 448
- 512 x 512
- 768 x 768
