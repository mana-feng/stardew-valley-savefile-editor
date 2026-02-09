import os
import sys
import shutil
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog, colorchooser
import ttkbootstrap as ttkb
from ttkbootstrap.constants import PRIMARY, SECONDARY
from ttkbootstrap.dialogs.colorchooser import ColorChooserDialog
from models.item_data import ITEM_CATEGORIES
from models.profession_data import PROFESSIONS
from models.pet_data import PET_DATA
from models.special_powers import SPECIAL_POWERS, ACHIEVEMENTS
from models.item import Item
from utils.save_utils import find_save_files, sync_player_xml, SaveProxy, list_save_folders
from utils import tr

def setup_mousewheel(widget):
    """为 Widget (Canvas/Listbox/Treeview) 添加鼠标滚轮支持 (专为 Windows 优化)"""
    def _on_mousewheel(event):
        try:
            if not widget.winfo_exists():
                return

            target = widget.winfo_containing(event.x_root, event.y_root)
            if not target:
                return
            
            current = target
            while current is not None and current != widget:
                current = current.master
            if current != widget:
                return
            
            # Windows 下使用 delta，通常为 120 的倍数
            if event.delta != 0:
                # 检查是否按下 Shift 键用于横向滚动
                if event.state & 0x1:
                    # 横向滚动前检查边界
                    if event.delta > 0: # 滚轮向上(左移)
                        if widget.xview()[0] <= 0: return
                    else: # 滚轮向下(右移)
                        if widget.xview()[1] >= 1: return
                        
                    # 横向滚动：稍微加快速度 (*2)
                    widget.xview_scroll(int(-2 * (event.delta / 120)), "units")
                else:
                    # 纵向滚动前检查边界
                    if event.delta > 0: # 滚轮向上
                        if widget.yview()[0] <= 0: return
                    else: # 滚轮向下
                        if widget.yview()[1] >= 1: return

                    # 纵向滚动：加快速度 (*3)，提升流畅感
                    widget.yview_scroll(int(-3 * (event.delta / 120)), "units")
        except (tk.TclError, AttributeError):
            pass

    widget.bind_all("<MouseWheel>", _on_mousewheel, add=True)

def center_window(window, width, height):
    """将窗口置于屏幕中央"""
    window.withdraw()  # 先隐藏窗口，防止在左上角闪烁
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.deiconify()  # 设置好位置后再显示

