# Define modal dialogs used to edit focused pieces of save data from the UI.
import tkinter as tk

from tkinter import messagebox, ttk

import ttkbootstrap as ttkb

from ttkbootstrap.dialogs.colorchooser import ColorChooserDialog

from models.item_data import ITEM_CATEGORIES

from models.profession_data import PROFESSIONS

from models.special_powers import ACHIEVEMENTS, MAIL_FLAGS, WALLET_ITEMS

from utils import tr

from utils.game_text_localization import (
    get_mail_flag_category,
    get_mail_flag_category_label,
    get_mail_flag_category_order,
    translate_mail_flag,
    translate_bundle_name,
    translate_location_name,
    translate_npc_name,
    translate_profession_desc,
    translate_profession_name,
    translate_room_name,
)

from utils.item_localization import get_localized_item_name, translate_item_name

from .helpers import bind_numeric_input_limit, center_window, setup_mousewheel

def translate_special_powers_entry(entry):

    name_key = entry.get("name_key")

    desc_key = entry.get("desc_key")

    name = tr.translate(name_key) if name_key else entry["name"]

    desc = tr.translate(desc_key) if desc_key else entry["desc"]

    return name, desc

# Manage a modal dialog that collects a focused set of values from the user.
# It keeps dialog widgets and returned values synchronized during the modal workflow.
class AddItemDialog(ttkb.Toplevel):

    def __init__(self, parent, title=None, initial_data=None, category_hint=None):

        super().__init__(parent)

        if title is None:

            title = tr.translate("add_item")

        self.title(title)

        center_window(self, 450, 600)

        self.result = None

        self.category_hint = category_hint

        self.selected_save_name = None

        self.selected_item_id = ""

        self.transient(parent)

        self.grab_set()

        self.categories = ITEM_CATEGORIES

        self.category_names = {cat: tr.translate(cat) for cat in self.categories.keys()}

        self.rev_category_names = {v: k for k, v in self.category_names.items()}

        self.flat_presets = {}

        for cat, items in self.categories.items():

            translated_cat = self.category_names[cat]

            for name, data in items.items():

                if isinstance(data, dict):

                    item_info = dict(data)

                else:

                    item_info = {"id": str(data)}

                if "name" not in item_info:

                    item_info["name"] = name

                if "id" not in item_info:

                    item_info["id"] = ""

                item_info["save_name"] = item_info["name"]

                item_info["display_name"] = get_localized_item_name(name, item_info)

                item_id = item_info["id"]

                if "(" not in item_id:

                    if cat == "rings": prefix = "O"

                    elif cat == "trinkets": prefix = "TR"

                    elif cat == "hats": prefix = "H"

                    elif cat == "shoes": prefix = "B"

                    elif cat == "clothes":

                        prefix = None

                    else: prefix = None

                    if prefix:

                        item_info["id"] = f"({prefix}){item_id}"

                self.flat_presets[f"[{translated_cat}] {item_info['display_name']}"] = {

                    "data": item_info,

                    "cat_key": cat

                }

        main_frame = ttk.Frame(self, padding=20)

        main_frame.pack(fill=tk.BOTH, expand=True)

        search_frame = ttk.LabelFrame(main_frame, text=tr.translate("quick_select_item"), padding=10)

        search_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        controls_frame = ttk.Frame(search_frame)

        controls_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(controls_frame, text=tr.translate("category")).grid(row=0, column=0, sticky=tk.W)

        default_cat = tr.translate("all")

        if category_hint:

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

        list_container = ttk.Frame(search_frame)

        list_container.pack(fill=tk.BOTH, expand=True)

        self.item_listbox = tk.Listbox(list_container, height=10)

        h_scrollbar = ttk.Scrollbar(list_container, orient=tk.HORIZONTAL, command=self.item_listbox.xview)

        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        v_scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.item_listbox.yview)

        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.item_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.item_listbox.bind("<<ListboxSelect>>", self.on_listbox_select)

        self.item_listbox.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        setup_mousewheel(self.item_listbox)

        self.update_search()

        edit_frame = ttk.LabelFrame(main_frame, text=tr.translate("item_details"), padding=10)

        edit_frame.pack(fill=tk.X, pady=5)

        ttk.Label(edit_frame, text=tr.translate("item_name")).grid(row=0, column=0, sticky=tk.W, pady=5)

        self.name_var = tk.StringVar(value=initial_data["name"] if initial_data else "")

        ttk.Entry(edit_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)

        ttk.Label(edit_frame, text=tr.translate("item_id")).grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))

        initial_id = ""

        if initial_data:

            model = initial_data.get("model")

            if model:

                initial_id = model.itemId or ""

        self.id_var = tk.StringVar(value=initial_id)

        if initial_data and "id" in initial_data and initial_data["id"]:

            self.id_var.set(initial_data["id"])

        if initial_data:

            self.selected_save_name = initial_data.get("save_name")

            self.selected_item_id = self.id_var.get()

        ttk.Entry(edit_frame, textvariable=self.id_var, width=10).grid(row=0, column=3, sticky=tk.W, pady=5, padx=5)

        ttk.Label(edit_frame, text=tr.translate("quantity")).grid(row=1, column=0, sticky=tk.W, pady=5)

        self.stack_var = tk.StringVar(value=initial_data["stack"] if initial_data else "1")

        bind_numeric_input_limit(self.stack_var, min_value=1)

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

        help_text = f"{tr.translate('description')}: {tr.translate('id_help_text')}"

        ttk.Label(main_frame, text=help_text, font=("", 8), foreground="gray").pack(pady=5)

        btn_frame = ttk.Frame(main_frame)

        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text=tr.translate("confirm_add"), command=self.on_ok).pack(side=tk.LEFT, padx=10)

        ttk.Button(btn_frame, text=tr.translate("cancel"), command=self.destroy).pack(side=tk.LEFT, padx=10)

    # Update the search.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def update_search(self, *args):

        search_term = self.search_var.get().lower()

        selected_cat = self.category_var.get()

        self.item_listbox.delete(0, tk.END)

        self.item_listbox_data = {}

        matches = []

        for display_name, entry in self.flat_presets.items():

            data = entry["data"]

            if selected_cat != tr.translate("all") and not display_name.startswith(f"[{selected_cat}]"):

                continue

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

            name_for_search = display_name.split("] ", 1)[-1] if "] " in display_name else display_name

            en_name = data.get("name", "").lower()

            item_id_lower = item_id.lower()

            if (search_term in name_for_search.lower() or

                search_term in en_name or

                search_term in item_id_lower):

                matches.append((display_name, entry))

        matches.sort(key=lambda x: (0 if tr.translate("common_items") in x[0] else 1, x[0]))

        for display_name, entry in matches:

            data = entry["data"]

            list_text = f"{display_name} (ID: {data.get('id', 'N/A')})"

            self.item_listbox.insert(tk.END, list_text)

            self.item_listbox_data[list_text] = data

    # Synchronize the dialog fields with the current list selection.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def on_listbox_select(self, event):

        selection = self.item_listbox.curselection()

        if not selection: return

        list_text = self.item_listbox.get(selection[0])

        if hasattr(self, "item_listbox_data") and list_text in self.item_listbox_data:

            p = self.item_listbox_data[list_text]

            pure_name = list_text.split("] ", 1)[-1].split(" (ID:", 1)[0] if "] " in list_text else list_text.split(" (ID:", 1)[0]

            self.name_var.set(pure_name)

            self.id_var.set(p.get("id", ""))

            self.selected_save_name = p.get("save_name", p.get("name", pure_name))

            self.selected_item_id = p.get("id", "")

    # Resolve the English item name that should be written back to the save.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def resolve_save_name(self):

        current_id = self.id_var.get().strip()

        current_name = self.name_var.get().strip()

        if current_id:

            candidates = [
                entry["data"]
                for entry in self.flat_presets.values()
                if str(entry["data"].get("id", "")) == current_id
            ]

            display_matches = [
                candidate
                for candidate in candidates
                if candidate.get("display_name") == current_name
            ]

            if len(display_matches) == 1:

                return display_matches[0].get("save_name", current_name)

            if len(candidates) == 1:

                return candidates[0].get("save_name", current_name)

        if self.selected_save_name and current_id == self.selected_item_id:

            return self.selected_save_name

        return current_name

    # Validate the current inputs, store the dialog result, and close the window.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def on_ok(self):

        if not self.id_var.get() or not self.name_var.get():

            messagebox.showwarning(tr.translate("info"), tr.translate("name_id_empty"))

            return

        if not self.stack_var.get().isdigit():

            messagebox.showerror(tr.translate("error"), tr.translate("quantity_must_be_number"))

            return

        self.result = {

            "name": self.name_var.get(),

            "save_name": self.resolve_save_name(),

            "id": self.id_var.get(),

            "stack": self.stack_var.get(),

            "quality": self.quality_map.get(self.quality_var.get(), "0")

        }

        self.destroy()

