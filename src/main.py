import os
import sys

# Resolve absolute path of this script (resolving any symbolic links)
real_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, real_dir)

import tkinter as tk
from app import DesktopManager

def main():
    root = tk.Tk()
    app = DesktopManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
