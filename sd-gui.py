import os
import sys

# Resolve path to the 'src' directory
real_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(real_dir, "src"))

import tkinter as tk
from app import DesktopManager

def main():
    root = tk.Tk()
    app = DesktopManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