# Manage a modal dialog that collects a focused set of values from the user.
# It keeps dialog widgets and returned values synchronized during the modal workflow.
class ProfessionDialog(ttkb.Toplevel):

    def __init__(self, parent, current_professions, player_levels):

        super().__init__(parent)

        self.title(tr.translate("skill_professions"))

        center_window(self, 700, 850)

        self.result = list(current_professions)

        self.player_levels = player_levels

        self.transient(parent)

        self.grab_set()

        main_frame = ttk.Frame(self, padding=10)

        main_frame.pack(fill=tk.BOTH, expand=True)

        content_frame = ttk.Frame(main_frame)

        content_frame.pack(fill=tk.BOTH, expand=True)

        self.check_vars = {}

        categories_map = {
            "Farming": tr.translate("farming"),
            "Mining": tr.translate("mining"),
            "Foraging": tr.translate("foraging"),
            "Fishing": tr.translate("fishing"),
            "Combat": tr.translate("combat"),
        }

        for cat_key, display_name in categories_map.items():

            group_frame = ttk.LabelFrame(content_frame, text=display_name, padding=10)

            group_frame.pack(fill=tk.X, padx=10, pady=5)

            profs = PROFESSIONS.get(cat_key, {})

            lvl5 = {k: v for k, v in profs.items() if v[2] == 5}

            lvl10 = {k: v for k, v in profs.items() if v[2] == 10}

            for p5_id, p5_info in lvl5.items():

                row_frame = ttk.Frame(group_frame)

                row_frame.pack(fill=tk.X, pady=5)

                p5_name, p5_desc, _, _ = p5_info
                display_p5_name = translate_profession_name(p5_name)
                display_p5_desc = translate_profession_desc(p5_name, p5_desc)

                var5 = tk.BooleanVar(value=(p5_id in self.result))

                self.check_vars[p5_id] = var5

                current_lvl = self.player_levels.get(cat_key, 0)

                state5 = tk.NORMAL if current_lvl >= 5 else tk.DISABLED

                lvl5_text = f"{tr.translate('level_5_prefix')}{display_p5_name}"

                cb5 = ttk.Checkbutton(row_frame, text=lvl5_text, variable=var5, state=state5,

                                      command=lambda pid=p5_id: self.update_profession_state(pid))

                cb5.pack(side=tk.LEFT, padx=(0, 20))

                self._add_tip(cb5, display_p5_desc)

                p10_frame = ttk.Frame(row_frame)

                p10_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

                related_p10 = {k: v for k, v in lvl10.items() if v[3] == p5_id}

                for p10_id, p10_info in related_p10.items():

                    p10_name, p10_desc, _, _ = p10_info
                    display_p10_name = translate_profession_name(p10_name)
                    display_p10_desc = translate_profession_desc(p10_name, p10_desc)

                    var10 = tk.BooleanVar(value=(p10_id in self.result))

                    self.check_vars[p10_id] = var10

                    state10 = tk.NORMAL if current_lvl >= 10 else tk.DISABLED

                    lvl10_text = f"{tr.translate('level_10_prefix')}{display_p10_name}"

                    cb10 = ttk.Checkbutton(p10_frame, text=lvl10_text, variable=var10, state=state10,

                                           command=lambda pid=p10_id: self.update_profession_state(pid))

                    cb10.pack(side=tk.LEFT, padx=10)

                    self._add_tip(cb10, display_p10_desc)

        btn_frame = ttk.Frame(content_frame, padding=10)

        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(btn_frame, text=tr.translate("confirm_modify"), command=self.on_ok, width=20).pack(pady=10)

    # Update the profession state.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def update_profession_state(self, changed_id):

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

                for other_id, other_info in category.items():

                    if other_id != changed_id and other_info[2] == 5 and self.check_vars.get(other_id) and self.check_vars[other_id].get():

                        self.check_vars[other_id].set(False)

                        for child_id, child_info in category.items():

                            if child_info[3] == other_id:

                                if self.check_vars.get(child_id):

                                    self.check_vars[child_id].set(False)

            else:

                for child_id, child_info in category.items():

                    if child_info[3] == changed_id:

                        if self.check_vars.get(child_id):

                            self.check_vars[child_id].set(False)

        elif level == 10:

            if is_checked:

                if parent_id is not None and self.check_vars.get(parent_id) and not self.check_vars[parent_id].get():

                    self.check_vars[parent_id].set(True)

                    self.update_profession_state(parent_id)

                for other_id, other_info in category.items():

                    if other_id != changed_id and other_info[2] == 10 and other_info[3] == parent_id and self.check_vars.get(other_id) and self.check_vars[other_id].get():

                        self.check_vars[other_id].set(False)

            else:

                pass

    # Bind a lightweight tooltip to the provided widget.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _add_tip(self, widget, text):

        # Show the hovered profession description in the help label.
        # It keeps dialog widgets and returned values synchronized during the modal workflow.
        def on_enter(e):

            self.tip_label.config(text=f"{tr.translate('description')}: {text}")

        # Restore the default profession help text when the pointer leaves.
        # It keeps dialog widgets and returned values synchronized during the modal workflow.
        def on_leave(e):

            self.tip_label.config(text="Hover over a profession for description.")

        widget.bind("<Enter>", on_enter)

        widget.bind("<Leave>", on_leave)

    # Return the dialog's tip label.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    @property

    def tip_label(self):

        if not hasattr(self, "_tip_label"):

            self._tip_label = ttk.Label(self, text=tr.translate("hover_tip"), foreground="gray", font=("", 9), wraplength=650)

            self._tip_label.pack(side=tk.BOTTOM, pady=(0, 10), padx=20)

        return self._tip_label

    # Validate the current inputs, store the dialog result, and close the window.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def on_ok(self):

        known_ids = set(self.check_vars.keys())

        new_result = [p_id for p_id in self.result if p_id not in known_ids]

        new_result.extend([p_id for p_id, var in self.check_vars.items() if var.get()])

        self.result = new_result

        self.destroy()

