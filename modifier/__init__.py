# Expose the main modifier package entry points used by the desktop application.
from .models import Chest, Farmer, ITEM_CATEGORIES, Item, PROFESSIONS, Pet

from .ui import StardewEditor

from .utils import SaveProxy, find_save_files

__version__ = "1.0.0"

__author__ = "Stardew Save Editor Team"

# Create the Tk root window and start the desktop application loop.
# It supports application startup, packaging, or project tooling workflows.
def run_app():

    import tkinter as tk

    root = tk.Tk()

    StardewEditor(root)

    root.mainloop()
