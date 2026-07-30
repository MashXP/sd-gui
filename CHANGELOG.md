# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-07-30

### Added
- **Modular UI tab architecture**: Monolithic `app.py` split into dedicated tab modules under `src/ui/`:
  - `tab_generator.py` — Generator tab with collapsible parameter groups
  - `tab_gallery.py` — Output gallery with thumbnail grid and Open File/Folder support
  - `tab_history.py` — Execution history with SQLite-backed `history_db.py` and double-click to load params
  - `tab_prompt_helper.py` — Prompt Tag Helper with categorized chip tags and dynamic wrap layout
  - `widgets.py` — Reusable components: `CollapsibleFrame` accordion sections
- **T5XXL model support**: New text encoder path selectors for T5XXL and LLM models.
- **Generation mode selector**: GUI support for `-M` flag values — `txt2img`, `img2img`, `vid_gen`, `inpaint`, `convert`.
- **Video generation settings**: Flow shift and video frame count inputs for `vid_gen` mode.
- **Extra CLI flags**: Free-form input field for passing arbitrary CLI flags to `sd-cli`.
- **VAE direct convolution toggle**: Checkbox to enable `--vae-conv-direct` for performance.
- **Output preview tab**: Default sub-tab in the right pane showing generated image preview, file path link, Open File and Open Folder buttons; Terminal Logs as secondary sub-tab.
- **Auto-refresh output**: Generator output tab refreshes with latest image on process completion.
- **Gallery Open Folder**: Button to open the output folder via `xdg-open`.
- **Wayland clipboard support**: `Ctrl+C`/`Ctrl+X` in all text widgets uses `wl-copy` with `start_new_session=True` to bypass XWayland bridge and avoid SIGSEGV crashes (e.g. Antigravity IDE).
- **500-line rolling buffer**: Terminal log console capped to prevent memory growth.
- **Combobox scroll-steal fix**: Mousewheel event filtering to prevent combobox scroll stealing.
- **Text shortcuts**: `Ctrl+A` (Select All), `Ctrl+Delete` (Delete Word Forward), `Ctrl+Backspace` (Delete Word Backward) in all text/entry widgets.
- **Desktop integration**: `sd-gui.desktop` file for Linux desktop launcher support.
- **Application icon**: `icon.png` for branding and `.desktop` file.
- **History pagination**: 20 rows per page with Prev/Next navigation and page counter.
- **Shift+Click range selection**: Shift+click on checkbox column toggles a range of rows from the anchor point.
- **Drag area select**: Drag across the checkbox column to toggle rows in sweep.
- **Ctrl+C on cells**: Click any prompt or seed cell, then Ctrl+C to copy that cell's value to clipboard.
- **Copy toast notification**: Toast appears at app bottom-center confirming the copied cell content.
- **Random seed checkbox**: Toggle to auto-generate random seeds (`-1`) in the Generator tab.
- **History recording toggle**: Button to pause/resume automatic logging of runs to history.
- **Extended history fields**: Generation time, mode, steps, CFG scale, and sampler are now stored and displayed.
- **Seed extraction**: Actual seed used by the process is extracted from terminal output and logged to history.

### Changed
- **UI architecture overhaul**: Refactored from a single monolithic `app.py` (~793 lines) to modular tab classes and a `src/ui/` package (~1207 lines added).
- **History table columns**: Added check, mode, steps, CFG, time, and sampler columns; reorganized layout.
- **Typography upgrade**: Replaced hardcoded `Helvetica` font with `fc-list` based font detection that selects the first available font from a preferred stack (Inter, Roboto, Noto Sans, etc.) without making any X11 requests.
- **Font sizes**: Bumped all font sizes by 1pt to improve readability on high-DPI displays (1.33x Tk scaling detected).
- **Checkbox rendering**: Switched from Unicode `☐`/`☑` to ASCII `[ ]`/`[x]` for reliable rendering across all fonts.
- **Toast positioning**: Changed `update_idletasks()` to `update()` + `winfo_reqwidth/height` to prevent toast from appearing at screen corner before window is fully mapped.
- **HistoryDB query**: `get_all()` now accepts offset param; added `count_all()` for pagination.
- **CLI mode flags**: Updated `-M` flag values from legacy names to match `stable-diffusion.cpp` spec (e.g. `img_gen` instead of `txt2img`).
- **UI styling cleanup**: Removed all emoji decorations from the interface.
- **Terminal output color**: Updated terminal text color for improved readability.
- **Binary mode layout**: Generator form dynamically shows/hides fields depending on `sd-cli` vs `sd-server` mode.
- **`.gitignore`**: Updated to account for new project structure.