# Manage a modal dialog that collects a focused set of values from the user.
# It keeps dialog widgets and returned values synchronized during the modal workflow.
class ChestDialog(ttkb.Toplevel):

    def __init__(self, parent, chest_data):

        super().__init__(parent)

        location_name = chest_data.get("display_location") or translate_location_name(chest_data["location"])
        title = f"{tr.translate('modify_chest')} - {location_name}"

        self.title(title)

        center_window(self, 400, 350)

        self.result = None

        self.chest_data = chest_data

        self.model = chest_data['model']

        self.transient(parent)

        self.grab_set()

        main_frame = ttk.Frame(self, padding=20)

        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text=tr.translate("chest_capacity")).grid(row=0, column=0, sticky=tk.W, pady=5)

        self.cap_var = tk.StringVar(value=str(self.model.capacity))

        bind_numeric_input_limit(self.cap_var, min_value=1)

        ttk.Entry(main_frame, textvariable=self.cap_var, width=15).grid(row=0, column=1, sticky=tk.W, pady=5)

        ttk.Label(main_frame, text=tr.translate("special_type")).grid(row=1, column=0, sticky=tk.W, pady=5)

        self.type_var = tk.StringVar(value=self.model.specialChestType or "None")

        types = ["None", "BigChest", "JunimoChest", "StoneChest", "MiniShippingBin"]

        display_types = {t: tr.translate(f"chest_type_{t.lower()}") for t in types}

        self.rev_display_types = {v: k for k, v in display_types.items()}

        ttk.Combobox(main_frame, textvariable=self.type_var, values=list(display_types.values()), width=13).grid(row=1, column=1, sticky=tk.W, pady=5)

        ttk.Label(main_frame, text=tr.translate("global_inventory_id")).grid(row=2, column=0, sticky=tk.W, pady=5)

        self.gid_var = tk.StringVar(value=self.model.globalInventoryId or "")

        ttk.Entry(main_frame, textvariable=self.gid_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5)

        ttk.Label(main_frame, text=tr.translate("color_rgb")).grid(row=3, column=0, sticky=tk.W, pady=5)

        color = self.model.playerChoiceColor or {"R": 0, "G": 0, "B": 0}

        self.color_var = tk.StringVar(value=f"{color['R']},{color['G']},{color['B']}")

        color_input_frame = ttk.Frame(main_frame)

        color_input_frame.grid(row=3, column=1, sticky=tk.W, pady=5)

        color_entry = ttk.Entry(color_input_frame, textvariable=self.color_var, width=15)

        color_entry.pack(side=tk.LEFT)

        self.color_preview = tk.Canvas(color_input_frame, width=20, height=20, highlightthickness=1, highlightbackground="gray")

        self.color_preview.pack(side=tk.LEFT, padx=5)

        # Update the preview.
        # It keeps dialog widgets and returned values synchronized during the modal workflow.
        def update_preview(*args):

            try:

                rgb = self.color_var.get().split(",")

                if len(rgb) == 3:

                    r, g, b = map(int, rgb)

                    r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))

                    hex_color = f'#{r:02x}{g:02x}{b:02x}'

                    self.color_preview.config(bg=hex_color)

            except:

                self.color_preview.config(bg="white")

        self.color_var.trace_add("write", update_preview)

        update_preview()

        # Choose the color.
        # It keeps dialog widgets and returned values synchronized during the modal workflow.
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

    # Validate the current inputs, store the dialog result, and close the window.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def on_ok(self):

        try:

            cap = int(self.cap_var.get())

            self.model.capacity = cap

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

