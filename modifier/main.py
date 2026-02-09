import os
import sys
import ctypes

# 1. 立即设置运行环境（必须在任何业务代码导入之前）
def setup_environment():
    """设置运行环境，确保模块能被正确找到"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 环境
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    if base_path not in sys.path:
        sys.path.insert(0, base_path)
    return base_path

# 执行环境设置
BASE_DIR = setup_environment()

# 2. 修复任务栏图标：尽早设置 AppUserModelID
try:
    myappid = u'StardewSaveEditor.Modifier.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# 3. 导入业务模块
try:
    import ui.editor_ui
    from ui.editor_ui import StardewEditor
    import tkinter as tk
    from tkinter import messagebox
    import ttkbootstrap as ttkb
    from PIL import Image, ImageTk
    import models
    import utils
except ImportError as e:
    import traceback
    err_msg = traceback.format_exc()
    ctypes.windll.user32.MessageBoxW(0, f"Error loading modules:\n{err_msg}", u"Startup Error", 0x10)
    sys.exit(1)

def get_resource_path(relative_path):
    """获取资源的绝对路径"""
    return os.path.join(BASE_DIR, relative_path)

def run_app():
    """启动应用程序"""
    try:
        # 使用 ttkbootstrap 创建现代化窗口
        root = ttkb.Window(themename="cosmo")
        
        # 窗口标题
        root.title("Stardew Save Editor")
        
        # 强制设置图标逻辑
        icon_success = False
        
        # 获取图标路径并标准化
        icon_ico_path = os.path.normpath(get_resource_path("F.ico"))
        icon_png_path = os.path.normpath(get_resource_path("F.png"))
        
        # 方法 1: 使用 iconbitmap (对 Windows 窗口最有效)
        if os.path.exists(icon_ico_path):
            try:
                # 使用 wm_iconbitmap(default=...) 对所有窗口生效
                root.wm_iconbitmap(default=icon_ico_path)
                icon_success = True
            except Exception as e:
                print(f"wm_iconbitmap failed: {e}")
        
        # 方法 2: 使用 iconphoto (对任务栏分组最有效)
        if os.path.exists(icon_png_path):
            try:
                img = Image.open(icon_png_path)
                photo = ImageTk.PhotoImage(img)
                # True 表示对所有后续创建的窗口生效
                root.iconphoto(True, photo) # type: ignore
                # 重要：必须保持引用，否则会被垃圾回收
                root._icon_ref = photo # type: ignore
                icon_success = True
            except Exception as e:
                print(f"iconphoto failed: {e}")
                
        # 如果以上都失败，且在打包环境下，尝试直接从 exe 提取图标（进阶写法）
        if not icon_success and getattr(sys, 'frozen', False):
            try:
                exe_path = sys.executable
                root.iconbitmap(exe_path)
            except:
                pass
            
        app = StardewEditor(root)
        root.mainloop()
    except Exception as e:
        import traceback
        error_msg = f"程序启动失败:\n{e}\n\n{traceback.format_exc()}"
        print(error_msg)
        
        try:
            # 尝试使用已有的 tk 和 messagebox 显示错误
            # 如果之前的 tk.Tk() 失败了，可能需要创建一个新的 root
            temp_root = tk.Tk()
            temp_root.withdraw()
            messagebox.showerror("启动错误", error_msg)
        except:
            # 如果连弹窗都失败了，就只能放弃了
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    run_app()
