# Bootstrap the desktop application, configure runtime paths, and launch the main editor window.
import os

import sys

import ctypes

# Set up the runtime environment for the packaged and source-based application entry points.
# It supports application startup, packaging, or project tooling workflows.
def setup_environment():

    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

    if base_path not in sys.path:

        sys.path.insert(0, base_path)

    return base_path

BASE_DIR = setup_environment()

try:

    myappid = u'StardewSaveEditor.Modifier.1.0'

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

except Exception:

    pass

try:

    from ui.editor_ui import StardewEditor

    import tkinter as tk

    from tkinter import messagebox

    import ttkbootstrap as ttkb

    from PIL import Image, ImageTk

except ImportError:

    import traceback

    err_msg = traceback.format_exc()

    ctypes.windll.user32.MessageBoxW(0, f"Error loading modules:\n{err_msg}", u"Startup Error", 0x10)

    sys.exit(1)

# Resolve the absolute path to a bundled resource file.
# It supports application startup, packaging, or project tooling workflows.
def get_resource_path(relative_path):

    return os.path.join(BASE_DIR, relative_path)

# Create the Tk root window and start the desktop application loop.
# It supports application startup, packaging, or project tooling workflows.
def run_app():

    try:

        root = ttkb.Window(themename="cosmo")

        icon_success = False

        icon_ico_path = os.path.normpath(get_resource_path("F.ico"))

        icon_png_path = os.path.normpath(get_resource_path("F.png"))

        if os.path.exists(icon_ico_path):

            try:

                root.wm_iconbitmap(default=icon_ico_path)

                icon_success = True

            except Exception as e:

                print(f"wm_iconbitmap failed: {e}")

        if os.path.exists(icon_png_path):

            try:

                img = Image.open(icon_png_path)

                photo = ImageTk.PhotoImage(img)

                root.iconphoto(True, photo)

                root._icon_ref = photo

                icon_success = True

            except Exception as e:

                print(f"iconphoto failed: {e}")

        if not icon_success and getattr(sys, 'frozen', False):

            try:

                exe_path = sys.executable

                root.iconbitmap(exe_path)

            except:

                pass

        StardewEditor(root)

        root.mainloop()

    except Exception as e:

        import traceback

        error_msg = f"Application startup failed:\n{e}\n\n{traceback.format_exc()}"

        print(error_msg)

        try:

            temp_root = tk.Tk()

            temp_root.withdraw()

            messagebox.showerror("Startup Error", error_msg)

        except:

            pass

        sys.exit(1)

if __name__ == "__main__":

    run_app()