# Manage a modal dialog that collects a focused set of values from the user.
# It keeps dialog widgets and returned values synchronized during the modal workflow.
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

        self.XP_LEVELS = [0, 100, 380, 770, 1300, 2150, 3300, 4800, 6900, 10000, 15000]

        for i, label in enumerate(labels):

            row, col = divmod(i, 2)

            f = ttk.LabelFrame(grid_frame, text=label, padding=10)

            f.grid(row=row, column=col, padx=10, pady=10, sticky=tk.NSEW)

            entry_var = exp_vars[i]

            entry = ttk.Entry(f, textvariable=entry_var, width=12)

            entry.pack(side=tk.LEFT, padx=5)

            if hasattr(parent, "add_tooltip"):

                parent.add_tooltip(entry, tr.translate("exp_max_tip"))

            level_label = ttk.Label(f, text=f"{tr.translate('level')}: 0", foreground="blue")

            level_label.pack(side=tk.LEFT, padx=5)

            # Update the level.
            # It keeps dialog widgets and returned values synchronized during the modal workflow.
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

            update_level(None)

        grid_frame.columnconfigure(0, weight=1)

        grid_frame.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(main_frame)

        btn_frame.pack(side=tk.BOTTOM, pady=10)

        ttk.Button(btn_frame, text=tr.translate("max_level_btn"), command=lambda: self.max_all(exp_vars)).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text=tr.translate("confirm"), command=self.destroy, width=15).pack(side=tk.LEFT, padx=5)

    # Set every editable field in the dialog to its maximum supported value.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def max_all(self, exp_vars):

        if messagebox.askyesno(tr.translate("confirm"), tr.translate("confirm_max_exp")):

            for var in exp_vars:

                var.set("15000")

            messagebox.showinfo(tr.translate("tip"), tr.translate("max_exp_success_tip"))

# Manage a modal dialog that collects a focused set of values from the user.
# It keeps dialog widgets and returned values synchronized during the modal workflow.
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

    # Create the recipe tab.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
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

        setup_mousewheel(canvas)

        recipe_status = recipes_proxy.get_recipes_status()

        recipe_vars = {}

        sorted_names = sorted(recipe_status.keys(), key=lambda n: (recipe_status[n] is None, n))

        items = []

        for name in sorted_names:

            row_f = ttk.Frame(scrollable_frame)

            row_f.pack(fill=tk.X, padx=5, pady=2)

            is_unlocked = recipe_status[name] is not None

            var = tk.BooleanVar(value=is_unlocked)

            recipe_vars[name] = var

            display_name = translate_item_name(name, tr.translate(f"recipe_{name.lower().replace(' ', '_')}", name))

            cb = ttk.Checkbutton(row_f, text=display_name, variable=var,

                                 command=lambda n=name, v=var, p=recipes_proxy: self._on_recipe_toggle(p, n, v))

            cb.pack(side=tk.LEFT)

            craft_count_text = f"({tr.translate('craft_count_prefix')}: {recipe_status[name] or 0})"

            count_label = ttk.Label(row_f, text=craft_count_text, foreground="gray")

            count_label.pack(side=tk.LEFT, padx=10)

            items.append((row_f, name, display_name))

        # Filter the visible recipe rows by the current search text.
        # It keeps dialog widgets and returned values synchronized during the modal workflow.
        def on_search(*args):

            term = search_var.get().lower()

            for row_f, name, display_name in items:

                if term in name.lower() or term in display_name.lower():

                    row_f.pack(fill=tk.X, padx=5, pady=2)

                else:

                    row_f.pack_forget()

        search_var.trace("w", on_search)

        return frame

    # Update the recipe selection state after the current checkbox changes.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _on_recipe_toggle(self, recipes_proxy, name, var):

        if var.get():

            recipes_proxy.set_recipe_status(name, 0)

        else:

            recipes_proxy.set_recipe_status(name, None)

# Manage a modal dialog that collects a focused set of values from the user.
# It keeps dialog widgets and returned values synchronized during the modal workflow.
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

        search_frame = ttk.Frame(main_frame)

        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text=tr.translate('search_npc')).pack(side=tk.LEFT)

        self.search_var = tk.StringVar()

        self.search_var.trace_add("write", self.refresh_list)

        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

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

        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))

        setup_mousewheel(canvas)

        self.refresh_list()

        btn_frame = ttk.Frame(main_frame, padding=10)

        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(btn_frame, text=tr.translate("close"), command=self.destroy).pack()

    # Refresh the list.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def refresh_list(self, *args):

        for widget in self.scrollable_frame.winfo_children():

            widget.destroy()

        search_term = self.search_var.get().lower()

        sorted_names = sorted(self.friendship_data.keys())

        for name in sorted_names:

            display_name = translate_npc_name(name)

            if search_term and search_term not in name.lower() and search_term not in display_name.lower():

                continue

            data = self.friendship_data[name]

            f = ttk.Frame(self.scrollable_frame, padding=5)

            f.pack(fill=tk.X)

            ttk.Label(f, text=display_name, width=15).pack(side=tk.LEFT)

            ttk.Entry(f, textvariable=data["points"], width=8).pack(side=tk.LEFT, padx=5)

            heart_label = ttk.Label(f, foreground="red")

            heart_label.pack(side=tk.LEFT, padx=5)

            # Update the hearts.
            # It keeps dialog widgets and returned values synchronized during the modal workflow.
            def update_hearts(var, index, mode, label=heart_label, points_var=data["points"]):

                if not label.winfo_exists():

                    return

                try:

                    p = int(points_var.get())

                    h = p // 250

                    label.config(text=f"{tr.translate('hearts_prefix')}{h}")

                except:

                    label.config(text=f"{tr.translate('hearts_prefix')}0")

            update_hearts(None, None, None)

            if "trace_id" in data:

                try:

                    data["points"].trace_remove("write", data["trace_id"])

                except:

                    pass

            data["trace_id"] = data["points"].trace_add("write", update_hearts)

