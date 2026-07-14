# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-15

### Added
- Created the standalone repository structure for `sd-gui`.
- Added the main launcher entrypoint `sd-gui.py` to launch the GUI standalone.
- Included template files `models/put_models_here` to track folder structures in Git.
- Copied all profile `.env` files (`anima.env`, `bonsai.env`) from the original repository into `profiles/`.
- Copied the `ip` network-utility helper script to the root.
- Configured `.gitignore` to keep python caches, model weights, output images (except `output_anima_demo.png`), and profile configuration files (except `anima.env` and `bonsai.env`) out of Git tracking.
- Created `README.md` containing requirements, running instructions, and optimal size presets, usage documentation for the `ip` utility script.
- Added help option (`-h`/`--help`) and descriptive headers to the `ip` network-utility script targeting local `sd-server` navigation.

### Changed
- Migrated the core GUI modules (`app.py`, `profile_manager.py`, `runner.py`, and `styles.py`) from `sd-cli/gui_desktop/src/` to `sd-gui/src/`.
- Updated path resolution for `WORKSPACE_DIR` in `src/app.py` from three parent directories to two so that the application works seamlessly from the new standalone root structure.