### Fixed
- **X11 BadLength crash**: Removed `tk.PhotoImage(file=icon.png)` call that sent large pixmap data to XWayland, exceeding buffer limits.
- **Font specification**: Font family is no longer passed as a tuple (which Tkinter stringified into an invalid font name); resolved via `fc-list` to a single valid family name.
- **Hardcoded Helvetica**: All remaining `('Helvetica', 10)` references in `tab_generator.py` replaced with `styles.FONT_MAIN`/`styles.FONT_BOLD` for consistent theming.
- **Prompt chip overflow**: Dynamic wrap layout prevents horizontal overflow in Prompt Tag Helper.
- **Execution History dark theme**: Fixed white background regression in the Treeview on dark themes.
- **Wayland clipboard crash**: All clipboard operations (`Ctrl+C`/`Ctrl+X`, copy buttons) now use `wl-copy` with process group isolation to prevent SIGSEGV from XWayland bridge.
- **Copy button isolation**: Same `start_new_session=True` fix applied to all copy buttons.
- **History drag-select**: Treeview `selectmode` changed from `"none"` to `"extended"` to allow native click-drag row selection.
- **Shift+Click anchor**: Last clicked row index is now tracked unconditionally (not only on checkbox column), fixing Shift+click range selection after clicking other columns.
- **Checkbox column width**: Increased from 30px to 50px so the glyph is actually visible.
- **Ctrl+V paste on X11**: Custom paste handler deletes selected text before inserting clipboard content, working around Tk's intentional skip of selection deletion on X11.
- **Ctrl+A select-all**: Stale `tk.SEL` ranges are now cleared (`tag_remove`) before selecting all, preventing duplicate highlights.
- **Prompt scrollbar**: Prompt and negative-prompt text widgets now have a vertical scrollbar that only activates when content overflows; mousewheel scrolls the text widget only while hovering over it, letting the parent tab scroll normally otherwise.

## [1.0.0] - 2026-07-15

### Added
- Created the standalone repository structure for `sd-gui`.
- Added the main launcher entrypoint `sd-gui.py` to launch the GUI standalone.
- Included template files `models/put_models_here` to track folder structures in Git.
- Copied all profile `.env` files (`anima.env`, `bonsai.env`) from the original repository into `profiles/`.
- Copied the `ip` network-utility helper script to the root.
- Configured `.gitignore` to keep python caches, model weights, output images (except `output_anima_demo.png`), and profile configuration files (except `anima.env` and `bonsai.env`) out of Git tracking.
- Created `README.md` containing requirements, running instructions, optimal size presets, usage documentation for the `ip` utility script, preview images (`gui_preview.png` and `output_anima_demo.png`), and citations/credits for `stable-diffusion.cpp` and the `Anima` model.
- Added help option (`-h`/`--help`) and descriptive headers to the `ip` network-utility script targeting local `sd-server` navigation.

### Changed
- Migrated the core GUI modules (`app.py`, `profile_manager.py`, `runner.py`, and `styles.py`) from `sd-cli/gui_desktop/src/` to `sd-gui/src/`.
- Updated path resolution for `WORKSPACE_DIR` in `src/app.py` from three parent directories to two so that the application works seamlessly from the new standalone root structure.