# Manage a modal dialog that collects a focused set of values from the user.
# It keeps dialog widgets and returned values synchronized during the modal workflow.
class BundlesDialog(ttkb.Toplevel):

    def __init__(self, parent, bundles_manager):

        super().__init__(parent)

        self.title(tr.translate('community_center_bundles'))

        center_window(self, 600, 700)

        self.bundles_manager = bundles_manager

        self.transient(parent)

        self.grab_set()

        main_frame = ttk.Frame(self, padding=10)

        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame)

        top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(top_frame, text=tr.translate('complete_all_bundles'), command=self.complete_all).pack(side=tk.LEFT)

        ttk.Label(top_frame, text=f" ({tr.translate('save_hint')})", foreground="gray").pack(side=tk.LEFT)

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

        setup_mousewheel(canvas)

        self.refresh_list()

        btn_frame = ttk.Frame(main_frame, padding=10)

        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(btn_frame, text=tr.translate("close"), command=self.destroy).pack()

    # Refresh the list.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def refresh_list(self):

        for widget in self.scrollable_frame.winfo_children():

            widget.destroy()

        rooms = self.bundles_manager.get_bundles_by_room()

        for room_name, bundles in rooms.items():

            display_room_name = translate_room_name(room_name)

            room_frame = ttk.LabelFrame(self.scrollable_frame, text=f"{tr.translate('room_prefix')}{display_room_name}", padding=5)

            room_frame.pack(fill=tk.X, pady=5, padx=5)

            for bundle in bundles:

                bundle_f = ttk.Frame(room_frame)

                bundle_f.pack(fill=tk.X, pady=2)

                status_text = tr.translate("completed") if bundle.completed else tr.translate("in_progress")

                status_color = "green" if bundle.completed else "orange"

                ttk.Label(bundle_f, text=translate_bundle_name(bundle.name), width=28, anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

                ttk.Label(bundle_f, text=status_text, foreground=status_color, width=12).pack(side=tk.LEFT, padx=5)

                ttk.Button(

                    bundle_f,

                    text=tr.translate("fill_bundle"),

                    command=lambda b=bundle: self.fill_bundle(b),

                ).pack(side=tk.RIGHT)

    # Fill a single bundle and refresh the view.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def fill_bundle(self, bundle):

        bundle.complete_all()

        self.refresh_list()

        messagebox.showinfo(
            tr.translate("success"),
            tr.translate("bundle_completed_msg").format(name=translate_bundle_name(bundle.name)),
        )

    # Fill all bundles after the user confirms the action.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def complete_all(self):

        if not messagebox.askyesno(tr.translate("confirm"), tr.translate("confirm_complete_all_bundles")):

            return

        for bundle in self.bundles_manager.bundles:

            bundle.complete_all()

        self.refresh_list()

        messagebox.showinfo(tr.translate("success"), tr.translate("all_bundles_filled_success"))

# Manage a modal dialog that collects a focused set of values from the user.
# It keeps dialog widgets and returned values synchronized during the modal workflow.
class SpecialPowersDialog(ttkb.Toplevel):

    def __init__(self, parent, player_model):

        super().__init__(parent)

        self.title(tr.translate("special_powers_and_achievements"))

        center_window(self, 800, 900)

        self.player = player_model

        self.transient(parent)

        self.grab_set()

        main_frame = ttk.Frame(self, padding=10)

        main_frame.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(main_frame)

        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        wallet_tab = ttk.Frame(notebook, padding=10)

        notebook.add(wallet_tab, text=tr.translate("wallet_items"))

        wallet_canvas = tk.Canvas(wallet_tab)

        wallet_scroll = ttk.Scrollbar(wallet_tab, orient="vertical", command=wallet_canvas.yview)

        self.wallet_frame = ttk.Frame(wallet_canvas)

        self.wallet_frame.bind("<Configure>", lambda e: wallet_canvas.configure(scrollregion=wallet_canvas.bbox("all")))

        wallet_canvas_window = wallet_canvas.create_window((0, 0), window=self.wallet_frame, anchor="nw")

        wallet_canvas.bind("<Configure>", lambda e: wallet_canvas.itemconfig(wallet_canvas_window, width=e.width))

        wallet_canvas.configure(yscrollcommand=wallet_scroll.set)

        wallet_scroll.pack(side="right", fill="y")

        wallet_canvas.pack(side="left", fill="both", expand=True)

        setup_mousewheel(wallet_canvas)

        mail_tab = ttk.Frame(notebook, padding=10)

        notebook.add(mail_tab, text=tr.translate("mail_flags"))

        mail_canvas = tk.Canvas(mail_tab)

        mail_scroll = ttk.Scrollbar(mail_tab, orient="vertical", command=mail_canvas.yview)

        self.mail_frame = ttk.Frame(mail_canvas)

        self.mail_frame.bind("<Configure>", lambda e: mail_canvas.configure(scrollregion=mail_canvas.bbox("all")))

        mail_canvas_window = mail_canvas.create_window((0, 0), window=self.mail_frame, anchor="nw")

        mail_canvas.bind("<Configure>", lambda e: mail_canvas.itemconfig(mail_canvas_window, width=e.width))

        mail_canvas.configure(yscrollcommand=mail_scroll.set)

        mail_scroll.pack(side="right", fill="y")

        mail_canvas.pack(side="left", fill="both", expand=True)

        setup_mousewheel(mail_canvas)

        ach_tab = ttk.Frame(notebook, padding=10)

        notebook.add(ach_tab, text=tr.translate("achievements"))

        ach_canvas = tk.Canvas(ach_tab)

        ach_scroll = ttk.Scrollbar(ach_tab, orient="vertical", command=ach_canvas.yview)

        self.ach_frame = ttk.Frame(ach_canvas)

        self.ach_frame.bind("<Configure>", lambda e: ach_canvas.configure(scrollregion=ach_canvas.bbox("all")))

        ach_canvas_window = ach_canvas.create_window((0, 0), window=self.ach_frame, anchor="nw")

        ach_canvas.bind("<Configure>", lambda e: ach_canvas.itemconfig(ach_canvas_window, width=e.width))

        ach_canvas.configure(yscrollcommand=ach_scroll.set)

        ach_scroll.pack(side="right", fill="y")

        ach_canvas.pack(side="left", fill="both", expand=True)

        setup_mousewheel(ach_canvas)

        self.refresh_wallet()

        self.refresh_mail_flags()

        self.refresh_achievements()

        btn_frame = ttk.Frame(main_frame)

        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        ttk.Button(btn_frame, text=tr.translate("close"), command=self.destroy).pack()

    # Refresh the wallet.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def refresh_wallet(self):

        for widget in self.wallet_frame.winfo_children():

            widget.destroy()

        for item in WALLET_ITEMS:

            f = ttk.Frame(self.wallet_frame, padding=5)

            f.pack(fill=tk.X)

            has_item = self.player.has_mail(item["id"])

            status_text = tr.translate("unlocked") if has_item else tr.translate("locked")

            status_color = "green" if has_item else "red"

            icon = item.get("icon", "📦")

            item_name, item_desc = translate_special_powers_entry(item)

            ttk.Label(f, text=f"{icon} {item_name}", width=35, font=("", 10, "bold")).pack(side=tk.LEFT)

            ttk.Label(f, text=status_text, foreground=status_color, width=10).pack(side=tk.LEFT)

            # Toggle the item.
            # It keeps dialog widgets and returned values synchronized during the modal workflow.
            def toggle_item(i=item, current=has_item):

                if current:

                    self.player.remove_mail(i["id"])

                else:

                    self.player.add_mail(i["id"])

                self.refresh_wallet()

            btn_text = tr.translate("remove") if has_item else tr.translate("add")

            ttk.Button(f, text=btn_text, command=toggle_item).pack(side=tk.RIGHT)

            ttk.Label(self.wallet_frame, text=item_desc, foreground="gray", font=("", 8)).pack(fill=tk.X, padx=(10, 0), pady=(0, 5))

    # Refresh the mail flags.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def refresh_mail_flags(self):

        for widget in self.mail_frame.winfo_children():

            widget.destroy()

        search_frame = ttk.Frame(self.mail_frame)

        search_frame.pack(fill=tk.X, pady=(0, 10))

        search_var = tk.StringVar()

        search_entry = ttk.Entry(search_frame, textvariable=search_var)

        search_entry.pack(fill=tk.X)

        search_entry.insert(0, tr.translate("search_placeholder"))

        # Filter the visible mail flags by the current search text.
        # It keeps dialog widgets and returned values synchronized during the modal workflow.
        def on_search_change(*args):

            self._filter_mail_flags(search_var.get())

        search_var.trace_add("write", on_search_change)

        self.mail_flags_container = ttk.Frame(self.mail_frame)

        self.mail_flags_container.pack(fill=tk.BOTH, expand=True)

        self._all_mail_flags = MAIL_FLAGS

        self._filter_mail_flags("")

    # Filter the mail flags.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _filter_mail_flags(self, search_text):

        for widget in self.mail_flags_container.winfo_children():

            widget.destroy()

        search_text = search_text.lower()

        filtered = [
            flag
            for flag in self._all_mail_flags
            if search_text in flag.lower() or search_text in translate_mail_flag(flag).lower()
        ]

        grouped_flags = {category: [] for category in get_mail_flag_category_order()}

        for flag in filtered:

            grouped_flags.setdefault(get_mail_flag_category(flag), []).append(flag)

        for category in get_mail_flag_category_order():

            flags = grouped_flags.get(category, [])

            if not flags:

                continue

            section = ttk.LabelFrame(
                self.mail_flags_container,
                text=f"{get_mail_flag_category_label(category)} ({len(flags)})",
                padding=6,
            )

            section.pack(fill=tk.X, expand=True, pady=(0, 8))

            for flag in flags:

                f = ttk.Frame(section, padding=3)

                f.pack(fill=tk.X)

                has_flag = self.player.has_mail(flag)

                cb_var = tk.BooleanVar(value=has_flag)

                # Toggle the selected mail flag for the player.
                # It keeps dialog widgets and returned values synchronized during the modal workflow.
                def toggle_flag(f=flag, var=cb_var):

                    if var.get():

                        self.player.add_mail(f)

                    else:

                        self.player.remove_mail(f)

                display_flag = translate_mail_flag(flag)

                checkbox_text = f"{display_flag} [{flag}]" if display_flag != flag else flag

                cb = ttk.Checkbutton(f, text=checkbox_text, variable=cb_var, command=toggle_flag)

                cb.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # Refresh the achievements.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def refresh_achievements(self):

        for widget in self.ach_frame.winfo_children():

            widget.destroy()

        for ach in ACHIEVEMENTS:

            f = ttk.Frame(self.ach_frame, padding=5)

            f.pack(fill=tk.X)

            has_ach = self.player.has_achievement(ach["id"])

            status_text = tr.translate("unlocked") if has_ach else tr.translate("locked")

            status_color = "green" if has_ach else "red"

            ach_name, ach_desc = translate_special_powers_entry(ach)

            ttk.Label(f, text=ach_name, width=25, font=("", 10, "bold")).pack(side=tk.LEFT)

            ttk.Label(f, text=status_text, foreground=status_color, width=10).pack(side=tk.LEFT)

            # Toggle the achievement state for the selected row.
            # It keeps dialog widgets and returned values synchronized during the modal workflow.
            def toggle_ach(aid=ach["id"], current=has_ach):

                if current:

                    self.player.remove_achievement(aid)

                else:

                    self.player.add_achievement(aid)

                self.refresh_achievements()

            btn_text = tr.translate("remove") if has_ach else tr.translate("unlock")

            ttk.Button(f, text=btn_text, command=toggle_ach).pack(side=tk.RIGHT)

            ttk.Label(self.ach_frame, text=ach_desc, foreground="gray", font=("", 8)).pack(fill=tk.X, padx=(10, 0), pady=(0, 5))

# Manage a modal dialog that collects a focused set of values from the user.
# It keeps dialog widgets and returned values synchronized during the modal workflow.
class AppearanceDialog(ttkb.Toplevel):

    def __init__(self, parent, player_model):

        super().__init__(parent)

        self.title(tr.translate("appearance_editor"))

        center_window(self, 500, 600)

        self.player = player_model

        self.result = None

        self.transient(parent)

        self.grab_set()

        main_frame = ttk.Frame(self, padding=20)

        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)

        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right_frame = ttk.Frame(main_frame)

        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._create_basic_fields(left_frame)

        self._create_color_fields(right_frame)

        btn_frame = ttk.Frame(main_frame)

        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        ttk.Button(btn_frame, text=tr.translate("confirm"), command=self.on_ok, width=15).pack(side=tk.LEFT, padx=10)

        ttk.Button(btn_frame, text=tr.translate("cancel"), command=self.destroy, width=15).pack(side=tk.LEFT, padx=10)

    # Create the basic fields.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _create_basic_fields(self, parent):

        text_fields = [

            (tr.translate("name"), "name"),

            (tr.translate("farm_name"), "farmName"),

            (tr.translate("favorite_thing"), "favoriteThing"),

        ]

        for label_text, attr in text_fields:

            f = ttk.Frame(parent)

            f.pack(fill=tk.X, pady=5)

            ttk.Label(f, text=label_text, width=15).pack(side=tk.LEFT)

            var = tk.StringVar(value=getattr(self.player, attr, ""))

            entry = ttk.Entry(f, textvariable=var, width=20)

            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            setattr(self, f"{attr}_var", var)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, pady=15)

        gender_frame = ttk.LabelFrame(parent, text=tr.translate("gender"), padding=10)

        gender_frame.pack(fill=tk.X, pady=5)

        current_gender = self.player.gender

        self.gender_var = tk.StringVar(value="Male" if current_gender == "0" else "Female")

        ttk.Radiobutton(gender_frame, text="🚹 Male", variable=self.gender_var, value="Male").pack(side=tk.LEFT, padx=20)

        ttk.Radiobutton(gender_frame, text="🚺 Female", variable=self.gender_var, value="Female").pack(side=tk.LEFT, padx=20)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, pady=15)

        number_fields = [

            (tr.translate("skin"), "skin", 0, 23),

            (tr.translate("hairstyle"), "hairstyle", 0, 73),

            (tr.translate("accessory"), "accessory", -1, 29),

        ]

        for label_text, attr, min_val, max_val in number_fields:

            f = ttk.Frame(parent)

            f.pack(fill=tk.X, pady=5)

            ttk.Label(f, text=label_text, width=15).pack(side=tk.LEFT)

            current_val = getattr(self.player, attr, 0)

            var = tk.StringVar(value=str(current_val))

            bind_numeric_input_limit(

                var,

                max_value=max_val,

                min_value=min_val,

                allow_negative=(min_val < 0)

            )

            entry = ttk.Entry(f, textvariable=var, width=8)

            entry.pack(side=tk.LEFT)

            ttk.Label(f, text=f"({min_val}-{max_val})", foreground="gray").pack(side=tk.LEFT, padx=5)

            setattr(self, f"{attr}_var", var)

            if attr == "skin":

                self._create_skin_preview(f)

    # Create the skin preview.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _create_skin_preview(self, parent):

        self.skin_preview = tk.Canvas(parent, width=30, height=20, highlightthickness=1, highlightbackground="gray")

        self.skin_preview.pack(side=tk.LEFT, padx=10)

        self._update_skin_preview()

        # Refresh the skin preview when the selected skin index changes.
        # It keeps dialog widgets and returned values synchronized during the modal workflow.
        def on_skin_change(*args):

            self._update_skin_preview()

        self.skin_var.trace_add("write", on_skin_change)

    # Update the skin preview.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _update_skin_preview(self):

        try:

            skin_idx = int(self.skin_var.get())

            from models.appearance_data import get_skin_colors, rgb_to_hex

            colors = get_skin_colors(skin_idx)

            if colors:

                hex_color = rgb_to_hex(*colors['primary'])

                self.skin_preview.config(bg=hex_color)

            else:

                self.skin_preview.config(bg="white")

        except:

            self.skin_preview.config(bg="white")

    # Create the color fields.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _create_color_fields(self, parent):

        color_fields = [

            (tr.translate("hair_color"), "hairColor"),

            (tr.translate("eye_color"), "eyeColor"),

        ]

        ttk.Label(parent, text=tr.translate("colors"), font=("", 10, "bold")).pack(pady=(0, 10))

        self.color_previews = {}

        self.color_vars = {}

        for label_text, attr in color_fields:

            f = ttk.Frame(parent)

            f.pack(fill=tk.X, pady=8)

            ttk.Label(f, text=label_text, width=12).pack(side=tk.LEFT)

            current_color = getattr(self.player, attr, (0, 0, 0, 255))

            r, g, b = current_color[0], current_color[1], current_color[2]

            preview = tk.Canvas(f, width=25, height=25, highlightthickness=1, highlightbackground="gray")

            preview.pack(side=tk.LEFT, padx=5)

            hex_color = f'#{r:02x}{g:02x}{b:02x}'

            preview.config(bg=hex_color)

            self.color_previews[attr] = preview

            var = tk.StringVar(value=f"{r},{g},{b}")

            self.color_vars[attr] = var

            btn = ttk.Button(f, text="🎨", width=3,

                           command=lambda a=attr, p=preview, v=var: self._choose_color(a, p, v))

            btn.pack(side=tk.LEFT, padx=5)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, pady=15)

        self._create_presets_section(parent)

    # Create the presets section.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _create_presets_section(self, parent):

        ttk.Label(parent, text=tr.translate("skin_presets"), font=("", 10, "bold")).pack(pady=(0, 10))

        presets_frame = ttk.Frame(parent)

        presets_frame.pack(fill=tk.X)

        from models.appearance_data import CHARACTER_COLORS, rgb_to_hex

        for i, (r, g, b) in enumerate(CHARACTER_COLORS['primary_skin']):

            btn_frame = ttk.Frame(presets_frame)

            btn_frame.grid(row=i // 6, column=i % 6, padx=2, pady=2)

            hex_color = rgb_to_hex(r, g, b)

            btn = tk.Button(btn_frame, bg=hex_color, width=3, height=1,

                          command=lambda idx=i: self._apply_skin_preset(idx))

            btn.pack()

    # Choose the color.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _choose_color(self, attr, preview, var):

        current = var.get()

        initial_color = "#ffffff"

        try:

            parts = current.split(",")

            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])

            initial_color = f'#{r:02x}{g:02x}{b:02x}'

        except:

            pass

        cd = ColorChooserDialog(initialcolor=initial_color, title=tr.translate("choose_color"), parent=self)

        cd.show()

        if cd.result:

            r, g, b = map(int, cd.result.rgb)

            var.set(f"{r},{g},{b}")

            hex_color = f'#{r:02x}{g:02x}{b:02x}'

            preview.config(bg=hex_color)

    # Apply the skin preset.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _apply_skin_preset(self, idx):

        self.skin_var.set(str(idx))

    # Validate the current inputs, store the dialog result, and close the window.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def on_ok(self):

        try:

            self.player.name = self.name_var.get()

            self.player.farmName = self.farmName_var.get()

            self.player.favoriteThing = self.favorite_thing_var.get()

            gender_val = "0" if self.gender_var.get() == "Male" else "1"

            self.player.gender = gender_val

            self.player.skin = int(self.skin_var.get())

            self.player.hairstyle = int(self.hairstyle_var.get())

            self.player.accessory = int(self.accessory_var.get())

            for attr in ["hairColor", "eyeColor"]:

                var = self.color_vars.get(attr)

                if var:

                    parts = var.get().split(",")

                    if len(parts) >= 3:

                        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])

                        setattr(self.player, attr, (r, g, b, 255))

            self.result = True

            self.destroy()

        except ValueError as e:

            messagebox.showerror(tr.translate("error"), tr.translate("invalid_input_format"))

