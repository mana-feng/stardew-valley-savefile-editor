# Build the player page and wire editable player-focused widgets to save data.
import tkinter as tk

from tkinter import messagebox, ttk

from ttkbootstrap.dialogs.colorchooser import ColorChooserDialog

from models.item import Item

from utils import tr

from ..dialogs import (

    AddItemDialog,

    AppearanceDialog,

    ExperienceDialog,

    FriendshipDialog,

    ProfessionDialog,

    RecipeDialog,

    SpecialPowersDialog,

)

from ..helpers import bind_numeric_input_limit, setup_mousewheel

# Provide page-specific UI builders and behaviors that are mixed into the main editor window.
# It keeps tab-specific widgets synchronized with the current save model and editor state.
class PlayerPageMixin:

    # Build the player tab.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def build_player_tab(self, main_notebook):

        player_tab = ttk.Frame(main_notebook)

        main_notebook.add(player_tab, text=tr.translate("player_attrs_tab"))

        selector_frame = ttk.Frame(player_tab, padding=10)

        selector_frame.pack(fill=tk.X)

        ttk.Label(selector_frame, text=f"{tr.translate('current_editing_player')}:").pack(side=tk.LEFT)

        self.player_selector = ttk.Combobox(selector_frame, state="readonly", width=30)

        self.player_selector.pack(side=tk.LEFT, padx=5)

        self.player_selector.bind("<<ComboboxSelected>>", self.on_player_selected)

        scroll_container = ttk.Frame(player_tab)

        scroll_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas = tk.Canvas(scroll_container, highlightthickness=0)

        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)

        scrollable_frame = ttk.Frame(canvas)

        # Update the scrollregion.
        # It keeps tab-specific widgets synchronized with the current save model and editor state.
        def _update_scrollregion(event):

            canvas.configure(scrollregion=canvas.bbox("all"))

            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        scrollable_frame.bind("<Configure>", _update_scrollregion)

        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")

        canvas.pack(side="left", fill="both", expand=True)

        setup_mousewheel(canvas)

        categories = [

            ("basic_info", [

                ("player_name", "name", "entry"),

                ("gender", "gender", "combo_gender"),

                ("spouse", "spouse", "entry"),

                ("farm_name", "farmName", "entry"),

                ("pet_type", "catPerson", "combo_pet"),

                ("pet_breed", "whichPetBreed", "entry"),

                ("favorite_thing", "favoriteThing", "entry"),

                ("house_level", "houseUpgradeLevel", "entry"),

                ("days_until_upgrade", "daysUntilHouseUpgrade", "entry"),

                ("cave_choice", "caveChoice", "combo_cave"),

            ]),

            ("assets_progress", [

                ("current_money", "money", "entry"),

                ("total_money", "totalMoneyEarned", "entry"),

                ("qi_gems", "qiGems", "entry"),

                ("club_coins", "clubCoins", "entry"),

                ("mine_depth", "deepestMineLevel", "entry"),

                ("times_reached_mine_bottom", "timesReachedMineBottom", "entry"),

                ("golden_walnuts", "goldenWalnuts", "game_entry"),

            ]),

            ("stats_abilities", [

                ("stamina", "stamina", "entry"),

                ("max_stamina", "maxStamina", "entry"),

                ("health", "health", "entry"),

                ("max_health", "maxHealth", "entry"),

                ("inventory_size", "maxItems", "entry"),

                ("trash_can_level", "trashCanLevel", "entry"),

                ("magnetic_radius", "magneticRadius", "entry"),

                ("resilience", "resilience", "entry"),

                ("immunity", "immunity", "entry"),

                ("attack", "attack", "entry"),

                ("skill_experience", "btn_professions", "button"),

                ("friendship_management", "btn_friendship", "button"),

                ("recipe_management", "btn_recipes", "button"),

                ("special_powers_and_achievements", "btn_special_powers", "button"),

            ]),

            ("skill_levels", [

                ("farming_level", "farmingLevel", "entry"),

                ("fishing_level", "fishingLevel", "entry"),

                ("foraging_level", "foragingLevel", "entry"),

                ("mining_level", "miningLevel", "entry"),

                ("combat_level", "combatLevel", "entry"),

                ("luck_level", "luckLevel", "entry"),

                ("mastery_exp", "masteryExp", "entry"),

                ("skill_professions", "btn_skills", "button"),

            ]),

            ("appearance_custom", [

                ("edit_appearance", "btn_appearance", "button"),

                ("hairstyle", "hairstyle", "entry"),

                ("accessory", "accessory", "entry"),

                ("skin", "skin", "entry"),

                ("hair_color", "hairColor", "color"),

                ("eye_color", "eyeColor", "color"),

                ("pants_color", "pantsColor", "color"),

                ("facial_hair", "facialHair", "entry"),

            ]),

            ("equipment_slots", [

                ("hat", "hat", "entry"),

                ("shirt_item", "shirtItem", "entry"),

                ("pants_item", "pantsItem", "entry"),

                ("boots", "boots", "entry"),

                ("left_ring", "leftRing", "entry"),

                ("right_ring", "rightRing", "entry"),

                ("trinket_item", "trinketItem", "entry"),

            ]),

        ]

        for cat_key, fields in categories:

            cat_frame = ttk.LabelFrame(scrollable_frame, text=tr.translate(cat_key), padding=10)

            cat_frame.pack(fill=tk.X, padx=10, pady=5)

            for i, (label_key, attr, item_type) in enumerate(fields):

                row, col = divmod(i, 2)

                if label_key:

                    ttk.Label(cat_frame, text=tr.translate(label_key)).grid(row=row, column=col * 2, sticky=tk.W, pady=5, padx=(10, 5))

                if item_type == "entry":

                    if attr in self.equipment_map:

                        cb = ttk.Combobox(

                            cat_frame,

                            textvariable=self.player_fields[attr],

                            values=self.category_options.get(attr, []),

                            width=20,

                        )

                        cb.grid(row=row, column=col * 2 + 1, sticky=tk.W, pady=5)

                        cb.bind("<Double-1>", lambda e, a=attr: self.select_equipment_item(a))

                    else:

                        entry = ttk.Entry(cat_frame, textvariable=self.player_fields[attr], width=15)

                        entry.grid(row=row, column=col * 2 + 1, sticky=tk.W, pady=5)

                elif item_type == "combo_gender":

                    cb = ttk.Combobox(

                        cat_frame,

                        textvariable=self.player_fields[attr],

                        values=[tr.translate("male"), tr.translate("female")],

                        state="readonly",

                        width=12,

                    )

                    cb.grid(row=row, column=col * 2 + 1, sticky=tk.W, pady=5)

                elif item_type == "combo_pet":

                    cb = ttk.Combobox(

                        cat_frame,

                        textvariable=self.player_fields[attr],

                        values=self.get_pet_type_options(),

                        state="readonly",

                        width=12,

                    )

                    cb.grid(row=row, column=col * 2 + 1, sticky=tk.W, pady=5)

                elif item_type == "combo_cave":

                    cb = ttk.Combobox(

                        cat_frame,

                        textvariable=self.game_fields["caveChoice"],

                        values=self.get_cave_choice_options(),

                        state="readonly",

                        width=12,

                    )

                    cb.grid(row=row, column=col * 2 + 1, sticky=tk.W, pady=5)

                elif item_type == "game_entry":

                    entry = ttk.Entry(cat_frame, textvariable=self.game_fields[attr], width=15)

                    entry.grid(row=row, column=col * 2 + 1, sticky=tk.W, pady=5)

                elif item_type == "color":

                    color_frame = ttk.Frame(cat_frame)

                    color_frame.grid(row=row, column=col * 2 + 1, sticky=tk.W, pady=5)

                    preview = tk.Canvas(color_frame, width=20, height=20, bd=1, relief="solid", highlightthickness=0)

                    preview.pack(side=tk.LEFT, padx=(0, 5))

                    if not hasattr(self, "color_previews"):

                        self.color_previews = {}

                    self.color_previews[attr] = preview

                    btn = ttk.Button(

                        color_frame,

                        text=tr.translate("choose_color"),

                        width=12,

                        command=lambda a=attr, p=preview: self.choose_color(a, p),

                    )

                    btn.pack(side=tk.LEFT)

                elif item_type == "button":

                    btn_text = tr.translate(label_key)

                    cmd = lambda: None

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

                    elif attr == "btn_appearance":

                        cmd = self.show_appearance_window

                    ttk.Button(cat_frame, text=btn_text, command=cmd, width=18).grid(

                        row=row,

                        column=col * 2 + 1,

                        sticky=tk.W,

                        pady=5,

                    )

    # Load the player data.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def load_player_data(self, idx):

        if idx < 0 or idx >= len(self.all_players): return

        player_info = self.all_players[idx]

        player = player_info["model"]

        for attr, var in self.player_fields.items():

            if attr == "spouse":

                if player_info.get("role") == "host":

                    var.set(self.save_proxy.spouse or tr.translate("none"))

                else:

                    var.set(tr.translate("none"))

                continue

            if hasattr(player, attr):

                val = getattr(player, attr)

                if attr == "gender":

                    var.set(self.get_display_gender(val))

                elif attr == "catPerson":

                    var.set(self.get_display_pet_type(player.petType))

                elif attr in ["hairColor", "eyeColor", "pantsColor"]:

                    r, g, b, a = getattr(player, attr)

                    var.set(f"{r},{g},{b}")

                    if hasattr(self, "color_previews") and attr in self.color_previews:

                        hex_color = f'#{r:02x}{g:02x}{b:02x}'

                        self.color_previews[attr].config(bg=hex_color)

                elif isinstance(val, Item):

                    item_id = val.itemId or tr.translate("none")

                    if attr in self.equipment_map:

                        if item_id == tr.translate("none"):

                            var.set(tr.translate("none"))

                        else:

                            display_name = self.item_name_map.get(item_id)

                            if not display_name:

                                prefixed_id = val.prefixedId

                                if prefixed_id and prefixed_id in self.item_name_map:

                                    display_name = self.item_name_map[prefixed_id]

                                    item_id = prefixed_id

                            if not display_name:

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

        for attr, var in self.game_fields.items():

            if attr == "caveChoice":

                choice = self.save_proxy.playerChoiceFruitCave

                var.set(self.get_display_cave_choice(choice if choice is not None else "0"))

            elif attr == "currentSeason":

                var.set(self.get_display_season(self.save_proxy.currentSeason))

            elif attr == "weatherForTomorrow":

                weather_value = self.save_proxy.weatherForTomorrow or "Sun"

                self._ensure_weather_tomorrow_option(weather_value)

                if self.weather_tomorrow_cb is not None:

                    self.weather_tomorrow_cb["values"] = self.get_weather_tomorrow_options()

                var.set(self.get_display_weather_tomorrow(weather_value))

            elif attr == "stats/stepsTaken":

                var.set(str(self.save_proxy.stepsTaken))

            elif attr == "goldenWalnuts":

                var.set(str(self.save_proxy.goldenWalnuts))

            elif attr == "canCheat":

                val = self.save_proxy.canCheat

                var.set(val if isinstance(val, bool) else False)

            elif hasattr(self.save_proxy, attr):

                val = getattr(self.save_proxy, attr)

                var.set(str(val) if val is not None else "")

            else:

                val = self.save_proxy.get_text(attr)

                var.set(val if val is not None else "")

        for i, exp in enumerate(player.experiencePoints):

            if i < len(self.exp_vars):

                self.exp_vars[i].set(str(exp))

        self.professions_list = player.get_professions()

        self.friendship_data = {}

        for data in player.friendshipData:

            npc_name = data["name"]

            points_var = tk.StringVar(value=str(data["points"]))

            bind_numeric_input_limit(points_var, min_value=0)

            self.friendship_data[npc_name] = {

                "points": points_var

            }

        self.load_inventory_for_player(player)

        self.refresh_items_list()

    # Load the newly selected player into the player and inventory views.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def on_player_selected(self, event):

        idx = self.player_selector.current()

        if idx != -1:

            self.save_current_player_to_element()

            self.current_player_idx = idx

            self.load_player_data(idx)

    # Switch the editor language and refresh translated labels.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def change_language(self, event=None):

        new_lang = tr.resolve_language_code(self.language_var.get())

        if new_lang != tr.current_lang:

            tr.set_language(new_lang)

            for widget in self.root.winfo_children():

                widget.destroy()

            self.color_previews = {}

            self.setup_ui()

            self._auto_detect_game_path()

            if hasattr(self, "save_proxy"):

                self.refresh_save_list()

                self.status_var.set(tr.translate('language_changed'))

    # Choose the color.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def choose_color(self, attr, preview_canvas):

        current_rgb_str = self.player_fields[attr].get()

        initial_color = "#ffffff"

        if current_rgb_str:

            try:

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

    # Select the equipment item.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def select_equipment_item(self, attr):

        if not self.all_players:

            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save_first"))

            return

        player = self.all_players[self.current_player_idx]["model"]

        current_val = getattr(player, attr)

        initial_data = None

        if current_val and hasattr(current_val, "itemId"):

            raw_name = current_val.name or tr.translate("unknown")

            item_id = current_val.itemId or ""

            display_name = raw_name

            if item_id:

                mapped_name = self.item_name_map.get(item_id)

                if not mapped_name:

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

            display_val = f"({dialog.result['id']}) {dialog.result['name']}"

            self.player_fields[attr].set(display_val)

            setattr(player, attr, dialog.result["id"])

            if attr in ["shirtItem", "pantsItem"]:

                item_obj = getattr(player, attr)

                if item_obj:

                    item_obj.set_bool("dyed", False)

            messagebox.showinfo(tr.translate("selected_item"), f"{tr.translate('selected_item')}: {dialog.result['name']} (ID: {dialog.result['id']})")

    # Show the professions window.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def show_professions_window(self):

        if not self.save_file:

            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))

            return

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

    # Show the experience window.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def show_experience_window(self):

        if not self.save_file:

            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))

            return

        dialog = ExperienceDialog(self.root, self.exp_vars)

        self.root.wait_window(dialog)

        messagebox.showinfo(tr.translate("updated"), tr.translate("xp_updated"))

    # Show the friendship window.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
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

    # Show the recipes window.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def show_recipes_window(self):

        if not self.all_players:

            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))

            return

        player = self.all_players[self.current_player_idx]["model"]

        dialog = RecipeDialog(self.root, player)

        self.root.wait_window(dialog)

        messagebox.showinfo(tr.translate("updated"), tr.translate("recipes_updated"))

    # Show the special powers window.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def show_special_powers_window(self):

        if not self.all_players:

            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))

            return

        player = self.all_players[self.current_player_idx]["model"]

        dialog = SpecialPowersDialog(self.root, player)

        self.root.wait_window(dialog)

        messagebox.showinfo(tr.translate("updated"), tr.translate("special_powers_updated"))

    # Show the appearance window.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def show_appearance_window(self):

        if not self.all_players:

            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))

            return

        player = self.all_players[self.current_player_idx]["model"]

        dialog = AppearanceDialog(self.root, player)

        self.root.wait_window(dialog)

        if dialog.result:

            self.load_player_data(self.current_player_idx)