class AddItemDialog(ttkb.Toplevel):
    def __init__(self, parent, title=None, initial_data=None, category_hint=None):
        super().__init__(parent)
        if title is None:
            title = tr.translate("add_item")
        self.title(title)
        center_window(self, 450, 600)
        self.result = None
        self.category_hint = category_hint
        self.transient(parent)
        self.grab_set()
        
        # 使用从 models 导入的分类
        self.categories = ITEM_CATEGORIES
        
        # 建立分类映射：原始 key -> 翻译后的名称
        self.category_names = {cat: tr.translate(cat) for cat in self.categories.keys()}
        self.rev_category_names = {v: k for k, v in self.category_names.items()}
        
        # 展平一份用于搜索
        self.flat_presets = {}
        for cat, items in self.categories.items():
            translated_cat = self.category_names[cat]
            for name, data in items.items():
                # 翻译物品名称（如果存在翻译）
                translated_item_name = tr.translate(name)
                # 确保 data 中包含 id 和 name 字段，以便后续 update_search 使用
                if isinstance(data, dict):
                    item_info = dict(data)
                else:
                    item_info = {"id": str(data)}

                if "name" not in item_info:
                    item_info["name"] = name
                if "id" not in item_info:
                    item_info["id"] = ""
                
                # 自动推断前缀 (针对 1.6 格式)
                item_id = item_info["id"]
                if "(" not in item_id:
                    if cat == "rings": prefix = "O"
                    elif cat == "trinkets": prefix = "TR"
                    elif cat == "hats": prefix = "H"
                    elif cat == "shoes": prefix = "B"
                    elif cat == "clothes":
                        # 衣服类需要区分上衣和裤子，但在 ITEM_CATEGORIES 中通常是混在一起的
                        # 这里简单处理，如果 ID 以 (S) 或 (P) 开头则不处理，否则默认不加前缀
                        # 或者根据 category_hint 推断，但在初始化时还不知道 hint
                        prefix = None
                    else: prefix = None
                    
                    if prefix:
                        item_info["id"] = f"({prefix}){item_id}"
                
                self.flat_presets[f"[{translated_cat}] {translated_item_name}"] = {
                    "data": item_info,
                    "cat_key": cat
                }

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 搜索和选择区
        search_frame = ttk.LabelFrame(main_frame, text=tr.translate("quick_select_item"), padding=10)
        search_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 使用 grid 布局搜索栏
        controls_frame = ttk.Frame(search_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 分类选择
        ttk.Label(controls_frame, text=tr.translate("category")).grid(row=0, column=0, sticky=tk.W)
        
        # 如果有提示，尝试匹配分类
        default_cat = tr.translate("all")
        if category_hint:
            # 映射属性到分类名
            hint_map = {
                "leftRing": "rings",
                "rightRing": "rings",
                "trinketItem": "trinkets",
                "boots": "shoes",
                "hat": "hats",
                "shirtItem": "clothes",
                "pantsItem": "clothes"
            }
            mapped_cat_key = hint_map.get(category_hint)
            if mapped_cat_key in self.category_names:
                default_cat = self.category_names[mapped_cat_key]
        
        self.category_var = tk.StringVar(value=default_cat)
        self.category_cb = ttk.Combobox(controls_frame, textvariable=self.category_var, state="readonly", width=15)
        self.category_cb["values"] = [tr.translate("all")] + sorted(list(self.category_names.values()))
        self.category_cb.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        self.category_cb.bind("<<ComboboxSelected>>", self.update_search)
        
        ttk.Label(controls_frame, text=tr.translate("search")).grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_search)
        ttk.Entry(controls_frame, textvariable=self.search_var).grid(row=0, column=3, sticky=tk.EW, padx=5, pady=2)
        controls_frame.columnconfigure(3, weight=1)
        
        # 列表框区域
        list_container = ttk.Frame(search_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.item_listbox = tk.Listbox(list_container, height=10)
        
        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(list_container, orient=tk.HORIZONTAL, command=self.item_listbox.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 垂直滚动条
        v_scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.item_listbox.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.item_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.item_listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        
        self.item_listbox.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        setup_mousewheel(self.item_listbox)
        
        # 初始化列表
        self.update_search()
        
        # 自定义输入区
        edit_frame = ttk.LabelFrame(main_frame, text=tr.translate("item_details"), padding=10)
        edit_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(edit_frame, text=tr.translate("item_name")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=initial_data["name"] if initial_data else "")
        ttk.Entry(edit_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        
        ttk.Label(edit_frame, text=tr.translate("item_id")).grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        # 获取物品 ID (如果是修改模式，尝试从 initial_data 获取)
        initial_id = ""
        if initial_data:
            # 尝试从模型获取 itemId
            model = initial_data.get("model")
            if model:
                initial_id = model.itemId or ""
        
        self.id_var = tk.StringVar(value=initial_id)
        if initial_data and "id" in initial_data and initial_data["id"]:
            self.id_var.set(initial_data["id"])
            
        ttk.Entry(edit_frame, textvariable=self.id_var, width=10).grid(row=0, column=3, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(edit_frame, text=tr.translate("quantity")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.stack_var = tk.StringVar(value=initial_data["stack"] if initial_data else "1")
        ttk.Entry(edit_frame, textvariable=self.stack_var).grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        
        ttk.Label(edit_frame, text=tr.translate("quality")).grid(row=1, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        self.quality_map = {
            tr.translate("normal"): "0",
            tr.translate("silver"): "1",
            tr.translate("gold"): "2",
            tr.translate("iridium"): "4"
        }
        self.rev_quality_map = {v: k for k, v in self.quality_map.items()}
        
        initial_q_str = tr.translate("normal")
        if initial_data:
            initial_q_str = self.rev_quality_map.get(str(initial_data["quality"]), tr.translate("normal"))
            
        self.quality_var = tk.StringVar(value=initial_q_str)
        ttk.Combobox(edit_frame, textvariable=self.quality_var, values=list(self.quality_map.keys()), state="readonly", width=10).grid(row=1, column=3, sticky=tk.W, pady=5, padx=5)
        
        edit_frame.columnconfigure(1, weight=1)
        # edit_frame.columnconfigure(3, weight=1) # 不让 ID 和品质占太多空间
        
        # 说明
        help_text = f"{tr.translate('description')}: {tr.translate('id_help_text')}"
        ttk.Label(main_frame, text=help_text, font=("", 8), foreground="gray").pack(pady=5)
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text=tr.translate("confirm_add"), command=self.on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text=tr.translate("cancel"), command=self.destroy).pack(side=tk.LEFT, padx=10)

    def update_search(self, *args):
        search_term = self.search_var.get().lower()
        selected_cat = self.category_var.get()
        self.item_listbox.delete(0, tk.END)
        
        matches = []
        for display_name, entry in self.flat_presets.items():
            data = entry["data"]
            # 分类过滤
            if selected_cat != tr.translate("all") and not display_name.startswith(f"[{selected_cat}]"):
                continue
            
            # 装备位前缀过滤
            item_id = str(data.get("id", ""))
            if self.category_hint:
                if self.category_hint == "shirtItem" and not item_id.startswith("(S)"):
                    continue
                if self.category_hint == "pantsItem" and not item_id.startswith("(P)"):
                    continue
                if self.category_hint == "hat" and not item_id.startswith("(H)"):
                    continue
                if self.category_hint == "boots" and not item_id.startswith("(B)"):
                    continue
                if self.category_hint == "trinketItem" and not item_id.startswith("(TR)"):
                    continue
                if self.category_hint in ["leftRing", "rightRing"]:
                    if "(" in item_id and not item_id.startswith("(O)"):
                        continue
                
            # 搜索词过滤: 支持显示名、英文名、ID
            name_for_search = display_name.split("] ", 1)[-1] if "] " in display_name else display_name
            en_name = data.get("name", "").lower()
            item_id_lower = item_id.lower()
            
            if (search_term in name_for_search.lower() or 
                search_term in en_name or 
                search_term in item_id_lower):
                matches.append((display_name, entry))
        
        # 排序：常用项优先，然后按名称
        matches.sort(key=lambda x: (0 if tr.translate("common_items") in x[0] else 1, x[0]))
        
        for display_name, entry in matches:
            data = entry["data"]
            # 在列表显示中包含 ID，方便区分同名物品
            list_text = f"{display_name} (ID: {data.get('id', 'N/A')})"
            self.item_listbox.insert(tk.END, list_text)
            # 保存映射，以便在 on_listbox_select 中获取数据
            if not hasattr(self, "item_listbox_data"):
                self.item_listbox_data = {}
            self.item_listbox_data[list_text] = data

    def on_listbox_select(self, event):
        selection = self.item_listbox.curselection()
        if not selection: return
        
        list_text = self.item_listbox.get(selection[0])
        if hasattr(self, "item_listbox_data") and list_text in self.item_listbox_data:
            p = self.item_listbox_data[list_text]
            # 从列表文本中提取纯显示名 (去掉 [分类] 前缀和 (ID: ...) 后缀)
            # 兼容旧逻辑：如果 display_name 包含 [分类]，则分割
            pure_name = list_text.split("] ", 1)[-1].split(" (ID:", 1)[0] if "] " in list_text else list_text.split(" (ID:", 1)[0]
            self.name_var.set(pure_name)
            self.id_var.set(p.get("id", ""))

    def on_ok(self):
        if not self.id_var.get() or not self.name_var.get():
            messagebox.showwarning(tr.translate("info"), tr.translate("name_id_empty"))
            return
        if not self.stack_var.get().isdigit():
            messagebox.showerror(tr.translate("error"), tr.translate("quantity_must_be_number"))
            return
            
        self.result = {
            "name": self.name_var.get(),
            "id": self.id_var.get(),
            "stack": self.stack_var.get(),
            "quality": self.quality_map.get(self.quality_var.get(), "0")
        }
        self.destroy()

class ProfessionDialog(ttkb.Toplevel):
    def __init__(self, parent, current_professions, player_levels):
        super().__init__(parent)
        self.title(tr.translate("skill_professions"))
        center_window(self, 700, 850)
        self.result = list(current_professions)
        self.player_levels = player_levels # { "Farming": level, ... }
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 直接使用主容器，不再添加滚动条
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        self.check_vars = {}
        
        categories_map = {
            "Farming": tr.translate("farming_skill"),
            "Mining": tr.translate("mining_skill"),
            "Foraging": tr.translate("foraging_skill"),
            "Fishing": tr.translate("fishing_skill"),
            "Combat": tr.translate("combat_skill")
        }
        
        for cat_key, display_name in categories_map.items():
            group_frame = ttk.LabelFrame(content_frame, text=display_name, padding=10)
            group_frame.pack(fill=tk.X, padx=10, pady=5)
            
            profs = PROFESSIONS.get(cat_key, {})
            
            # 分离 5 级 and 10 级
            lvl5 = {k: v for k, v in profs.items() if v[2] == 5}
            lvl10 = {k: v for k, v in profs.items() if v[2] == 10}
            
            # 布局：左边是 5 级，右边是对应的 10 级
            for p5_id, p5_info in lvl5.items():
                row_frame = ttk.Frame(group_frame)
                row_frame.pack(fill=tk.X, pady=5)
                
                # 5 级职业
                p5_name_key, p5_desc_key, _, _ = p5_info
                p5_name = tr.translate(p5_name_key)
                p5_desc = tr.translate(p5_desc_key)
                var5 = tk.BooleanVar(value=(p5_id in self.result))
                self.check_vars[p5_id] = var5
                
                # 检查等级是否足够
                current_lvl = self.player_levels.get(cat_key, 0)
                state5 = tk.NORMAL if current_lvl >= 5 else tk.DISABLED
                
                lvl5_text = tr.translate("level_5_prefix") + p5_name
                cb5 = ttk.Checkbutton(row_frame, text=lvl5_text, variable=var5, state=state5,
                                      command=lambda pid=p5_id: self.update_profession_state(pid))
                cb5.pack(side=tk.LEFT, padx=(0, 20))
                
                # 5 级 Tip
                self._add_tip(cb5, p5_desc)
                
                # 对应的 10 级职业
                p10_frame = ttk.Frame(row_frame)
                p10_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                related_p10 = {k: v for k, v in lvl10.items() if v[3] == p5_id}
                for p10_id, p10_info in related_p10.items():
                    p10_name_key, p10_desc_key, _, _ = p10_info
                    p10_name = tr.translate(p10_name_key)
                    p10_desc = tr.translate(p10_desc_key)
                    var10 = tk.BooleanVar(value=(p10_id in self.result))
                    self.check_vars[p10_id] = var10
                    
                    state10 = tk.NORMAL if current_lvl >= 10 else tk.DISABLED
                    lvl10_text = tr.translate("level_10_prefix") + p10_name
                    cb10 = ttk.Checkbutton(p10_frame, text=lvl10_text, variable=var10, state=state10,
                                           command=lambda pid=p10_id: self.update_profession_state(pid))
                    cb10.pack(side=tk.LEFT, padx=10)
                    
                    # 10 级 Tip
                    self._add_tip(cb10, p10_desc)

        btn_frame = ttk.Frame(content_frame, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btn_frame, text=tr.translate("confirm_modify"), command=self.on_ok, width=20).pack(pady=10)

    def update_profession_state(self, changed_id):
        """同步职业选择逻辑"""
        is_checked = self.check_vars[changed_id].get()
        info = None
        category = None
        for cat_name, cat_data in PROFESSIONS.items():
            if changed_id in cat_data:
                info = cat_data[changed_id]
                category = cat_data
                break
        
        if not info or category is None: return
        
        level = info[2]
        parent_id = info[3]
        
        if level == 5:
            if is_checked:
                # 1. 取消选中同分类的另一个 5 级及其子级
                for other_id, other_info in category.items():
                    if other_id != changed_id and other_info[2] == 5 and self.check_vars.get(other_id) and self.check_vars[other_id].get():
                        self.check_vars[other_id].set(False)
                        # 取消选中其子级
                        for child_id, child_info in category.items():
                            if child_info[3] == other_id:
                                if self.check_vars.get(child_id):
                                    self.check_vars[child_id].set(False)
            else:
                # 2. 取消选中 5 级，则自动取消所有子级
                for child_id, child_info in category.items():
                    if child_info[3] == changed_id:
                        if self.check_vars.get(child_id):
                            self.check_vars[child_id].set(False)
        elif level == 10:
            if is_checked:
                # 1. 选中 10 级，必须确保父级已选中
                if parent_id is not None and self.check_vars.get(parent_id) and not self.check_vars[parent_id].get():
                    self.check_vars[parent_id].set(True)
                    # 级联更新父级状态（取消另一分支）
                    self.update_profession_state(parent_id)
                
                # 2. 取消选中同父级的另一个 10 级
                for other_id, other_info in category.items():
                    if other_id != changed_id and other_info[2] == 10 and other_info[3] == parent_id and self.check_vars.get(other_id) and self.check_vars[other_id].get():
                        self.check_vars[other_id].set(False)
            else:
                # 取消选中 10 级，无额外逻辑
                pass
    
    def _add_tip(self, widget, text):
        def on_enter(e):
            self.tip_label.config(text=f"{tr.translate('description')}: {text}")
        def on_leave(e):
            self.tip_label.config(text=tr.translate("hover_tip"))
            
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    # 在 ProfessionDialog 中添加一个用于显示 Tip 的 Label
    @property
    def tip_label(self):
        if not hasattr(self, "_tip_label"):
            self._tip_label = ttk.Label(self, text=tr.translate("hover_tip"), foreground="gray", font=("", 9), wraplength=650)
            self._tip_label.pack(side=tk.BOTTOM, pady=(0, 10), padx=20)
        return self._tip_label

    def on_ok(self):
        # 保留不在当前字典中的职业（可能是 MOD 增加的或未来的新职业）
        known_ids = set(self.check_vars.keys())
        new_result = [p_id for p_id in self.result if p_id not in known_ids]
        # 添加勾选的职业
        new_result.extend([p_id for p_id, var in self.check_vars.items() if var.get()])
        self.result = new_result
        self.destroy()

class ChestDialog(ttkb.Toplevel):
    def __init__(self, parent, chest_data):
        super().__init__(parent)
        title = f"{tr.translate('modify_chest')} - {chest_data['location']}"
        self.title(title)
        center_window(self, 400, 350)
        self.result = None
        self.chest_data = chest_data
        self.model = chest_data['model']
        
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 容量
        ttk.Label(main_frame, text=tr.translate("chest_capacity")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cap_var = tk.StringVar(value=str(self.model.capacity))
        ttk.Entry(main_frame, textvariable=self.cap_var, width=15).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 特殊类型
        ttk.Label(main_frame, text=tr.translate("special_type")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value=self.model.specialChestType or "None")
        types = ["None", "BigChest", "JunimoChest", "StoneChest", "MiniShippingBin"]
        # 使用翻译后的显示名称
        display_types = {t: tr.translate(f"chest_type_{t.lower()}") for t in types}
        self.rev_display_types = {v: k for k, v in display_types.items()}
        
        ttk.Combobox(main_frame, textvariable=self.type_var, values=list(display_types.values()), width=13).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 全局 ID
        ttk.Label(main_frame, text=tr.translate("global_inventory_id")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.gid_var = tk.StringVar(value=self.model.globalInventoryId or "")
        ttk.Entry(main_frame, textvariable=self.gid_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 颜色 (简易展示)
        ttk.Label(main_frame, text=tr.translate("color_rgb")).grid(row=3, column=0, sticky=tk.W, pady=5)
        color = self.model.playerChoiceColor or {"R": 0, "G": 0, "B": 0}
        self.color_var = tk.StringVar(value=f"{color['R']},{color['G']},{color['B']}")
        
        color_input_frame = ttk.Frame(main_frame)
        color_input_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        color_entry = ttk.Entry(color_input_frame, textvariable=self.color_var, width=15)
        color_entry.pack(side=tk.LEFT)
        
        # 颜色预览块
        self.color_preview = tk.Canvas(color_input_frame, width=20, height=20, highlightthickness=1, highlightbackground="gray")
        self.color_preview.pack(side=tk.LEFT, padx=5)
        
        def update_preview(*args):
            try:
                rgb = self.color_var.get().split(",")
                if len(rgb) == 3:
                    r, g, b = map(int, rgb)
                    # 确保在 0-255 范围内
                    r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
                    hex_color = f'#{r:02x}{g:02x}{b:02x}'
                    self.color_preview.config(bg=hex_color)
            except:
                self.color_preview.config(bg="white")
        
        self.color_var.trace_add("write", update_preview)
        update_preview() # 初始更新

        # 颜色选择器按钮
        def choose_color():
            curr_color = self.color_preview.cget("bg")
            cd = ColorChooserDialog(initialcolor=curr_color, title=tr.translate("choose_chest_color"), parent=self)
            cd.show()
            if cd.result:
                r, g, b = cd.result.rgb
                self.color_var.set(f"{r},{g},{b}")

        btn = ttk.Button(color_input_frame, text="🎨", width=3, command=choose_color)
        btn.pack(side=tk.LEFT)
        if hasattr(parent, "add_tooltip"):
            parent.add_tooltip(btn, tr.translate("pick_color"))
        
        ttk.Label(main_frame, text=tr.translate("color_tip"), font=("", 8), foreground="gray").grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text=tr.translate("confirm"), command=self.on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text=tr.translate("cancel"), command=self.destroy).pack(side=tk.LEFT, padx=10)

    def on_ok(self):
        try:
            cap = int(self.cap_var.get())
            self.model.capacity = cap
            # 获取原始类型名
            display_val = self.type_var.get()
            self.model.specialChestType = self.rev_display_types.get(display_val, display_val)
            self.model.globalInventoryId = self.gid_var.get()
            
            rgb = self.color_var.get().split(",")
            if len(rgb) == 3:
                r, g, b = map(int, rgb)
                self.model.playerChoiceColor = {"R": r, "G": g, "B": b, "A": 255}
            
            self.result = True
            self.destroy()
        except ValueError:
            messagebox.showerror(tr.translate("error"), tr.translate("invalid_input_format"))

class ExperienceDialog(ttkb.Toplevel):
    def __init__(self, parent, exp_vars):
        super().__init__(parent)
        self.title(tr.translate("skill_experience"))
        center_window(self, 650, 350)
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=tr.translate("modify_exp_tip"), font=("", 10, "bold")).pack(pady=(0, 15))

        grid_frame = ttk.Frame(main_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True)

        labels = [
            tr.translate("farming_exp"), 
            tr.translate("mining_exp"), 
            tr.translate("foraging_exp"), 
            tr.translate("fishing_exp"), 
            tr.translate("combat_exp"), 
            tr.translate("luck_exp")
        ]
        
        # 经验等级对应表
        self.XP_LEVELS = [0, 100, 380, 770, 1300, 2150, 3300, 4800, 6900, 10000, 15000]

        for i, label in enumerate(labels):
            row, col = divmod(i, 2)
            f = ttk.LabelFrame(grid_frame, text=label, padding=10)
            f.grid(row=row, column=col, padx=10, pady=10, sticky=tk.NSEW)
            
            entry_var = exp_vars[i]
            entry = ttk.Entry(f, textvariable=entry_var, width=12)
            entry.pack(side=tk.LEFT, padx=5)
            
            # 由于 ExperienceDialog 继承自 Toplevel，而 add_tooltip 是 EditorUI 的方法
            # 我们直接通过传入的 parent (即 EditorUI 实例) 调用 add_tooltip
            if hasattr(parent, "add_tooltip"):
                parent.add_tooltip(entry, tr.translate("exp_max_tip"))
            
            level_label = ttk.Label(f, text=f"{tr.translate('level')}: 0", foreground="blue")
            level_label.pack(side=tk.LEFT, padx=5)
            
            # 绑定更新事件
            def update_level(event, var=entry_var, lbl=level_label):
                try:
                    xp_str = var.get() or "0"
                    xp = int(xp_str)
                    if xp > 15000:
                        xp = 15000
                        var.set("15000")
                    lvl = 0
                    for threshold in self.XP_LEVELS:
                        if xp >= threshold:
                            lvl = self.XP_LEVELS.index(threshold)
                    lbl.config(text=f"{tr.translate('level')}: {lvl}")
                except:
                    pass
            
            entry.bind("<KeyRelease>", update_level)
            # 初始化等级显示
            update_level(None)

        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, pady=10)
        ttk.Button(btn_frame, text=tr.translate("max_level_btn"), command=lambda: self.max_all(exp_vars)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=tr.translate("confirm"), command=self.destroy, width=15).pack(side=tk.LEFT, padx=5)

    def max_all(self, exp_vars):
        if messagebox.askyesno(tr.translate("confirm"), tr.translate("confirm_max_exp")):
            for var in exp_vars:
                var.set("15000")
            # 强制触发一次 UI 更新（简单起见，提示用户重新打开或手动改一下）
            messagebox.showinfo(tr.translate("tip"), tr.translate("max_exp_success_tip"))

class RecipeDialog(ttkb.Toplevel):
    def __init__(self, parent, player_model):
        super().__init__(parent)
        self.title(tr.translate("recipe_management"))
        center_window(self, 600, 800)
        self.player = player_model
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.cooking_tab = self._create_recipe_tab(self.player.cookingRecipes)
        self.crafting_tab = self._create_recipe_tab(self.player.craftingRecipes)
        
        self.notebook.add(self.cooking_tab, text=tr.translate("cooking_recipes"))
        self.notebook.add(self.crafting_tab, text=tr.translate("crafting_recipes"))
        
        btn_frame = ttk.Frame(main_frame, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btn_frame, text=tr.translate("close"), command=self.destroy).pack()

    def _create_recipe_tab(self, recipes_proxy):
        frame = ttk.Frame(self.notebook)
        
        search_var = tk.StringVar()
        search_entry = ttk.Entry(frame, textvariable=search_var)
        search_entry.pack(fill=tk.X, padx=5, pady=5)
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # 鼠标滚轮支持
        setup_mousewheel(canvas)
        
        recipe_status = recipes_proxy.get_recipes_status()
        recipe_vars = {}
        
        # 排序：已解锁的在前
        sorted_names = sorted(recipe_status.keys(), key=lambda n: (recipe_status[n] is None, n))
        
        items = []
        for name in sorted_names:
            row_f = ttk.Frame(scrollable_frame)
            row_f.pack(fill=tk.X, padx=5, pady=2)
            
            is_unlocked = recipe_status[name] is not None
            var = tk.BooleanVar(value=is_unlocked)
            recipe_vars[name] = var
            
            # 翻译食谱/制作名
            display_name = tr.translate(f"recipe_{name.lower().replace(' ', '_')}", name)
            cb = ttk.Checkbutton(row_f, text=display_name, variable=var, 
                                 command=lambda n=name, v=var, p=recipes_proxy: self._on_recipe_toggle(p, n, v))
            cb.pack(side=tk.LEFT)
            
            craft_count_text = f"({tr.translate('craft_count_prefix')}: {recipe_status[name] or 0})"
            count_label = ttk.Label(row_f, text=craft_count_text, foreground="gray")
            count_label.pack(side=tk.LEFT, padx=10)
            
            items.append((row_f, name))

        def on_search(*args):
            term = search_var.get().lower()
            for row_f, name in items:
                if term in name.lower():
                    row_f.pack(fill=tk.X, padx=5, pady=2)
                else:
                    row_f.pack_forget()
                    
        search_var.trace("w", on_search)
        return frame

    def _on_recipe_toggle(self, recipes_proxy, name, var):
        if var.get():
            recipes_proxy.set_recipe_status(name, 0)
        else:
            recipes_proxy.set_recipe_status(name, None)

class FriendshipDialog(ttkb.Toplevel):
    def __init__(self, parent, friendship_data):
        super().__init__(parent)
        self.title(tr.translate("friendship_management"))
        center_window(self, 400, 600)
        self.friendship_data = friendship_data
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 搜索框
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(search_frame, text=tr.translate('search_npc')).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.refresh_list)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 列表区域
        list_container = ttk.Frame(main_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(list_container)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # 同步宽度
        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        # 鼠标滚轮支持
        setup_mousewheel(canvas)

        self.refresh_list()
        
        btn_frame = ttk.Frame(main_frame, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btn_frame, text=tr.translate("close"), command=self.destroy).pack()

    def refresh_list(self, *args):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        search_term = self.search_var.get().lower()
        
        # 按照名字排序
        sorted_names = sorted(self.friendship_data.keys())
        
        for name in sorted_names:
            if search_term and search_term not in name.lower():
                continue
                
            data = self.friendship_data[name]
            f = ttk.Frame(self.scrollable_frame, padding=5)
            f.pack(fill=tk.X)
            
            # 翻译 NPC 名称
            display_name = tr.translate(f"npc_{name.lower().replace(' ', '_')}", name)
            ttk.Label(f, text=display_name, width=15).pack(side=tk.LEFT)
            ttk.Entry(f, textvariable=data["points"], width=8).pack(side=tk.LEFT, padx=5)
            
            # 计算心数 (250 points per heart)
            heart_label = ttk.Label(f, foreground="red")
            heart_label.pack(side=tk.LEFT, padx=5)
            
            def update_hearts(var, index, mode, label=heart_label, points_var=data["points"]):
                if not label.winfo_exists():
                    return
                try:
                    p = int(points_var.get())
                    h = p // 250
                    label.config(text=f"{tr.translate('hearts_prefix')}{h}")
                except:
                    label.config(text=f"{tr.translate('hearts_prefix')}0")
            
            # 初始更新
            update_hearts(None, None, None)
            
            # 清除旧的 trace 以防重复绑定（因为 refresh_list 会多次调用）
            if "trace_id" in data:
                try:
                    data["points"].trace_remove("write", data["trace_id"])
                except:
                    pass
            
            # 绑定更新事件并保存 ID
            data["trace_id"] = data["points"].trace_add("write", update_hearts)

class BundlesDialog(ttkb.Toplevel):
    """社区中心收集包管理对话框"""
    def __init__(self, parent, bundles_manager):
        super().__init__(parent)
        self.title(tr.translate('community_center_bundles'))
        center_window(self, 600, 700)
        self.bundles_manager = bundles_manager
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部操作
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(top_frame, text=tr.translate('complete_all_bundles'), command=self.complete_all).pack(side=tk.LEFT)
        ttk.Label(top_frame, text=f" ({tr.translate('save_hint')})", foreground="gray").pack(side=tk.LEFT)
        
        # 列表区域
        list_container = ttk.Frame(main_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(list_container)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # 鼠标滚轮支持
        setup_mousewheel(canvas)

        self.refresh_list()
        
        btn_frame = ttk.Frame(main_frame, padding=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btn_frame, text=tr.translate("close"), command=self.destroy).pack()

    def refresh_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        rooms = self.bundles_manager.get_bundles_by_room()
        
        for room_name, bundles in rooms.items():
            # 翻译房间名称
            display_room_name = tr.translate(f"room_{room_name.lower().replace(' ', '_')}", room_name)
            room_frame = ttk.LabelFrame(self.scrollable_frame, text=f"{tr.translate('room_prefix')}{display_room_name}", padding=5)
            room_frame.pack(fill=tk.X, pady=5, padx=5)
            
            for bundle in bundles:
                bundle_f = ttk.Frame(room_frame)
                bundle_f.pack(fill=tk.X, pady=2)
                
                status_text = tr.translate("completed") if bundle.completed else tr.translate("in_progress")
                status_color = "green" if bundle.completed else "orange"
                
                # 翻译 Bundle 名称
                display_bundle_name = tr.translate(f"bundle_{bundle.name.lower().replace(' ', '_')}", bundle.name)
                ttk.Label(bundle_f, text=display_bundle_name, width=25).pack(side=tk.LEFT)
                ttk.Label(bundle_f, text=status_text, foreground=status_color, width=10).pack(side=tk.LEFT)
                
                ttk.Button(bundle_f, text=tr.translate("fill_bundle"), command=lambda b=bundle: self.complete_bundle(b)).pack(side=tk.RIGHT)

    def complete_bundle(self, bundle):
        bundle.complete_all()
        self.refresh_list()
        messagebox.showinfo(tr.translate("success"), f"{tr.translate('bundle_filled_success_prefix')} '{bundle.name}' {tr.translate('bundle_filled_success_suffix')}")

    def complete_all(self):
        if messagebox.askyesno(tr.translate("confirm"), tr.translate("confirm_complete_all_bundles")):
            for bundle in self.bundles_manager.bundles:
                bundle.complete_all()
            self.refresh_list()
            messagebox.showinfo(tr.translate("success"), tr.translate("all_bundles_filled_success"))

class SpecialPowersDialog(ttkb.Toplevel):
    """特殊能力与成就管理对话框"""
    def __init__(self, parent, player_model):
        super().__init__(parent)
        self.title(tr.translate('special_powers_and_achievements'))
        center_window(self, 600, 800)
        self.player = player_model
        self.transient(parent)
        self.grab_set()
        
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 使用 Notebook 分开特殊能力和成就
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 1. 特殊能力页
        powers_tab = ttk.Frame(notebook, padding=10)
        notebook.add(powers_tab, text=tr.translate('special_powers'))
        
        powers_canvas = tk.Canvas(powers_tab)
        powers_scroll = ttk.Scrollbar(powers_tab, orient="vertical", command=powers_canvas.yview)
        self.powers_frame = ttk.Frame(powers_canvas)
        
        self.powers_frame.bind("<Configure>", lambda e: powers_canvas.configure(scrollregion=powers_canvas.bbox("all")))
        powers_canvas_window = powers_canvas.create_window((0, 0), window=self.powers_frame, anchor="nw")
        powers_canvas.bind('<Configure>', lambda e: powers_canvas.itemconfig(powers_canvas_window, width=e.width))
        powers_canvas.configure(yscrollcommand=powers_scroll.set)
        
        powers_scroll.pack(side="right", fill="y")
        powers_canvas.pack(side="left", fill="both", expand=True)
        setup_mousewheel(powers_canvas)
        
        # 2. 成就页
        ach_tab = ttk.Frame(notebook, padding=10)
        notebook.add(ach_tab, text=tr.translate('achievements'))
        
        ach_canvas = tk.Canvas(ach_tab)
        ach_scroll = ttk.Scrollbar(ach_tab, orient="vertical", command=ach_canvas.yview)
        self.ach_frame = ttk.Frame(ach_canvas)
        
        self.ach_frame.bind("<Configure>", lambda e: ach_canvas.configure(scrollregion=ach_canvas.bbox("all")))
        ach_canvas_window = ach_canvas.create_window((0, 0), window=self.ach_frame, anchor="nw")
        ach_canvas.bind('<Configure>', lambda e: ach_canvas.itemconfig(ach_canvas_window, width=e.width))
        ach_canvas.configure(yscrollcommand=ach_scroll.set)
        
        ach_scroll.pack(side="right", fill="y")
        ach_canvas.pack(side="left", fill="both", expand=True)
        setup_mousewheel(ach_canvas)
        
        # 填充内容
        self.refresh_powers()
        self.refresh_achievements()
        
        # 底部按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        ttk.Button(btn_frame, text=tr.translate("close"), command=self.destroy).pack()

    def refresh_powers(self):
        for widget in self.powers_frame.winfo_children():
            widget.destroy()
            
        for power in SPECIAL_POWERS:
            f = ttk.Frame(self.powers_frame, padding=5)
            f.pack(fill=tk.X)
            
            has_power = False
            if power["type"] == "mail":
                has_power = self.player.has_mail(power["id"])
            
            status_text = tr.translate("unlocked") if has_power else tr.translate("locked")
            status_color = "green" if has_power else "red"
            
            ttk.Label(f, text=tr.translate(power["name_key"]), width=25, font=("", 10, "bold")).pack(side=tk.LEFT)
            ttk.Label(f, text=status_text, foreground=status_color, width=10).pack(side=tk.LEFT)
            
            def toggle_power(p=power, current=has_power):
                if p["type"] == "mail":
                    if current:
                        self.player.remove_mail(p["id"])
                    else:
                        self.player.add_mail(p["id"])
                self.refresh_powers()
            
            btn_text = tr.translate("remove") if has_power else tr.translate("add")
            ttk.Button(f, text=btn_text, command=toggle_power).pack(side=tk.RIGHT)
            
            desc = tr.translate(power["desc_key"])
            ttk.Label(self.powers_frame, text=desc, foreground="gray", font=("", 8)).pack(fill=tk.X, padx=(10, 0), pady=(0, 5))

    def refresh_achievements(self):
        for widget in self.ach_frame.winfo_children():
            widget.destroy()
            
        for ach in ACHIEVEMENTS:
            f = ttk.Frame(self.ach_frame, padding=5)
            f.pack(fill=tk.X)
            
            has_ach = self.player.has_achievement(ach["id"])
            status_text = tr.translate("unlocked") if has_ach else tr.translate("locked")
            status_color = "green" if has_ach else "red"
            
            ttk.Label(f, text=tr.translate(ach["name_key"]), width=25, font=("", 10, "bold")).pack(side=tk.LEFT)
            ttk.Label(f, text=status_text, foreground=status_color, width=10).pack(side=tk.LEFT)
            
            def toggle_ach(aid=ach["id"], current=has_ach):
                if current:
                    self.player.remove_achievement(aid)
                else:
                    self.player.add_achievement(aid)
                self.refresh_achievements()
            
            btn_text = tr.translate("remove") if has_ach else tr.translate("locked_btn") # 虽然是解锁，但逻辑是一样的
            if not has_ach:
                btn_text = tr.translate("unlock")
                
            ttk.Button(f, text=btn_text, command=toggle_ach).pack(side=tk.RIGHT)
            
            desc = tr.translate(ach["desc_key"])
            ttk.Label(self.ach_frame, text=desc, foreground="gray", font=("", 8)).pack(fill=tk.X, padx=(10, 0), pady=(0, 5))

class StardewEditor:
    def get_default_save_path(self):
        """ 获取系统默认的星露谷存档路径 (Windows) """
        return os.path.expandvars(r"%AppData%\StardewValley\Saves")

    def __init__(self, root):
        self.root = root
        self.root.title(f"{tr.translate('app_title')} --manafeng")
        center_window(self.root, 1000, 750)
        self.root.resizable(False, False) # 固定窗口大小

        # 设置图标
        try:
            icon_path = self.resource_path("F.png")
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, img)
        except Exception:
            pass
        
        self.save_dir = "" # 当前选中的具体存档目录
        self.parent_save_dir = "" # 存档根目录 (如 Saves)
        self.available_saves = [] # 可用的存档列表
        self.save_file = ""
        self.info_file = "SaveGameInfo"
        
        # 数据存储
        self.player_fields = {
            "name": tk.StringVar(),
            "farmName": tk.StringVar(),
            "money": tk.StringVar(),
            "totalMoneyEarned": tk.StringVar(),
            "qiGems": tk.StringVar(),
            "masteryExp": tk.StringVar(),
            "health": tk.StringVar(),
            "maxHealth": tk.StringVar(),
            "stamina": tk.StringVar(),
            "maxStamina": tk.StringVar(),
            "clubCoins": tk.StringVar(),
            "spouse": tk.StringVar(),
            "gender": tk.StringVar(),
            "deepestMineLevel": tk.StringVar(),
            "trashCanLevel": tk.StringVar(),
            "luckLevel": tk.StringVar(),
            "houseUpgradeLevel": tk.StringVar(),
            "magneticRadius": tk.StringVar(),
            "resilience": tk.StringVar(),
            "immunity": tk.StringVar(),
            "farmingLevel": tk.StringVar(),
            "miningLevel": tk.StringVar(),
            "foragingLevel": tk.StringVar(),
            "fishingLevel": tk.StringVar(),
            "combatLevel": tk.StringVar(),
            "favoriteThing": tk.StringVar(),
            "catPerson": tk.StringVar(),
            "maxItems": tk.StringVar(),
            "attack": tk.StringVar(),
            "hair": tk.StringVar(),
            "hairstyle": tk.StringVar(),
            "accessory": tk.StringVar(),
            "shirt": tk.StringVar(),
            "skin": tk.StringVar(),
            "hairColor": tk.StringVar(), # 格式 "R,G,B"
            "eyeColor": tk.StringVar(),  # 格式 "R,G,B"
            "hat": tk.StringVar(),
            "shirtItem": tk.StringVar(),
            "pantsItem": tk.StringVar(),
            "boots": tk.StringVar(),
            "leftRing": tk.StringVar(),
            "rightRing": tk.StringVar(),
            "trinketItem": tk.StringVar()
        }
        self.all_players = [] 
        self.current_player_idx = 0
        self.exp_data = [0, 0, 0, 0, 0, 0]
        self.exp_vars = [tk.StringVar() for _ in range(6)]
        self.professions_list = []
        self.friendship_data = {}
        self.friendship_vars = {}
        self.game_fields = {
            "dailyLuck": tk.StringVar(),
            "goldenWalnuts": tk.StringVar(),
            "stats/stepsTaken": tk.StringVar(),
            "year": tk.StringVar(),
            "currentSeason": tk.StringVar(),
            "dayOfMonth": tk.StringVar(),
            "caveChoice": tk.StringVar(),
            "canCheat": tk.BooleanVar()
        }
        
        self.weather_vars = {
            "isRaining": tk.BooleanVar(),
            "isLightning": tk.BooleanVar(),
            "isSnowing": tk.BooleanVar(),
            "isDebrisWeather": tk.BooleanVar(),
            "isGreenRain": tk.BooleanVar()
        }
        self.pets_data = []
        self.animals_data = []
        self.inventory_items = []
        self.inventory_max = 36
        self.chests_data = []
        
        # 初始化存档路径
        default_path = self.get_default_save_path()
        if os.path.exists(default_path):
            self.parent_save_dir = default_path
        else:
            self.parent_save_dir = os.getcwd()

        self.setup_ui()
        self.setup_realtime_limits()
        self.refresh_save_list()

    def init_item_maps(self):
        """ 初始化物品名称映射和装备选项 (支持多语言切换) """
        self.item_name_map = {}
        self.item_name_map_by_prefix = {}

        for cat, items in ITEM_CATEGORIES.items():
            for key, data in items.items():
                # 尝试翻译 key
                display_name = tr.translate(key)
                # 如果没有翻译（返回原 key），则不建立映射，或者使用 data 中的 name
                if display_name == key:
                    display_name = data.get("name", key)

                # 记录 英文名 -> 显示名 和 ID -> 显示名
                self.item_name_map[data["name"]] = display_name
                item_id = data["id"]
                self.item_name_map[item_id] = display_name
                
                # 记录 前缀 -> ID -> 显示名
                if "(" in item_id and ")" in item_id:
                    prefix = item_id[item_id.find("(")+1 : item_id.find(")")]
                    clean_id = item_id[item_id.find(")")+1:]
                else:
                    # 如果没有前缀，尝试根据分类推断，默认为 (O)
                    clean_id = item_id
                    if cat == "rings": prefix = "O"
                    elif cat == "trinkets": prefix = "TR"
                    elif cat == "hats": prefix = "H"
                    elif cat == "shoes": prefix = "B"
                    else: prefix = "O"
                    
                    # 同时记录带推断前缀的 ID 到显示名映射
                    prefixed_id = f"({prefix}){item_id}"
                    self.item_name_map[prefixed_id] = display_name

                if prefix not in self.item_name_map_by_prefix:
                    self.item_name_map_by_prefix[prefix] = {}
                self.item_name_map_by_prefix[prefix][clean_id] = display_name

        # 装备位映射与其对应的分类
        self.equipment_map = {
            "leftRing": "rings",
            "rightRing": "rings",
            "trinketItem": "trinkets",
            "boots": "shoes",
            "hat": "hats",
            "shirtItem": "clothes",
            "pantsItem": "clothes"
        }
        
        # 预先生成每个装备位对应的下拉列表选项
        self.category_options = {}
        for attr, cat_key in self.equipment_map.items():
            options = [tr.translate("none")]
            items = ITEM_CATEGORIES.get(cat_key, {})
            for key, data in items.items():
                item_id = data["id"]
                
                # 针对不同装备位，自动推断并补齐前缀 (针对 1.6 格式)
                if "(" not in item_id:
                    if cat_key == "rings": item_id = f"(O){item_id}"
                    elif cat_key == "trinkets": item_id = f"(TR){item_id}"
                    elif cat_key == "hats": item_id = f"(H){item_id}"
                    elif cat_key == "shoes": item_id = f"(B){item_id}"
                    elif cat_key == "clothes":
                        if attr == "shirtItem": item_id = f"(S){item_id}"
                        elif attr == "pantsItem": item_id = f"(P){item_id}"

                # 衣服和裤子的过滤
                if attr == "shirtItem" and not item_id.startswith("(S)"):
                    continue
                if attr == "pantsItem" and not item_id.startswith("(P)"):
                    continue
                
                if attr == "hat" and not item_id.startswith("(H)"):
                    continue
                if attr == "boots" and not item_id.startswith("(B)"):
                    continue
                if attr == "trinketItem" and not item_id.startswith("(TR)"):
                    continue
                if attr in ["leftRing", "rightRing"]:
                    if "(" in item_id and not item_id.startswith("(O)"):
                        continue
                
                display_name = self.item_name_map.get(item_id, tr.translate(key))
                options.append(f"({item_id}) {display_name}")
            self.category_options[attr] = options

    def setup_realtime_limits(self):
        """ 为房屋等级和金钱设置实时输入检测和上限限制 """
        def cap_money(*args):
            val = self.player_fields["money"].get()
            if not val: return
            try:
                # 移除非数字字符
                clean_val = "".join(filter(str.isdigit, val))
                if not clean_val:
                    if val != "":
                        self.player_fields["money"].set("")
                    return
                
                num = int(clean_val)
                if num > 99999999:
                    self.player_fields["money"].set("99999999")
                elif clean_val != val:
                    self.player_fields["money"].set(clean_val)
            except ValueError:
                pass

        def cap_house(*args):
            val = self.player_fields["houseUpgradeLevel"].get()
            if not val: return
            try:
                clean_val = "".join(filter(str.isdigit, val))
                if not clean_val:
                    if val != "":
                        self.player_fields["houseUpgradeLevel"].set("")
                    return
                
                num = int(clean_val)
                if num > 3: # 1.6 房屋等级可以到 3
                    self.player_fields["houseUpgradeLevel"].set("3")
                elif clean_val != val:
                    self.player_fields["houseUpgradeLevel"].set(clean_val)
            except ValueError:
                pass

        def cap_mine_level(*args):
            val = self.player_fields["deepestMineLevel"].get()
            if not val: return
            try:
                clean_val = "".join(filter(str.isdigit, val))
                if not clean_val:
                    if val != "":
                        self.player_fields["deepestMineLevel"].set("")
                    return
                
                num = int(clean_val)
                if num > 120:
                    self.player_fields["deepestMineLevel"].set("120")
                elif clean_val != val:
                    self.player_fields["deepestMineLevel"].set(clean_val)
            except ValueError:
                pass

        self.player_fields["money"].trace_add("write", cap_money)
        self.player_fields["houseUpgradeLevel"].trace_add("write", cap_house)
        self.player_fields["deepestMineLevel"].trace_add("write", cap_mine_level)

    def refresh_save_list(self):
        """ 刷新存档列表并尝试加载第一个 """
        self.available_saves = list_save_folders(self.parent_save_dir)
        if hasattr(self, 'save_selector'):
            save_names = [s["name"] for s in self.available_saves]
            self.save_selector["values"] = save_names
            if save_names:
                self.save_selector.current(0)
                self.on_save_selected()
            else:
                self.status_var.set(f"{tr.translate('no_save_found_prefix')} {os.path.basename(self.parent_save_dir)} {tr.translate('no_save_found_suffix')}")

    def on_save_selected(self, event=None):
        """ 当用户在下拉框选择了一个不同的存档文件夹时 """
        idx = self.save_selector.current()
        if idx >= 0:
            self.save_dir = self.available_saves[idx]["path"]
            self.load_save_data()

    def resource_path(self, relative_path):
        """ 获取资源的绝对路径，兼容开发环境和 PyInstaller 打包环境 """
        try:
            # PyInstaller 打包后的临时目录
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        except Exception:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        return os.path.join(base_path, relative_path)

    def select_save_dir(self):
        """ 让用户手动选择存档根目录 (Saves 文件夹) """
        new_dir = filedialog.askdirectory(initialdir=self.parent_save_dir, title=tr.translate("select_saves_dir"))
        if new_dir:
            self.parent_save_dir = new_dir
            self.refresh_save_list()

    def setup_ui(self):
        self.init_item_maps()
        # 这里的 UI 设置代码较长，为了保持逻辑清晰，将其主要结构保留
        # 使用 ttkbootstrap 的样式，不需要手动配置繁琐的 Style
        
        # 顶部工具栏
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttkb.Button(toolbar, text=tr.translate('select_saves_dir_btn'), command=self.select_save_dir, bootstyle=PRIMARY).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(toolbar, text=f"{tr.translate('select_save')}:").pack(side=tk.LEFT, padx=(10, 2))
        self.save_selector = ttk.Combobox(toolbar, state="readonly", width=40)
        self.save_selector.pack(side=tk.LEFT, padx=5)
        self.save_selector.bind("<<ComboboxSelected>>", self.on_save_selected)

        ttkb.Button(toolbar, text=tr.translate('refresh'), command=self.refresh_save_list, bootstyle=SECONDARY).pack(side=tk.LEFT, padx=5)

        # 语言切换
        ttk.Label(toolbar, text=f"{tr.translate('language')}:").pack(side=tk.LEFT, padx=(10, 2))
        self.lang_var = tk.StringVar(value="中文" if tr.current_lang == "zh" else "English")
        self.lang_selector = ttk.Combobox(toolbar, textvariable=self.lang_var, values=["中文", "English"], state="readonly", width=8)
        self.lang_selector.pack(side=tk.LEFT, padx=5)
        self.lang_selector.bind("<<ComboboxSelected>>", self.change_language)

        self.status_var = tk.StringVar(value=tr.translate("detecting_saves"))
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        main_notebook = ttk.Notebook(self.root)
        main_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 1. 环境与宠物页 (移到第一位)
        world_tab = ttk.Frame(main_notebook)
        main_notebook.add(world_tab, text=tr.translate('world_tab'))

        # 使世界页可滚动
        world_container = ttk.Frame(world_tab)
        world_container.pack(fill=tk.BOTH, expand=True)
        
        world_canvas = tk.Canvas(world_container, highlightthickness=0)
        world_scrollbar = ttk.Scrollbar(world_container, orient="vertical", command=world_canvas.yview)
        scrollable_world = ttk.Frame(world_canvas)
        
        scrollable_world.bind(
            "<Configure>",
            lambda e: world_canvas.configure(scrollregion=world_canvas.bbox("all"))
        )
        
        # 绑定宽度同步
        world_canvas_window = world_canvas.create_window((0, 0), window=scrollable_world, anchor="nw")
        world_canvas.bind('<Configure>', lambda e: world_canvas.itemconfig(world_canvas_window, width=e.width))
        
        world_canvas.configure(yscrollcommand=world_scrollbar.set)
        world_scrollbar.pack(side="right", fill="y")
        world_canvas.pack(side="left", fill="both", expand=True)
        
        setup_mousewheel(world_canvas)

        # 时间与基础环境设置
        env_frame = ttk.LabelFrame(scrollable_world, text=tr.translate("env_time_settings"), padding=10)
        env_frame.pack(fill=tk.X, padx=10, pady=5)

        time_fields = [
            (f"{tr.translate('current_year')}:", "year"), (f"{tr.translate('current_day')}:", "dayOfMonth"),
            (f"{tr.translate('current_season')}:", "currentSeason"), (f"{tr.translate('daily_luck')}:", "dailyLuck"),
            (f"{tr.translate('total_steps')}:", "stats/stepsTaken")
        ]
        
        for i, (label, attr) in enumerate(time_fields):
            row, col = divmod(i, 2)
            ttk.Label(env_frame, text=label).grid(row=row, column=col*2, sticky=tk.W, pady=2)
            if attr == "currentSeason":
                # 季节使用下拉框
                cb = ttk.Combobox(env_frame, textvariable=self.game_fields[attr], 
                                 values=["spring", "summer", "fall", "winter"], state="readonly", width=12)
                cb.grid(row=row, column=col*2+1, sticky=tk.W, padx=5, pady=2)
            else:
                ttk.Entry(env_frame, textvariable=self.game_fields[attr], width=15).grid(row=row, column=col*2+1, sticky=tk.W, padx=5, pady=2)

        # 天气与功能设置
        weather_frame = ttk.LabelFrame(scrollable_world, text=tr.translate("weather_settings"), padding=10)
        weather_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Checkbutton(weather_frame, text=tr.translate("is_raining"), variable=self.weather_vars["isRaining"]).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(weather_frame, text=tr.translate("is_lightning"), variable=self.weather_vars["isLightning"]).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(weather_frame, text=tr.translate("is_snowing"), variable=self.weather_vars["isSnowing"]).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(weather_frame, text=tr.translate("is_debris"), variable=self.weather_vars["isDebrisWeather"]).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(weather_frame, text=tr.translate("is_green_rain"), variable=self.weather_vars["isGreenRain"]).pack(side=tk.LEFT, padx=10)
        
        cheat_cb = ttk.Checkbutton(weather_frame, text=tr.translate("can_cheat"), variable=self.game_fields["canCheat"])
        cheat_cb.pack(side=tk.LEFT, padx=10)
        self.add_tooltip(cheat_cb, tr.translate("can_cheat_tip"))

        # 社区中心管理
        bundles_frame = ttk.LabelFrame(scrollable_world, text=tr.translate('community_center'), padding=10)
        bundles_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(bundles_frame, text=tr.translate('manage_bundles'), command=self.show_bundles_window).pack(side=tk.LEFT, padx=5)

        # 宠物列表 (调整到社区中心下面)
        self.pets_frame = ttk.LabelFrame(scrollable_world, text=tr.translate("pets_list"), padding=10)
        self.pets_frame.pack(fill=tk.X, padx=10, pady=5)

        # 农场动物列表
        self.animals_frame = ttk.LabelFrame(scrollable_world, text=tr.translate("animals_list"), padding=10)
        self.animals_frame.pack(fill=tk.X, padx=10, pady=5)

        # 2. 角色属性页
        player_tab = ttk.Frame(main_notebook)
        main_notebook.add(player_tab, text=tr.translate('player_tab'))
        
        # 玩家选择器
        selector_frame = ttk.Frame(player_tab, padding=10)
        selector_frame.pack(fill=tk.X)
        ttk.Label(selector_frame, text=f"{tr.translate('current_editing_player')}:").pack(side=tk.LEFT)
        self.player_selector = ttk.Combobox(selector_frame, state="readonly", width=30)
        self.player_selector.pack(side=tk.LEFT, padx=5)
        self.player_selector.bind("<<ComboboxSelected>>", self.on_player_selected)

        # 基础属性 - 使用可滚动区域
        scroll_container = ttk.Frame(player_tab)
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas = tk.Canvas(scroll_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        def _update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # 自动调整窗口宽度以适应内容
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        scrollable_frame.bind("<Configure>", _update_scrollregion)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # 鼠标滚轮支持
        setup_mousewheel(canvas)

        # 定义分类布局
        categories = [
            (tr.translate('basic_info'), [
                (tr.translate("player_name"), "name", "entry"), 
                (tr.translate("gender"), "gender", "combo_gender"), 
                (tr.translate("spouse"), "spouse", "entry"),
                (tr.translate("farm_name"), "farmName", "entry"), 
                (tr.translate("pet_type"), "catPerson", "combo_pet"), 
                (tr.translate("favorite_thing"), "favoriteThing", "entry"),
                (tr.translate("house_level"), "houseUpgradeLevel", "entry"), 
                (tr.translate("cave_choice"), "caveChoice", "combo_cave"),
            ]),
            (tr.translate('assets_progress'), [
                (tr.translate("current_money"), "money", "entry"), 
                (tr.translate("total_money"), "totalMoneyEarned", "entry"),
                (tr.translate("qi_gems"), "qiGems", "entry"),
                (tr.translate("mine_depth"), "deepestMineLevel", "entry"), 
                (tr.translate("golden_walnuts"), "goldenWalnuts", "game_entry"),
            ]),
            (tr.translate('stats_abilities'), [
                (tr.translate("stamina"), "stamina", "entry"), 
                (tr.translate("max_stamina"), "maxStamina", "entry"), 
                (tr.translate("health"), "health", "entry"), 
                (tr.translate("max_health"), "maxHealth", "entry"),
                (tr.translate("inventory_size"), "maxItems", "entry"),
                (tr.translate("profession_exp"), "btn_professions", "button"), 
                (tr.translate("skills_points"), "btn_skills", "button"),
                (tr.translate("friendship_management"), "btn_friendship", "button"),
                (tr.translate("recipe_management"), "btn_recipes", "button"),
                (tr.translate("special_powers_and_achievements"), "btn_special_powers", "button"),
            ]),
            (tr.translate('skill_levels'), [
                (tr.translate("farming_level"), "farmingLevel", "entry"), 
                (tr.translate("fishing_level"), "fishingLevel", "entry"), 
                (tr.translate("foraging_level"), "foragingLevel", "entry"),
                (tr.translate("mining_level"), "miningLevel", "entry"), 
                (tr.translate("combat_level"), "combatLevel", "entry"), 
                (tr.translate("luck_level"), "luckLevel", "entry"),
                (tr.translate("mastery_exp"), "masteryExp", "entry"),
            ]),
            (tr.translate('appearance_custom'), [
                (tr.translate("hairstyle"), "hairstyle", "entry"), 
                (tr.translate("accessory"), "accessory", "entry"),
                (tr.translate("skin"), "skin", "entry"), 
                (tr.translate("hair_color"), "hairColor", "color"),
                (tr.translate("eye_color"), "eyeColor", "color"),
                (tr.translate("shirt_id"), "shirt", "entry"),
            ]),
            (tr.translate('equipment_slots'), [
                (tr.translate("hat"), "hat", "entry"),
                (tr.translate("shirt_item"), "shirtItem", "entry"),
                (tr.translate("pants_item"), "pantsItem", "entry"),
                (tr.translate("boots"), "boots", "entry"),
                (tr.translate("left_ring"), "leftRing", "entry"),
                (tr.translate("right_ring"), "rightRing", "entry"),
                (tr.translate("trinket_item"), "trinketItem", "entry"),
            ])
        ]

        # 动态创建分类容器
        for cat_name, fields in categories:
            cat_frame = ttk.LabelFrame(scrollable_frame, text=cat_name, padding=10)
            cat_frame.pack(fill=tk.X, padx=10, pady=5)
            
            for i, (label, attr, item_type) in enumerate(fields):
                row, col = divmod(i, 3)
                
                # 标签
                if label:
                    ttk.Label(cat_frame, text=label).grid(row=row, column=col*2, sticky=tk.W, pady=5, padx=(10, 5))
                
                # 输入控件
                if item_type == "entry":
                    if attr in self.equipment_map:
                        # 装备位使用下拉选择框
                        cat_key = self.equipment_map[attr]
                        cb = ttk.Combobox(cat_frame, textvariable=self.player_fields[attr], 
                                          values=self.category_options.get(attr, []), width=20)
                        cb.grid(row=row, column=col*2+1, sticky=tk.W, pady=5)
                        cb.bind("<Double-1>", lambda e, a=attr: self.select_equipment_item(a))
                        self.add_tooltip(cb, tr.translate("double_click_to_select"))
                    else:
                        entry = ttk.Entry(cat_frame, textvariable=self.player_fields[attr], width=15)
                        entry.grid(row=row, column=col*2+1, sticky=tk.W, pady=5)
                        if attr == "houseUpgradeLevel":
                            self.add_tooltip(entry, tr.translate("house_level_limit_hint"))
                        elif attr == "money":
                            self.add_tooltip(entry, tr.translate("money_limit_hint"))
                elif item_type == "combo_gender":
                    cb = ttk.Combobox(cat_frame, textvariable=self.player_fields[attr], values=[tr.translate("male"), tr.translate("female")], state="readonly", width=12)
                    cb.grid(row=row, column=col*2+1, sticky=tk.W, pady=5)
                elif item_type == "combo_pet":
                    cb = ttk.Combobox(cat_frame, textvariable=self.player_fields[attr], values=[tr.translate("dog"), tr.translate("cat"), tr.translate("turtle")], state="readonly", width=12)
                    cb.grid(row=row, column=col*2+1, sticky=tk.W, pady=5)
                elif item_type == "combo_cave":
                    cb = ttk.Combobox(cat_frame, textvariable=self.game_fields["caveChoice"], values=[tr.translate("none"), tr.translate("bat_cave"), tr.translate("mushroom_cave")], state="readonly", width=12)
                    cb.grid(row=row, column=col*2+1, sticky=tk.W, pady=5)
                elif item_type == "game_entry":
                    entry = ttk.Entry(cat_frame, textvariable=self.game_fields[attr], width=15)
                    entry.grid(row=row, column=col*2+1, sticky=tk.W, pady=5)
                elif item_type == "color":
                    # 创建一个预览框和按钮
                    color_frame = ttk.Frame(cat_frame)
                    color_frame.grid(row=row, column=col*2+1, sticky=tk.W, pady=5)
                    
                    # 预览颜色的小方块
                    preview = tk.Canvas(color_frame, width=20, height=20, bd=1, relief="solid", highlightthickness=0)
                    preview.pack(side=tk.LEFT, padx=(0, 5))
                    
                    if not hasattr(self, "color_previews"):
                        self.color_previews = {}
                    self.color_previews[attr] = preview
                    
                    btn = ttk.Button(color_frame, text=tr.translate("choose_color"), width=10, 
                                     command=lambda a=attr, p=preview: self.choose_color(a, p))
                    btn.pack(side=tk.LEFT)
                elif item_type == "button":
                    btn_text = label
                    cmd = lambda: None # 默认空函数
                    if attr == "btn_professions":
                        cmd = self.show_experience_window
                    elif attr == "btn_skills":
                        cmd = self.show_professions_window
                    elif attr == "btn_friendship":
                        cmd = self.show_friendship_window
                    elif attr == "btn_recipes":
                        cmd = self.show_recipes_window
                    elif attr == "btn_special_powers":
                        cmd = self.show_special_powers_window
                    
                    ttk.Button(cat_frame, text=btn_text, command=cmd, width=15).grid(row=row, column=col*2+1, sticky=tk.W, pady=5)

        # 3. 物品编辑页
        items_tab = ttk.Frame(main_notebook)
        main_notebook.add(items_tab, text=tr.translate("items_chests_tab"))

        tree_frame = ttk.Frame(items_tab, padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.items_tree = ttk.Treeview(tree_frame, columns=("name", "stack", "quality"), show="tree headings")
        self.items_tree.heading("#0", text=tr.translate("location_item"))
        self.items_tree.heading("name", text=tr.translate("item_name"))
        self.items_tree.heading("stack", text=tr.translate("quantity"))
        self.items_tree.heading("quality", text=tr.translate("quality"))
        self.items_tree.column("#0", width=250)
        self.items_tree.column("stack", width=80)
        self.items_tree.column("quality", width=80)
        
        # 水平滚动条
        tree_h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.items_tree.xview)
        tree_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 垂直滚动条
        tree_v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        tree_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.items_tree.configure(yscrollcommand=tree_v_scroll.set, xscrollcommand=tree_h_scroll.set)
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        setup_mousewheel(self.items_tree)
        
        # 绑定双击修改
        self.items_tree.bind("<Double-1>", lambda e: self.edit_selected_item())
        
        item_btn_frame = ttk.Frame(items_tab, padding=5)
        item_btn_frame.pack(fill=tk.X)
        ttk.Button(item_btn_frame, text=tr.translate("edit_selected"), command=self.edit_selected_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(item_btn_frame, text=tr.translate("add_new"), command=self.add_new_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(item_btn_frame, text=tr.translate("delete_selected"), command=self.delete_selected_item).pack(side=tk.LEFT, padx=5)

        # 底部保存按钮
        save_btn = ttk.Button(self.root, text=tr.translate("save_all"), command=self.save_data, style="Header.TButton")
        save_btn.pack(pady=10)

    def load_save_data(self):
        save_file, info_file = find_save_files(self.save_dir)
        if not save_file:
            self.status_var.set(tr.translate('no_valid_save_found').format(os.path.basename(self.save_dir) or self.save_dir))
            return
        
        self.status_var.set(tr.translate('loading_from').format(name=os.path.basename(self.save_dir)))
        self.root.update_idletasks()

        try:
            # 使用 SaveProxy 加载
            self.save_proxy = SaveProxy(save_file, info_file)
            self.save_file = save_file
            self.info_file = os.path.basename(info_file) if info_file else "SaveGameInfo"
            root = self.save_proxy.root
            
            # 加载全局数据和天气
            # 这些现在会在 load_player_data 中通过 save_proxy 加载
            self.weather_vars["isRaining"].set(bool(self.save_proxy.isRaining))
            self.weather_vars["isDebrisWeather"].set(bool(self.save_proxy.isDebrisWeather))
            self.weather_vars["isLightning"].set(bool(self.save_proxy.isLightning))
            self.weather_vars["isSnowing"].set(bool(self.save_proxy.isSnowing))
            self.weather_vars["isGreenRain"].set(bool(self.save_proxy.isGreenRain))

            # 加载所有玩家
            self.all_players = []
            if self.save_proxy.player:
                p = self.save_proxy.player
                self.all_players.append({"type": tr.translate("host"), "name": p.name, "model": p})
            
            for hand in self.save_proxy.farmhands:
                self.all_players.append({"type": tr.translate("farmhand"), "name": hand.name, "model": hand})
            
            # 加载宠物和箱子
            self.pets_data = []
            for pet_info in self.save_proxy.get_all_pets():
                pet = pet_info["model"]
                self.pets_data.append({
                    'name': tk.StringVar(value=pet.name),
                    'type': tk.StringVar(value=pet.petType),
                    'breed': tk.StringVar(value=str(pet.whichBreed)),
                    'friendship': tk.StringVar(value=str(pet.friendshipTowardFarmer)),
                    'timesPet': tk.StringVar(value=str(pet.timesPet)),
                    'isSleepingOnFarmerBed': tk.BooleanVar(value=pet.isSleepingOnFarmerBed),
                    'grantedFriendshipForPet': tk.BooleanVar(value=pet.grantedFriendshipForPet),
                    'model': pet,
                    'location': pet_info["location"]
                })
            
            self.chests_data = []
            for chest_info in self.save_proxy.get_all_chests():
                chest = chest_info["model"]
                chest_items = []
                for item in chest.items:
                    if item.is_empty: continue
                    
                    raw_name = item.name or tr.translate("unknown")
                    item_id = item.itemId or ""
                    
                    # 尝试映射中文名
                    display_name = raw_name
                    if item_id and item_id in self.item_name_map:
                        display_name = self.item_name_map[item_id]
                    elif raw_name in self.item_name_map:
                        display_name = self.item_name_map[raw_name]
                        
                    chest_items.append({
                        'display_name': display_name,
                        'name': raw_name,
                        'stack': tk.StringVar(value=str(item.stack)),
                        'quality': tk.StringVar(value=str(item.quality)),
                        'model': item
                    })
                
                self.chests_data.append({
                    'location': chest_info["location"],
                    'capacity': str(chest.capacity),
                    'items': chest_items,
                    'model': chest
                })
            
            # 加载农 farm 动物
            self.animals_data = []
            for animal_info in self.save_proxy.get_all_animals():
                animal = animal_info["model"]
                self.animals_data.append({
                    'name': tk.StringVar(value=animal.name),
                    'type': tk.StringVar(value=animal.type),
                    'gender': tk.StringVar(value=animal.gender),
                    'age': tk.StringVar(value=str(animal.age)),
                    'friendship': tk.StringVar(value=str(animal.friendship)),
                    'fullness': tk.StringVar(value=str(animal.fullness)),
                    'happiness': tk.StringVar(value=str(animal.happiness)),
                    'allowReproduction': tk.BooleanVar(value=animal.allowReproduction),
                    'hasEatenAnimalCracker': tk.BooleanVar(value=animal.hasEatenAnimalCracker),
                    'wasPet': tk.BooleanVar(value=animal.wasPet),
                    'isEating': tk.BooleanVar(value=animal.isEating),
                    'wasAutoPet': tk.BooleanVar(value=animal.wasAutoPet),
                    'buildingTypeILiveIn': tk.StringVar(value=animal.buildingTypeILiveIn),
                    'model': animal,
                    'location': animal_info["location"]
                })
            
            if self.all_players:
                self.player_selector["values"] = [f"[{p['type']}] {p['name']}" for p in self.all_players]
                self.player_selector.current(0)
                self.load_player_data(0)

            self.refresh_pets_list()
            self.refresh_animals_list() # 新增动物列表刷新
            self.refresh_items_list()
            self.status_var.set(tr.translate('save_loaded').format(name=os.path.basename(self.save_file)))
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"解析错误详情:\n{error_details}")
            messagebox.showerror(tr.translate("load_failed"), tr.translate("parse_save_failed").format(error=e))

    def load_player_data(self, idx):
        if idx < 0 or idx >= len(self.all_players): return
        player_info = self.all_players[idx]
        player = player_info["model"]
        
        for attr, var in self.player_fields.items():
            if attr == "spouse":
                if player_info["type"] == "Host":
                    var.set(self.save_proxy.spouse or "None")
                else:
                    var.set("None")
                continue
            
            # 使用模型属性访问
            if hasattr(player, attr):
                val = getattr(player, attr)
                if attr == "gender":
                    var.set(tr.translate("male") if val == "0" else tr.translate("female"))
                # 特殊处理宠物类型
                elif attr == "catPerson":
                    mapping = {"Cat": tr.translate("cat"), "Dog": tr.translate("dog"), "Turtle": tr.translate("turtle")}
                    var.set(mapping.get(player.petType, tr.translate("cat")))
                elif attr in ["hairColor", "eyeColor"]:
                    r, g, b, a = getattr(player, attr)
                    var.set(f"{r},{g},{b}")
                    # 更新预览颜色
                    if hasattr(self, "color_previews") and attr in self.color_previews:
                        hex_color = f'#{r:02x}{g:02x}{b:02x}'
                        self.color_previews[attr].config(bg=hex_color)
                elif isinstance(val, Item):
                    # 如果是 Item 对象（装备位）
                    item_id = val.itemId or "None"
                    if attr in self.equipment_map:
                        if item_id == "None":
                            var.set(tr.translate("none"))
                        else:
                            # 尝试获取翻译后的名称并设置为 (ID) Name 格式
                            display_name = self.item_name_map.get(item_id)
                            if not display_name:
                                # 尝试使用带前缀的 ID 获取中文名
                                prefixed_id = val.prefixedId
                                if prefixed_id and prefixed_id in self.item_name_map:
                                    display_name = self.item_name_map[prefixed_id]
                                    item_id = prefixed_id # 更新 ID 为带前缀的 ID
                            
                            if not display_name:
                                # 如果没有带前缀的 ID 匹配，尝试使用 clean ID 和对应的分类前缀
                                clean_id = item_id
                                if "(" in clean_id and ")" in clean_id:
                                    clean_id = clean_id[clean_id.find(")")+1:]
                                    
                                prefix_map = {
                                    "hat": "H",
                                    "shirtItem": "S",
                                    "pantsItem": "P",
                                    "boots": "B",
                                    "leftRing": "O",
                                    "rightRing": "O",
                                    "trinketItem": "TR"
                                }
                                prefix = prefix_map.get(attr)
                                if prefix and prefix in self.item_name_map_by_prefix:
                                    display_name = self.item_name_map_by_prefix[prefix].get(clean_id)
                                    if display_name:
                                        item_id = f"({prefix}){clean_id}"
                            
                            if not display_name:
                                display_name = tr.translate("unknown")
                                
                            var.set(f"({item_id}) {display_name}")
                    else:
                        var.set(item_id)
                else:
                    var.set(str(val))
        
        # 加载全局游戏数据
        for attr, var in self.game_fields.items():
            if attr == "caveChoice":
                mapping = {"0": tr.translate("none"), "1": tr.translate("bat_cave"), "2": tr.translate("mushroom_cave")}
                choice = self.save_proxy.playerChoiceFruitCave
                var.set(mapping.get(choice if choice is not None else "0", tr.translate("none")))
            elif attr == "stats/stepsTaken":
                var.set(str(self.save_proxy.stepsTaken))
            elif attr == "goldenWalnuts":
                var.set(str(self.save_proxy.goldenWalnuts))
            elif attr == "canCheat":
                # BooleanVar 的 set 必须传入 bool 类型
                val = self.save_proxy.canCheat
                var.set(val if isinstance(val, bool) else False)
            elif hasattr(self.save_proxy, attr):
                val = getattr(self.save_proxy, attr)
                var.set(str(val) if val is not None else "")
            else:
                val = self.save_proxy.get_text(attr)
                var.set(val if val is not None else "")

        # 使用模型获取经验和职业
        for i, exp in enumerate(player.experiencePoints):
            if i < len(self.exp_vars):
                self.exp_vars[i].set(str(exp))
        
        self.professions_list = player.get_professions()
        
        # 加载好感度
        self.friendship_data = {}
        for data in player.friendshipData:
            npc_name = data["name"]
            self.friendship_data[npc_name] = {
                "points": tk.StringVar(value=str(data["points"]))
            }
        
        self.load_inventory_for_player(player)
        self.refresh_items_list()

    def load_inventory_for_player(self, player):
        self.inventory_items = []
        if player is None: return
        
        self.inventory_max = player.maxItems
        
        for item in player.items:
            # 过滤空物品 (nil="true")
            if item.is_empty: continue
            
            raw_name = item.name or "Unknown"
            item_id = item.itemId or ""
            
            # 尝试映射中文名
            display_name = raw_name
            if item_id:
                # 优先尝试带前缀的 ID
                prefixed_id = item.prefixedId
                mapped_name = self.item_name_map.get(prefixed_id)
                if not mapped_name:
                    mapped_name = self.item_name_map.get(item_id)
                
                if not mapped_name:
                    # 在背包中，我们不知道具体分类，所以尝试所有可能的前缀
                    for prefix_items in self.item_name_map_by_prefix.values():
                        if item_id in prefix_items:
                            mapped_name = prefix_items[item_id]
                            break
                
                if mapped_name:
                    display_name = mapped_name
                elif raw_name in self.item_name_map:
                    display_name = self.item_name_map[raw_name]
            
            self.inventory_items.append({
                'display_name': display_name,
                'name': raw_name,
                'stack': tk.StringVar(value=str(item.stack)),
                'quality': tk.StringVar(value=str(item.quality)),
                'model': item,
                'item_id': item.prefixedId or item_id # 保存带前缀的 ID 方便后续编辑
            })

    def refresh_items_list(self):
        if not hasattr(self, "items_tree"): return
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        inv_root = self.items_tree.insert("", tk.END, text=tr.translate("backpack_with_count").format(count=len(self.inventory_items), max=self.inventory_max), open=True)
        for item in self.inventory_items:
            self.items_tree.insert(inv_root, tk.END, values=(item['display_name'], item['stack'].get(), item['quality'].get()))
        for chest in self.chests_data:
            chest_root = self.items_tree.insert("", tk.END, text=tr.translate("chest_with_location_count").format(location=chest['location'], count=len(chest['items']), max=chest['capacity']), open=False)
            for item in chest['items']:
                self.items_tree.insert(chest_root, tk.END, values=(item['display_name'], item['stack'].get(), item['quality'].get()))

    def refresh_pets_list(self):
        for widget in self.pets_frame.winfo_children(): widget.destroy()
        
        if not self.pets_data:
            ttk.Label(self.pets_frame, text=tr.translate("no_pets_found")).pack(pady=10)
            return

        # 使用 Grid 布局管理 pets_frame
        self.pets_frame.columnconfigure(0, weight=1)
        self.pets_frame.rowconfigure(1, weight=1)

        # 表头 (固定在顶部)
        headers = [
            ("pet_name", 15), ("pet_type", 12), ("pet_breed", 20), 
            ("friendship", 12), ("times_pet", 12), ("on_bed", 10), 
            ("pet_today", 10), ("location", 15)
        ]
        header_frame = ttk.Frame(self.pets_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        for col, (key, width) in enumerate(headers):
            header_frame.columnconfigure(col, weight=1, minsize=width*8) # 设置最小宽度
            lbl = ttk.Label(header_frame, text=tr.translate(key), width=width, anchor=tk.CENTER)
            lbl.grid(row=0, column=col, padx=5, pady=5) # 默认居中

        # 宠物列表容器 (使用 Canvas 实现局部滚动)
        canvas_container = ttk.Frame(self.pets_frame)
        canvas_container.grid(row=1, column=0, sticky="nsew")

        canvas = tk.Canvas(canvas_container, height=150, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        
        # 水平滚动条 (在 pets_frame 底部)
        h_scrollbar = ttk.Scrollbar(self.pets_frame, orient="horizontal", command=canvas.xview)
        
        list_frame = ttk.Frame(canvas)
        # 配置 list_frame 的列，使其与表头对齐
        for col, (key, width) in enumerate(headers):
            list_frame.columnconfigure(col, weight=1, minsize=width*8)

        def update_pet_scrollbars(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # 根据内容决定是否显示垂直滚动条
            if canvas.bbox("all")[3] <= 150:
                v_scrollbar.pack_forget()
            else:
                v_scrollbar.pack(side="right", fill="y")
            
            # 根据内容决定是否显示水平滚动条
            if canvas.bbox("all")[2] <= canvas.winfo_width():
                h_scrollbar.grid_forget()
            else:
                h_scrollbar.grid(row=2, column=0, sticky="ew")

        list_frame.bind("<Configure>", update_pet_scrollbars)
        canvas.bind("<Configure>", update_pet_scrollbars)

        canvas.create_window((0, 0), window=list_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # 初始布局
        canvas.pack(side="left", fill="both", expand=True)

        setup_mousewheel(canvas)

        for i, pet in enumerate(self.pets_data):
            # 直接在 list_frame 中 grid，确保所有行的列宽一致并与表头对齐
            ttk.Entry(list_frame, textvariable=pet['name'], width=15).grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            
            # 类型下拉
            type_cb = ttk.Combobox(list_frame, textvariable=pet['type'], values=["Cat", "Dog", "Turtle"], state="readonly", width=12)
            type_cb.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
            
            # 品种下拉
            def get_breed_values(p_type):
                data = PET_DATA.get(p_type, {})
                breeds = data.get("breeds", {})
                return [f"{k}: {tr.translate(v)}" for k, v in breeds.items()]

            breed_var = tk.StringVar()
            # 初始值
            curr_type = pet['type'].get()
            curr_breed_idx = int(pet['breed'].get() if pet['breed'].get() else 0)
            breeds_list = get_breed_values(curr_type)
            
            # 查找匹配的显示文本
            initial_breed_text = f"{curr_breed_idx}"
            for b_text in breeds_list:
                if b_text.startswith(f"{curr_breed_idx}:"):
                    initial_breed_text = b_text
                    break
            breed_var.set(initial_breed_text)

            breed_cb = ttk.Combobox(list_frame, textvariable=breed_var, values=breeds_list, state="readonly", width=20)
            breed_cb.grid(row=i, column=2, padx=5, pady=2, sticky="ew")

            # 当品种改变时同步回原始 breed 变量
            def on_breed_change(event, b_var=breed_var, p_ref=pet):
                val = b_var.get()
                if ":" in val:
                    idx = val.split(":")[0]
                    p_ref['breed'].set(idx)

            breed_cb.bind("<<ComboboxSelected>>", on_breed_change)

            # 当类型改变时更新品种列表
            def on_type_change(event, t_cb=type_cb, b_cb=breed_cb, b_var=breed_var, p_ref=pet):
                new_type = t_cb.get()
                new_breeds = get_breed_values(new_type)
                b_cb["values"] = new_breeds
                if new_breeds:
                    b_var.set(new_breeds[0])
                    p_ref['breed'].set(new_breeds[0].split(":")[0])
                else:
                    b_var.set("0")
                    p_ref['breed'].set("0")

            type_cb.bind("<<ComboboxSelected>>", on_type_change)
            
            ttk.Entry(list_frame, textvariable=pet['friendship'], width=12).grid(row=i, column=3, padx=5, pady=2, sticky="ew")
            ttk.Entry(list_frame, textvariable=pet['timesPet'], width=12).grid(row=i, column=4, padx=5, pady=2, sticky="ew")
            
            cb_bed = ttk.Checkbutton(list_frame, variable=pet['isSleepingOnFarmerBed'])
            cb_bed.grid(row=i, column=5, padx=5, pady=2) # 默认居中
            self.add_tooltip(cb_bed, tr.translate("on_bed_tip"))

            cb_pet = ttk.Checkbutton(list_frame, variable=pet['grantedFriendshipForPet'])
            cb_pet.grid(row=i, column=6, padx=5, pady=2) # 默认居中
            self.add_tooltip(cb_pet, tr.translate("pet_today_tip"))

            ttk.Label(list_frame, text=pet['location'], width=15, anchor=tk.CENTER).grid(row=i, column=7, padx=5, pady=2, sticky="ew")


    def refresh_animals_list(self):
        """ 刷新农场动物列表 UI """
        for widget in self.animals_frame.winfo_children(): widget.destroy()
        
        if not self.animals_data:
            ttk.Label(self.animals_frame, text=tr.translate("no_animals_found")).pack(pady=10)
            return

        # 使用 Grid 布局
        self.animals_frame.columnconfigure(0, weight=1)
        self.animals_frame.rowconfigure(1, weight=1)

        # 表头 (固定在顶部，不随内容滚动)
        headers = [
            ("animal_name", 15), ("animal_type", 12), ("gender", 10), 
            ("animal_age", 12), ("friendship_range", 15), ("fullness_range", 12), 
            ("happiness_range", 12), ("reproduction", 8), ("animal_cracker", 8), 
            ("was_pet", 8), ("is_eating", 8), ("was_autopet", 8), 
            ("home", 15), ("location", 15)
        ]
        header_frame = ttk.Frame(self.animals_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        for col, (key, width) in enumerate(headers):
            header_frame.columnconfigure(col, weight=1, minsize=width*8)
            lbl = ttk.Label(header_frame, text=tr.translate(key), width=width, anchor=tk.CENTER)
            lbl.grid(row=0, column=col, padx=5, pady=5) # 默认居中

        # 创建一个可滚动的区域
        canvas_container = ttk.Frame(self.animals_frame)
        canvas_container.grid(row=1, column=0, sticky="nsew")

        canvas = tk.Canvas(canvas_container, height=300, highlightthickness=0) # 增加高度
        v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        
        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(self.animals_frame, orient="horizontal", command=canvas.xview)
        
        scroll_frame = ttk.Frame(canvas)
        # 配置 scroll_frame 的列，使其与表头对齐
        for col, (key, width) in enumerate(headers):
            scroll_frame.columnconfigure(col, weight=1, minsize=width*8)

        def update_animal_scrollbars(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # 根据内容决定是否显示垂直滚动条
            if canvas.bbox("all")[3] <= 300:
                v_scrollbar.pack_forget()
            else:
                v_scrollbar.pack(side="right", fill="y")
            
            # 根据内容决定是否显示水平滚动条
            if canvas.bbox("all")[2] <= canvas.winfo_width():
                h_scrollbar.grid_forget()
            else:
                h_scrollbar.grid(row=2, column=0, sticky="ew")

        scroll_frame.bind("<Configure>", update_animal_scrollbars)
        canvas.bind("<Configure>", update_animal_scrollbars)

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # 初始布局
        canvas.pack(side="left", fill="both", expand=True)
        
        setup_mousewheel(canvas)

        for i, animal in enumerate(self.animals_data):
            row = i # 因为表头移出去了，这里从0开始
            
            ttk.Entry(scroll_frame, textvariable=animal['name'], width=15).grid(row=row, column=0, padx=5, pady=2, sticky="ew")
            ttk.Label(scroll_frame, text=animal['type'].get(), width=12, anchor=tk.CENTER).grid(row=row, column=1, padx=5, pady=2, sticky="ew")
            
            gender_cb = ttk.Combobox(scroll_frame, textvariable=animal['gender'], values=[tr.translate("male"), tr.translate("female")], state="readonly", width=10)
            gender_cb.grid(row=row, column=2, padx=5, pady=2, sticky="ew")
            
            ttk.Entry(scroll_frame, textvariable=animal['age'], width=12).grid(row=row, column=3, padx=5, pady=2, sticky="ew")
            ttk.Entry(scroll_frame, textvariable=animal['friendship'], width=15).grid(row=row, column=4, padx=5, pady=2, sticky="ew")
            ttk.Entry(scroll_frame, textvariable=animal['fullness'], width=12).grid(row=row, column=5, padx=5, pady=2, sticky="ew")
            ttk.Entry(scroll_frame, textvariable=animal['happiness'], width=12).grid(row=row, column=6, padx=5, pady=2, sticky="ew")
            
            cb_reprod = ttk.Checkbutton(scroll_frame, variable=animal['allowReproduction'])
            cb_reprod.grid(row=row, column=7, padx=5, pady=2)
            self.add_tooltip(cb_reprod, tr.translate("allow_reproduction_tip"))

            cb_cracker = ttk.Checkbutton(scroll_frame, variable=animal['hasEatenAnimalCracker'])
            cb_cracker.grid(row=row, column=8, padx=5, pady=2)
            self.add_tooltip(cb_cracker, tr.translate("animal_cracker_tip"))

            cb_pet = ttk.Checkbutton(scroll_frame, variable=animal['wasPet'])
            cb_pet.grid(row=row, column=9, padx=5, pady=2)
            self.add_tooltip(cb_pet, tr.translate("pet_today_tip"))

            cb_eating = ttk.Checkbutton(scroll_frame, variable=animal['isEating'])
            cb_eating.grid(row=row, column=10, padx=5, pady=2)
            self.add_tooltip(cb_eating, tr.translate("is_eating_tip"))

            cb_autopet = ttk.Checkbutton(scroll_frame, variable=animal['wasAutoPet'])
            cb_autopet.grid(row=row, column=11, padx=5, pady=2)
            self.add_tooltip(cb_autopet, tr.translate("was_autopet_tip"))

            ttk.Entry(scroll_frame, textvariable=animal['buildingTypeILiveIn'], width=15).grid(row=row, column=12, padx=5, pady=2, sticky="ew")
            
            ttk.Label(scroll_frame, text=animal['location'], width=15, anchor=tk.CENTER).grid(row=row, column=13, padx=5, pady=2, sticky="ew")

    def on_player_selected(self, event):
        idx = self.player_selector.current()
        if idx != -1:
            self.save_current_player_to_element()
            self.current_player_idx = idx
            self.load_player_data(idx)

    def change_language(self, event=None):
        """切换 UI 语言"""
        selected = self.lang_var.get()
        new_lang = "zh" if selected == "中文" else "en"
        
        if new_lang != tr.current_lang:
            tr.set_language(new_lang)
            # 为了简单起见，这里销毁并重建 UI
            for widget in self.root.winfo_children():
                widget.destroy()
            
            # 重新初始化一些状态
            self.color_previews = {}
            # 重新构建 UI
            self.setup_ui()
            # 如果已经加载了数据，重新刷新显示
            if hasattr(self, "save_proxy"):
                self.refresh_save_list()
                # 提示用户数据已保留但 UI 已刷新
                self.status_var.set(tr.translate('language_changed'))

    def save_current_player_to_element(self):
        if self.current_player_idx is None: return
        player = self.all_players[self.current_player_idx]["model"]
        
        # 1. 玩家基础字段
        for attr, var in self.player_fields.items():
            if attr == "spouse":
                self.save_proxy.spouse = var.get() if var.get() != "None" else ""
                continue
            
            val = str(var.get())
            if hasattr(player, attr):
                # 特殊处理性别映射
                if attr == "gender":
                    player.gender = "0" if val == tr.translate("male") else "1"
                # 特殊处理颜色映射
                elif attr in ["hairColor", "eyeColor"]:
                    try:
                        r, g, b = map(int, val.split(","))
                        setattr(player, attr, (r, g, b, 255))
                    except:
                        pass # 格式不对则跳过
                # 特殊处理宠物类型
                elif attr == "catPerson":
                    mapping = {
                        tr.translate("cat"): ("Cat", True),
                        tr.translate("dog"): ("Dog", False),
                        tr.translate("turtle"): ("Turtle", False)
                    }
                    p_type_str, cat_person_val = mapping.get(val, ("Cat", True))
                    player.catPerson = cat_person_val
                    player.petType = p_type_str
                # 特殊处理装备位 Combobox 的保存 (解析 (ID) Name 格式)
                elif attr in self.equipment_map:
                    if val == tr.translate("none"):
                        setattr(player, attr, None)
                    elif val.startswith("(") and ") " in val:
                        # 从 "(ID) Name" 中提取 ID，考虑 ID 本身可能包含括号 (如 (H)60)
                        # 找最后一个 ") " 的位置
                        last_bracket_idx = val.rfind(") ")
                        if last_bracket_idx != -1:
                            item_id = val[1:last_bracket_idx]
                            setattr(player, attr, item_id)
                        else:
                            setattr(player, attr, val)
                    else:
                        # 如果没有 ") "，则视为原始 ID (例如 "(H)60" 或 "60")
                        setattr(player, attr, val)
                else:
                    setattr(player, attr, val)
        
        # 2. 背包物品数据
        for item_data in self.inventory_items:
            item_model = item_data['model']
            item_model.stack = int(item_data['stack'].get())
            item_model.quality = int(item_data['quality'].get())
        
        # 3. 箱子物品数据
        for chest in self.chests_data:
            for item_data in chest['items']:
                item_model = item_data['model']
                item_model.stack = int(item_data['stack'].get())
                item_model.quality = int(item_data['quality'].get())
        
        # 4. 全局游戏数据
        for attr, var in self.game_fields.items():
            if attr == "caveChoice":
                mapping = {
                    tr.translate("none"): "0",
                    tr.translate("bat_cave"): "1",
                    tr.translate("mushroom_cave"): "2"
                }
                self.save_proxy.playerChoiceFruitCave = mapping.get(var.get(), "0")
                continue
            
            if attr == "canCheat":
                self.save_proxy.canCheat = var.get()
                continue

            # 特殊处理嵌套路径 stats/stepsTaken
            if attr == "stats/stepsTaken":
                self.save_proxy.stepsTaken = int(var.get())
                continue

            if attr == "goldenWalnuts":
                self.save_proxy.goldenWalnuts = int(var.get() if var.get() else 0)
                continue

            # 使用 SaveProxy 的属性访问或 get_text/set_text
            if hasattr(self.save_proxy, attr):
                setattr(self.save_proxy, attr, var.get())
            else:
                self.save_proxy.set_text(attr, var.get())
        
        # 5. 天气数据
        self.save_proxy.isRaining = self.weather_vars["isRaining"].get()
        self.save_proxy.isDebrisWeather = self.weather_vars["isDebrisWeather"].get()
        self.save_proxy.isLightning = self.weather_vars["isLightning"].get()
        self.save_proxy.isSnowing = self.weather_vars["isSnowing"].get()
        self.save_proxy.isGreenRain = self.weather_vars["isGreenRain"].get()

        # 6. 经验值
        for i, var in enumerate(self.exp_vars):
            player.set_experience(i, int(var.get() if var.get() else 0))
        
        # 7. 职业
        player.set_professions(self.professions_list)
        
        # 8. 保存好感度
        for npc_name, data in self.friendship_data.items():
            player.update_friendship(npc_name, data["points"].get())

        # 9. 宠物数据
        for pet_data in self.pets_data:
            pet = pet_data["model"]
            pet.name = pet_data["name"].get()
            pet.petType = pet_data["type"].get()
            pet.whichBreed = int(pet_data["breed"].get() if pet_data["breed"].get() else 0)
            pet.friendshipTowardFarmer = int(pet_data["friendship"].get() if pet_data["friendship"].get() else 0)
            pet.timesPet = int(pet_data["timesPet"].get() if pet_data["timesPet"].get() else 0)
            pet.isSleepingOnFarmerBed = pet_data["isSleepingOnFarmerBed"].get()
            pet.grantedFriendshipForPet = pet_data["grantedFriendshipForPet"].get()

        # 10. 农场动物数据
        for animal_data in self.animals_data:
            animal = animal_data["model"]
            animal.name = animal_data["name"].get()
            animal.gender = animal_data["gender"].get()
            animal.age = int(animal_data["age"].get() if animal_data["age"].get() else 0)
            animal.friendship = int(animal_data["friendship"].get() if animal_data["friendship"].get() else 0)
            animal.fullness = int(animal_data["fullness"].get() if animal_data["fullness"].get() else 0)
            animal.happiness = int(animal_data["happiness"].get() if animal_data["happiness"].get() else 0)
            animal.allowReproduction = animal_data["allowReproduction"].get()
            animal.hasEatenAnimalCracker = animal_data["hasEatenAnimalCracker"].get()
            animal.wasPet = animal_data["wasPet"].get()
            animal.isEating = animal_data["isEating"].get()
            animal.wasAutoPet = animal_data["wasAutoPet"].get()
            animal.buildingTypeILiveIn = animal_data["buildingTypeILiveIn"].get()

    def save_data(self):
        if not self.save_file: return
        self.save_current_player_to_element()
        try:
            # 创建备份
            bak = self.save_file + ".bak"
            if not os.path.exists(bak): shutil.copy2(self.save_file, bak)
            
            info_path = os.path.join(os.path.dirname(self.save_file), self.info_file)
            if os.path.exists(info_path):
                info_bak = info_path + ".bak"
                if not os.path.exists(info_bak): shutil.copy2(info_path, info_bak)
            
            # 使用代理保存
            self.save_proxy.save()
                
            messagebox.showinfo(tr.translate("success"), tr.translate("save_success").format(os.path.basename(bak)))
            self.status_var.set(f"{tr.translate('saved')}: {os.path.basename(self.save_file)}")
        except Exception as e:
            messagebox.showerror(tr.translate("save_fail"), f"{tr.translate('cannot_write_save').format(e)}")

    def add_tooltip(self, widget, text):
        """为控件添加简单的 Tooltip 提示"""
        def enter(event):
            self.status_var.set(f"ℹ️ {text}")
        def leave(event):
            self.status_var.set(f"{tr.translate('save_loaded')}: {os.path.basename(self.save_file)}")
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def choose_color(self, attr, preview_canvas):
        """弹出颜色选择器并更新预览"""
        current_rgb_str = self.player_fields[attr].get()
        initial_color = "#ffffff"
        if current_rgb_str:
            try:
                # 尝试解析 R,G,B 格式
                parts = current_rgb_str.split(",")
                r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                initial_color = f'#{r:02x}{g:02x}{b:02x}'
            except:
                pass
        
        cd = ColorChooserDialog(initialcolor=initial_color, title=tr.translate("choose_color"), parent=self.root)
        cd.show()
        if cd.result:
            hex_color = cd.result.hex
            rgb_tuple = cd.result.rgb
            r, g, b = map(int, rgb_tuple)
            self.player_fields[attr].set(f"{r},{g},{b}")
            preview_canvas.config(bg=hex_color)

    def select_equipment_item(self, attr):
        """弹出物品选择对话框来修改装备位"""
        if not self.all_players:
            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save_first"))
            return
            
        player = self.all_players[self.current_player_idx]["model"]
        current_val = getattr(player, attr)
        
        initial_data = None
        if current_val and hasattr(current_val, "itemId"):
            # 如果已经是 Item 对象，映射中文名
            raw_name = current_val.name or tr.translate("unknown")
            item_id = current_val.itemId or ""
            display_name = raw_name
            if item_id:
                mapped_name = self.item_name_map.get(item_id)
                if not mapped_name:
                    # 根据装备位推断前缀
                    prefix_map = {
                        "hat": "H",
                        "shirtItem": "S",
                        "pantsItem": "P",
                        "boots": "B",
                        "leftRing": "O",
                        "rightRing": "O",
                        "trinketItem": "TR"
                    }
                    prefix = prefix_map.get(attr)
                    if prefix and prefix in self.item_name_map_by_prefix:
                        mapped_name = self.item_name_map_by_prefix[prefix].get(item_id)
                
                if mapped_name:
                    display_name = mapped_name
                elif raw_name in self.item_name_map:
                    display_name = self.item_name_map[raw_name]
                
            initial_data = {
                "name": display_name,
                "stack": str(current_val.stack),
                "quality": str(current_val.quality),
                "model": current_val
            }
            
        dialog = AddItemDialog(self.root, title=f"{tr.translate('select_equipment')} - {attr}", initial_data=initial_data, category_hint=attr)
        self.root.wait_window(dialog)
        
        if dialog.result:
            # 更新 UI 变量，使用 (ID) Name 格式以保持一致
            display_val = f"({dialog.result['id']}) {dialog.result['name']}"
            self.player_fields[attr].set(display_val)
            # 立即应用到模型
            setattr(player, attr, dialog.result["id"])
            
            # 如果修改的是衣服或裤子，1.6版本需要同步颜色数据
            # 衣服和裤子在存档中通常有 <dyeColor> 节点，如果设为新 ID，可能需要重置颜色
            if attr in ["shirtItem", "pantsItem"]:
                item_obj = getattr(player, attr)
                if item_obj:
                    # 尝试重置颜色为默认或移除染色
                    item_obj.set_bool("dyed", False)

            messagebox.showinfo(tr.translate("selected_item"), f"{tr.translate('selected_item')}: {dialog.result['name']} (ID: {dialog.result['id']})")

    # 以下是功能实现
    def show_professions_window(self):
        if not self.save_file:
            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))
            return
        
        # 获取当前玩家的等级
        player = self.all_players[self.current_player_idx]["model"]
        levels = {
            "Farming": int(self.player_fields["farmingLevel"].get() or 0),
            "Mining": int(self.player_fields["miningLevel"].get() or 0),
            "Foraging": int(self.player_fields["foragingLevel"].get() or 0),
            "Fishing": int(self.player_fields["fishingLevel"].get() or 0),
            "Combat": int(self.player_fields["combatLevel"].get() or 0)
        }
        
        dialog = ProfessionDialog(self.root, self.professions_list, levels)
        self.root.wait_window(dialog)
        if dialog.result is not None:
            self.professions_list = dialog.result
            messagebox.showinfo(tr.translate("updated"), tr.translate("professions_updated"))

    def show_experience_window(self):
        if not self.save_file:
            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))
            return
        dialog = ExperienceDialog(self.root, self.exp_vars)
        self.root.wait_window(dialog)
        messagebox.showinfo(tr.translate("updated"), tr.translate("xp_updated"))

    def show_friendship_window(self):
        if not self.save_file:
            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))
            return
        if not self.friendship_data:
            messagebox.showinfo(tr.translate("info"), tr.translate("no_friendship_found"))
            return
        dialog = FriendshipDialog(self.root, self.friendship_data)
        self.root.wait_window(dialog)
        messagebox.showinfo(tr.translate("updated"), tr.translate("friendship_updated"))
    def show_recipes_window(self):
        if not self.all_players:
            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))
            return
        player = self.all_players[self.current_player_idx]["model"]
        dialog = RecipeDialog(self.root, player)
        self.root.wait_window(dialog)
        messagebox.showinfo(tr.translate("updated"), tr.translate("recipes_updated"))

    def show_special_powers_window(self):
        if not self.all_players:
            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))
            return
        player = self.all_players[self.current_player_idx]["model"]
        dialog = SpecialPowersDialog(self.root, player)
        self.root.wait_window(dialog)
        messagebox.showinfo(tr.translate("updated"), tr.translate("special_powers_updated"))

    def show_bundles_window(self):
        """显示社区中心收集包管理窗口"""
        if not hasattr(self, "save_proxy") or not self.save_proxy:
            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))
            return
        
        from models.community_bundles import CommunityBundles
        try:
            bundles_manager = CommunityBundles(self.save_proxy)
            if not bundles_manager.bundles:
                messagebox.showinfo(tr.translate("info"), tr.translate("no_bundles_found"))
                return
                
            dialog = BundlesDialog(self.root, bundles_manager)
            self.root.wait_window(dialog)
        except Exception as e:
            messagebox.showerror(tr.translate("error"), tr.translate("load_bundles_failed_msg").format(error=e))

    def edit_selected_item(self):
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showwarning(tr.translate("info"), tr.translate("please_select_item_to_modify"))
            return
            
        item_id = selection[0]
        parent_id = self.items_tree.parent(item_id)
        
        # 如果选中的是顶层节点（背包或箱子根节点）
        if not parent_id:
            node_text = self.items_tree.item(item_id, "text")
            if tr.translate("chests") in node_text:
                # 寻找匹配的箱子
                for chest in self.chests_data:
                    if chest['location'] in node_text:
                        dialog = ChestDialog(self.root, chest)
                        self.root.wait_window(dialog)
                        if dialog.result:
                            self.refresh_items_list()
                            messagebox.showinfo(tr.translate("success"), tr.translate("chest_updated"))
                        return
            return
            
        item_index = self.items_tree.index(item_id)
        parent_text = self.items_tree.item(parent_id, "text")
        
        target_item = None
        if tr.translate("backpack") in parent_text:
            if 0 <= item_index < len(self.inventory_items):
                target_item = self.inventory_items[item_index]
        else:
            for chest in self.chests_data:
                if chest['location'] in parent_text:
                    if 0 <= item_index < len(chest['items']):
                        target_item = chest['items'][item_index]
                    break
                    
        if not target_item: return
        
        # 准备初始数据
        initial_data = {
            "name": target_item["display_name"], # 传递显示名称 (中文)
            "stack": target_item["stack"].get(),
            "quality": target_item["quality"].get(),
            "model": target_item["model"],
            "id": target_item.get("item_id", "") # 传递 ID (带前缀)
        }
        
        dialog = AddItemDialog(self.root, title=tr.translate("modify_item"), initial_data=initial_data)
        self.root.wait_window(dialog)
        
        if dialog.result:
            # 检查这个 new_name 是否是某个中文名，如果是，尝试找到对应的英文名
            # 这样可以保持 XML 的英文一致性
            new_name = dialog.result["name"]
            final_save_name = new_name
            
            # 建立反向映射: 中文名 -> 原始英文名
            rev_map = {}
            for cat, items in ITEM_CATEGORIES.items():
                for key, data in items.items():
                    zh = tr.translate(key)
                    if zh != key:
                        rev_map[zh] = data["name"]
            
            if new_name in rev_map:
                final_save_name = rev_map[new_name]
                    
            # 更新内存数据
            target_item["display_name"] = new_name
            target_item["name"] = final_save_name
            target_item["stack"].set(dialog.result["stack"])
            target_item["quality"].set(dialog.result["quality"])
            
            # 使用 Item 模型更新
            item_model = target_item["model"]
            item_model.name = final_save_name
            item_model.stack = int(dialog.result["stack"])
            item_model.quality = int(dialog.result["quality"])
            item_model.itemId = dialog.result["id"]
            
            # 更新保存的带前缀 ID
            target_item["item_id"] = item_model.prefixedId or dialog.result["id"]
            
            self.refresh_items_list()
            messagebox.showinfo(tr.translate("success"), tr.translate("item_modified_msg").format(name=new_name))
    def add_new_item(self):
        if not self.all_players:
            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))
            return
            
        selection = self.items_tree.selection()
        target_container = tr.translate("backpack")
        target_model = None # Farmer or Chest model
        target_list = None
        
        if selection:
            item_id = selection[0]
            parent_id = self.items_tree.parent(item_id)
            
            # 如果选中的是顶层节点（背包 or 箱子根节点）
            if not parent_id:
                node_text = self.items_tree.item(item_id, "text")
            else:
                # 如果选中是物品，则看它所属的父节点
                node_text = self.items_tree.item(parent_id, "text")
                
            if tr.translate("backpack") in node_text:
                target_container = tr.translate("backpack")
                target_model = self.all_players[self.current_player_idx]["model"]
                target_list = self.inventory_items
            else:
                # 寻找匹配的箱子
                for chest in self.chests_data:
                    if chest['location'] in node_text:
                        target_container = tr.translate("chest_at").format(location=chest['location'])
                        target_model = chest['model']
                        target_list = chest['items']
                        break
        
        # 默认回退到背包
        if target_model is None:
            target_container = tr.translate("backpack")
            target_model = self.all_players[self.current_player_idx]["model"]
            target_list = self.inventory_items

        dialog = AddItemDialog(self.root, title=tr.translate("add_item_to").format(container=target_container))
        self.root.wait_window(dialog)
        
        if dialog.result:
            # 检查是否是中文名并获取英文名
            new_name = dialog.result["name"]
            final_save_name = new_name
            
            # 建立反向映射: 中文名 -> 原始英文名
            rev_map = {}
            for cat, items in ITEM_CATEGORIES.items():
                for key, data in items.items():
                    zh = tr.translate(key)
                    if zh != key:
                        rev_map[zh] = data["name"]
            
            if new_name in rev_map:
                final_save_name = rev_map[new_name]

            # 使用模型方法添加物品
            item_model = target_model.add_item(
                name=final_save_name,
                item_id=dialog.result["id"],
                stack=int(dialog.result["stack"]),
                quality=int(dialog.result["quality"])
            )
            
            # 更新内存列表
            if target_list is not None:
                target_list.append({
                    'display_name': new_name,
                    'name': final_save_name,
                    'stack': tk.StringVar(value=str(dialog.result["stack"])),
                    'quality': tk.StringVar(value=str(dialog.result["quality"])),
                    'model': item_model,
                    'item_id': item_model.prefixedId or dialog.result["id"]
                })
            
            self.refresh_items_list()
            messagebox.showinfo(tr.translate("success"), tr.translate("item_added_to_container_msg").format(name=new_name, stack=dialog.result['stack'], container=target_container))
    def delete_selected_item(self):
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showwarning(tr.translate("info"), tr.translate("please_select_item_to_delete"))
            return
            
        item_id = selection[0]
        # 判断是背包还是箱子
        parent_id = self.items_tree.parent(item_id)
        if not parent_id:
            return # 根节点不删
            
        item_index = self.items_tree.index(item_id)
        parent_text = self.items_tree.item(parent_id, "text")
        
        if tr.translate("backpack") in parent_text:
            if 0 <= item_index < len(self.inventory_items):
                item_data = self.inventory_items.pop(item_index)
                # 使用模型方法删除
                player = self.all_players[self.current_player_idx]["model"]
                player.remove_item(item_data['model'])
                messagebox.showinfo(tr.translate("success"), tr.translate("deleted_from_backpack_msg").format(name=item_data['display_name']))
        else:
            # 处理箱子
            for chest in self.chests_data:
                if chest['location'] in parent_text:
                    if 0 <= item_index < len(chest['items']):
                        item_data = chest['items'].pop(item_index)
                        # 使用模型方法删除
                        chest['model'].remove_item(item_data['model'])
                        messagebox.showinfo(tr.translate("success"), tr.translate("deleted_from_chest_msg").format(name=item_data['display_name']))
                    break
        
        self.refresh_items_list()