# Manage a modal dialog that collects a focused set of values from the user.
# It keeps dialog widgets and returned values synchronized during the modal workflow.
class ModDialog(ttkb.Toplevel):

    def __init__(self, parent):

        super().__init__(parent)

        self.title(tr.translate("mod_manager"))

        center_window(self, 900, 700)

        self.transient(parent)

        self.grab_set()

        from models.mod_data import COMMON_MODS, get_mod_categories

        main_frame = ttk.Frame(self, padding=15)

        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text=tr.translate("mod_manager_title"),

                               font=("", 14, "bold"))

        title_label.pack(pady=(0, 10))

        desc_label = ttk.Label(main_frame, text=tr.translate("mod_manager_desc"),

                              foreground="gray", wraplength=800)

        desc_label.pack(pady=(0, 15))

        search_frame = ttk.Frame(main_frame)

        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text=tr.translate("search")).pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()

        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)

        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.search_var.trace_add("write", self._on_search_change)

        self.notebook = ttk.Notebook(main_frame)

        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.category_frames = {}

        self.mod_vars = {}

        category_names = {

            "quality_of_life": tr.translate("mod_cat_qol"),

            "visual": tr.translate("mod_cat_visual"),

            "gameplay": tr.translate("mod_cat_gameplay"),

            "farming": tr.translate("mod_cat_farming"),

            "inventory": tr.translate("mod_cat_inventory"),

            "fishing": tr.translate("mod_cat_fishing"),

            "mining_combat": tr.translate("mod_cat_combat"),

            "misc": tr.translate("mod_cat_misc"),

        }

        for cat_key, cat_name in category_names.items():

            if cat_key in COMMON_MODS:

                tab = ttk.Frame(self.notebook, padding=10)

                self.notebook.add(tab, text=cat_name)

                self._create_mod_list(tab, COMMON_MODS[cat_key], cat_key)

        btn_frame = ttk.Frame(main_frame)

        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text=tr.translate("mod_check_all"),

                  command=self._check_all, width=15).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text=tr.translate("mod_uncheck_all"),

                  command=self._uncheck_all, width=15).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text=tr.translate("mod_export_list"),

                  command=self._export_list, width=15).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text=tr.translate("close"),

                  command=self.destroy, width=15).pack(side=tk.RIGHT, padx=5)

        self._load_saved_config()

    # Create the mod list.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _create_mod_list(self, parent, mods, category):

        canvas = tk.Canvas(parent, highlightthickness=0)

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)

        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(

            "<Configure>",

            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))

        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=850)

        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")

        canvas.pack(side="left", fill="both", expand=True)

        setup_mousewheel(canvas)

        self.category_frames[category] = {

            'frame': scrollable_frame,

            'canvas': canvas,

            'mods': []

        }

        for mod in mods:

            mod_frame = ttk.Frame(scrollable_frame)

            mod_frame.pack(fill=tk.X, pady=3, padx=5)

            var = tk.BooleanVar(value=False)

            self.mod_vars[mod['id']] = var

            cb = ttk.Checkbutton(mod_frame, variable=var)

            cb.pack(side=tk.LEFT)

            name_label = ttk.Label(mod_frame, text=mod['name'],

                                  font=("", 10, "bold"), width=30)

            name_label.pack(side=tk.LEFT, padx=(5, 10))

            desc_label = ttk.Label(mod_frame, text=mod['desc'],

                                  foreground="gray", wraplength=500)

            desc_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            self.category_frames[category]['mods'].append({

                'frame': mod_frame,

                'name': mod['name'].lower(),

                'desc': mod['desc'].lower(),

                'id': mod['id']

            })

    # Filter the visible mods by the current search text.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _on_search_change(self, *args):

        search_text = self.search_var.get().lower()

        for category, data in self.category_frames.items():

            for mod_info in data['mods']:

                if search_text in mod_info['name'] or search_text in mod_info['desc']:

                    mod_info['frame'].pack(fill=tk.X, pady=3, padx=5)

                else:

                    mod_info['frame'].pack_forget()

    # Select every option in the current list.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _check_all(self):

        for var in self.mod_vars.values():

            var.set(True)

    # Clear every option in the current list.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _uncheck_all(self):

        for var in self.mod_vars.values():

            var.set(False)

    # Export the list.
    # It keeps dialog widgets and returned values synchronized during the modal workflow.
    def _export_list(self):

        selected = [mod_id for mod_id, var in self.mod_vars.items() if var.get()]

        if not selected:

            messagebox.showinfo(tr.translate("info"), tr.translate("mod_no_selection"))

            return

        content = tr.translate("mod_list_header") + "\n"

        content += "=" * 50 + "\n\n"

        from models.mod_data import get_all_mods

        all_mods = {m['id']: m for m in get_all_mods()}

        for mod_id in selected:

            if mod_id in all_mods:

                mod = all_mods[mod_id]

                content += f"• {mod['name']}\n"

                content += f"  ID: {mod_id}\n"

                content += f"  {mod['desc']}\n\n"

        dialog = tk.Toplevel(self)

        dialog.title(tr.translate("mod_export_title"))

        dialog.geometry("600x500")

        dialog.transient(self)

        text_widget = tk.Text(dialog, wrap=tk.WORD, padx=10, pady=10)

        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_widget.insert("1.0", content)

        text_widget.config(state=tk.DISABLED)

        scrollbar = ttk.Scrollbar(text_widget, command=text_widget.yview)

        text_widget.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(dialog, text=tr.translate("close"), command=dialog.destroy).pack(pady=10)

    def _load_saved_config(self):

        pass
