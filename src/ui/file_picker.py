"""File picker wrapper for the GUI.

Why this module exists: Tk's legacy `tkinter.filedialog` draws its own widget
tree and paints the item highlight with the system highlight colour, so hovering
a directory flashes the whole row white, and picking a file means clicking an
item in the list. The desktop's default picker is the GTK file chooser, which
follows the dark theme, highlights the selection in blue, shows a path bar to
type into, and limits the choice to its Open button. Every picker call in the
app goes through this wrapper so the white-hover behaviour cannot come back.

Backend order, decided once at first use:
  1. GTK's native chooser (Gtk.FileChooserNative): dark theme, extension filters
     from the field's `filetypes`, a typed path via the location bar, and the
     choice confirmed by the dialog's own Open button.
  2. zenity --file-selection, the desktop default picker CLI. Same GTK chooser,
     no extension filters.
  3. Tk's filedialog, last resort: no filters, and the white hover flash.
"""

import shutil
import subprocess
import time
from tkinter import filedialog

# The backend is chosen once and cached by select_backend().
_backend = None

# True while a GTK picker is open. Tk's events are pumped during the pick, so a
# click on another picker button can land inside the pump loop; the guard makes
# that second call return "" instead of opening a nested dialog.
_picking = [False]


def select_backend():
    """Picks the picker backend, GTK first, then zenity, then Tk's dialog.
    The probe that proves GTK works here is test_picker.py: the GTK chooser
    renders dark on the Wayland display, accepts `filetypes` as filters, and
    Tk stays responsive after the dialog closes."""
    global _backend
    if _backend is not None:
        return _backend
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
        _backend = "gtk"
    except Exception:
        _backend = "zenity" if shutil.which("zenity") else "tk"
    return _backend


def add_gtk_filters(dialog, filetypes):
    """Turns Tk's `filetypes` pairs (label, space-separated globs) into GTK
    filters, one per pair, in the given order, so the chooser's filter dropdown
    matches the field. Returns the number of filters added."""
    if not filetypes:
        return 0
    from gi.repository import Gtk
    added = 0
    for label, pattern in filetypes:
        flt = Gtk.FileFilter()
        flt.set_name(label)
        for glob in pattern.split():
            flt.add_pattern(glob)
        dialog.add_filter(flt)
        added += 1
    return added


def zenity_args(directory, title=None, initialdir=None):
    """The zenity call the desktop default picker answers to. `--directory`
    picks a folder, `--filename=DIR` sets where the chooser opens, `--title`
    the header. zenity has no extension filters, so `filetypes` is not used."""
    args = ["zenity", "--file-selection"]
    if title:
        args += ["--title", title]
    if directory:
        args.append("--directory")
    if initialdir:
        args.append(f"--filename={initialdir}")
    return args


def pick_file(title=None, filetypes=None, initialdir=None, parent=None):
    """Picks one file. Returns the chosen path, or "" when the picker is closed.
    `filetypes` is Tk's list of (label, globs) pairs; `initialdir` is where the
    chooser opens. `parent` is the Tk widget whose mainloop drives the pick: GTK's
    chooser is its own window, and a Tk window id cannot be its transient parent
    in this GI version, so `parent` is used to pump events, not to parent the
    dialog."""
    backend = select_backend()
    if backend == "gtk":
        return _gtk_pick(False, title, filetypes, initialdir, parent)
    if backend == "zenity":
        return _zenity_pick(False, title, initialdir)
    return filedialog.askopenfilename(title=title, filetypes=filetypes,
                                      initialdir=initialdir, parent=parent)


def pick_directory(title=None, initialdir=None, parent=None):
    """Picks one folder. Returns the chosen path, or "" when the picker is closed.
    `parent` is the Tk widget whose mainloop drives the pick (see pick_file)."""
    backend = select_backend()
    if backend == "gtk":
        return _gtk_pick(True, title, None, initialdir, parent)
    if backend == "zenity":
        return _zenity_pick(True, title, initialdir)
    return filedialog.askdirectory(title=title, initialdir=initialdir, parent=parent)


def _tk_root(parent):
    """The Tk widget whose mainloop must keep running during a GTK pick. Most
    call sites pass a Tk widget; the two that pass the App object are read
    through its `root`."""
    if parent is not None and hasattr(parent, "winfo"):
        return parent
    return getattr(parent, "root", None)


def _gtk_pick(directory, title, filetypes, initialdir, parent=None):
    """Opens GTK's native chooser without blocking Tk, and returns the chosen
    path ("" when the picker is closed).

    The freeze this absorbs: `run()` blocks Tk's mainloop for as long as the
    dialog is open, so the app stops answering its events. Measured in
    probe_pump.py: with `run()`, Tk's heartbeat went silent for 6.66 s while
    the dialog was open, and Hyprland raised its "application not responding"
    dialog for sd-gui. So the chooser is shown with `show()`, its `response`
    signal is connected, and both queues are pumped from the same loop: GTK
    events with `main_iteration_do`, Tk events with `root.update()`. The dialog
    works, the app answers the compositor throughout, and the path is read on
    ACCEPT only; Cancel, Esc and the corner button give "".

    `get_current_folder` is the answer for the folder action, `get_filename`
    for the file action."""
    from gi.repository import Gtk
    root = _tk_root(parent)
    if _picking[0]:
        return ""
    dialog = Gtk.FileChooserNative()
    dialog.set_title(title or ("Select a Folder" if directory else "Select a File"))
    dialog.set_action(Gtk.FileChooserAction.SELECT_FOLDER if directory else Gtk.FileChooserAction.OPEN)
    if not directory:
        add_gtk_filters(dialog, filetypes)
    if initialdir:
        dialog.set_current_folder(initialdir)
    result = [None]

    def on_response(dlg, resp):
        if resp == Gtk.ResponseType.ACCEPT:
            picked = dlg.get_current_folder() if directory else dlg.get_filename()
            result[0] = picked or ""
        else:
            result[0] = ""
        dlg.destroy()

    dialog.connect("response", on_response)
    _picking[0] = True
    dialog.show()
    try:
        while result[0] is None:
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
            if root is None:
                time.sleep(0.05)
                continue
            try:
                root.update()
            except Exception:
                break          # Tk is going away; the pick is abandoned
            time.sleep(0.02)
    finally:
        _picking[0] = False
    return result[0] or ""


def _zenity_pick(directory, title, initialdir):
    """zenity prints the chosen path on success and nothing when cancelled, so
    a non-zero exit or empty stdout means the picker was closed."""
    out = subprocess.run(zenity_args(directory, title, initialdir),
                         capture_output=True, text=True)
    if out.returncode != 0:
        return ""
    for line in out.stdout.splitlines():
        if line.strip():
            return line.strip()
    return ""
