from ui import StardewEditor
from utils import SaveProxy, find_save_files
from models import Farmer, Item, Pet, Chest, ITEM_CATEGORIES, PROFESSIONS

__version__ = "1.0.0"
__author__ = "Stardew Save Editor Team"

def run_app():
    """启动修改器图形界面"""
    import tkinter as tk
    root = tk.Tk()
    app = StardewEditor(root)
    root.mainloop()
