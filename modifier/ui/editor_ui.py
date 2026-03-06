# Assemble the main editor window and coordinate state shared across all UI pages.
import os

import shutil

import sys

import tkinter as tk

from tkinter import filedialog, messagebox, ttk

import ttkbootstrap as ttkb

from ttkbootstrap.constants import PRIMARY, SECONDARY

from models.item_data import ITEM_CATEGORIES

from utils import tr

from utils.game_text_localization import (
    get_weather_tomorrow_options,
    parse_display_building_name,
    parse_display_weather_tomorrow,
    translate_weather_tomorrow,
)

from utils.item_localization import get_localized_item_name

from utils.game_path_detector import GamePathDetector

from utils.save_utils import list_save_folders

from utils.steam_helper import SteamHelper

from .dialogs import (

    AddItemDialog,

    AppearanceDialog,

    BundlesDialog,

    ChestDialog,

    ExperienceDialog,

    FriendshipDialog,

    ModDialog,

    ProfessionDialog,

    RecipeDialog,

    SpecialPowersDialog,

)

from .helpers import (
    bind_float_input_limit,

    bind_numeric_input_limit,

    center_window,

)

from .pages import ItemsPageMixin, ModsPageMixin, PlayerPageMixin, WorldPageMixin

# Define the stardew editor type used by this module.
# It coordinates shared editor state across multiple tabs, dialogs, and services.
class StardewEditor(WorldPageMixin, PlayerPageMixin, ItemsPageMixin, ModsPageMixin):

    # Ensure the english text exists or is ready.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    @staticmethod

    def _ensure_english_text(text, fallback=""):

        if not text:

            return fallback

        if any("\u4e00" <= ch <= "\u9fff" for ch in text):

            return fallback or ""

        return text

    # Ensure the weather tomorrow option exists or is ready.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def _ensure_weather_tomorrow_option(self, value):

        if not value:

            return

        display_value = translate_weather_tomorrow(value)

        if display_value not in self.weather_tomorrow_options:

            self.weather_tomorrow_options.append(display_value)

            if self.weather_tomorrow_cb is not None:

                self.weather_tomorrow_cb["values"] = self.weather_tomorrow_options

    # Return the default save path.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def get_default_save_path(self):

        return os.path.expandvars(r"%AppData%\StardewValley\Saves")

    # Return the translated language choices used by the toolbar selector.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def get_language_options(self):

        return [tr.get_language_label(code) for code in tr.get_available_languages()]

    # Return the translated display value for a season ID.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def get_display_season(self, value):

        return tr.translate((value or "spring").lower(), value or tr.translate("spring"))

    # Return the season ID for a translated display value.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def parse_display_season(self, value):

        mapping = {
            tr.translate("spring"): "spring",
            tr.translate("summer"): "summer",
            tr.translate("fall"): "fall",
            tr.translate("winter"): "winter",
        }

        return mapping.get(value, (value or "spring").lower())

    # Return the translated season choices used by combobox widgets.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def get_season_options(self):

        return [tr.translate("spring"), tr.translate("summer"), tr.translate("fall"), tr.translate("winter")]

    def get_display_weather_tomorrow(self, value):

        return translate_weather_tomorrow(value)

    def parse_display_weather_tomorrow(self, value):

        extra_values = [self.save_proxy.weatherForTomorrow] if getattr(self, "save_proxy", None) else []

        return parse_display_weather_tomorrow(value, extra_values=extra_values)

    def get_weather_tomorrow_options(self):

        extra_values = [self.save_proxy.weatherForTomorrow] if getattr(self, "save_proxy", None) else []

        return get_weather_tomorrow_options(extra_values=extra_values)

    # Return the translated display value for a gender.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def get_display_gender(self, value):

        return tr.translate("male") if str(value).lower() == "male" or str(value) == "0" else tr.translate("female")

    # Return the canonical gender value for a translated display value.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def parse_display_gender(self, value):

        return "Male" if value == tr.translate("male") else "Female"

    # Return the translated display value for a pet type.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def get_display_pet_type(self, value):

        mapping = {
            "Cat": tr.translate("cat"),
            "Dog": tr.translate("dog"),
            "Turtle": tr.translate("turtle"),
        }

        return mapping.get(value, tr.translate("cat"))

    # Return the canonical pet type for a translated display value.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def parse_display_pet_type(self, value):

        mapping = {
            tr.translate("cat"): "Cat",
            tr.translate("dog"): "Dog",
            tr.translate("turtle"): "Turtle",
        }

        return mapping.get(value, value or "Cat")

    # Return the translated pet type choices used by combobox widgets.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def get_pet_type_options(self):

        return [tr.translate("cat"), tr.translate("dog"), tr.translate("turtle")]

    # Return the translated display value for a cave choice ID.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def get_display_cave_choice(self, value):

        mapping = {
            "0": tr.translate("none"),
            "1": tr.translate("bat_cave"),
            "2": tr.translate("mushroom_cave"),
        }

        return mapping.get(str(value), tr.translate("none"))

    # Return the cave choice ID for a translated display value.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def parse_display_cave_choice(self, value):

        mapping = {
            tr.translate("none"): "0",
            tr.translate("bat_cave"): "1",
            tr.translate("mushroom_cave"): "2",
        }

        return mapping.get(value, "0")

    # Return the translated cave choice values used by combobox widgets.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def get_cave_choice_options(self):

        return [tr.translate("none"), tr.translate("bat_cave"), tr.translate("mushroom_cave")]

    def __init__(self, root):

        self.root = root

        self.root.title(tr.translate("app_title"))

        center_window(self.root, 1400, 900)

        self.root.minsize(1200, 800)

        try:

            icon_path = self.resource_path("F.png")

            if os.path.exists(icon_path):

                img = tk.PhotoImage(file=icon_path)

                self.root.iconphoto(True, img)

        except Exception:

            pass

        self.save_dir = ""

        self.parent_save_dir = ""

        self.available_saves = []

        self.save_file = ""

        self.info_file = "SaveGameInfo"

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

            "timesReachedMineBottom": tk.StringVar(),

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

            "skin": tk.StringVar(),

            "facialHair": tk.StringVar(),

            "hairColor": tk.StringVar(),

            "eyeColor": tk.StringVar(),

            "pantsColor": tk.StringVar(),

            "hat": tk.StringVar(),

            "shirtItem": tk.StringVar(),

            "pantsItem": tk.StringVar(),

            "boots": tk.StringVar(),

            "leftRing": tk.StringVar(),

            "rightRing": tk.StringVar(),

            "trinketItem": tk.StringVar(),

            "whichPetBreed": tk.StringVar(),

            "daysUntilHouseUpgrade": tk.StringVar()

        }

        self.all_players = []

        self.current_player_idx = 0

        self.exp_vars = [tk.StringVar() for _ in range(6)]

        self.professions_list = []

        self.friendship_data = {}

        self.game_fields = {

            "dailyLuck": tk.StringVar(),

            "goldenWalnuts": tk.StringVar(),

            "stats/stepsTaken": tk.StringVar(),

            "stats/daysPlayed": tk.StringVar(),

            "stats/monstersKilled": tk.StringVar(),

            "stats/fishCaught": tk.StringVar(),

            "stats/itemsForaged": tk.StringVar(),

            "year": tk.StringVar(),

            "currentSeason": tk.StringVar(),

            "dayOfMonth": tk.StringVar(),

            "weatherForTomorrow": tk.StringVar(),

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

        self.weather_tomorrow_options = self.get_weather_tomorrow_options()

        self.weather_tomorrow_cb = None

        self.pets_data = []

        self.animals_data = []

        self.inventory_items = []

        self.inventory_max = 36

        self.chests_data = []

        default_path = self.get_default_save_path()

        if os.path.exists(default_path):

            self.parent_save_dir = default_path

        else:

            self.parent_save_dir = os.getcwd()

        tr.set_language(tr.current_lang or "en")

        self.language_var = tk.StringVar(value=tr.get_language_label(tr.current_lang))

        self.setup_ui()

        self.game_path_detector = GamePathDetector(log_callback=self._log_mod_message)

        self.steam_helper = SteamHelper(log_callback=self._log_mod_message)

        self._auto_detect_game_path()

        self.setup_realtime_limits()

        self.refresh_save_list()

    # Initialize the item lookup tables used by the editor.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def init_item_maps(self):

        self.item_name_map = {}

        self.item_name_map_by_prefix = {}

        for cat, items in ITEM_CATEGORIES.items():

            for key, data in items.items():

                display_name = get_localized_item_name(key, data)

                save_name = data.get("name", key)

                self.item_name_map[save_name] = display_name

                item_id = data["id"]

                self.item_name_map[item_id] = display_name

                if "(" in item_id and ")" in item_id:

                    prefix = item_id[item_id.find("(")+1 : item_id.find(")")]

                    clean_id = item_id[item_id.find(")")+1:]

                else:

                    clean_id = item_id

                    if cat == "rings": prefix = "O"

                    elif cat == "trinkets": prefix = "TR"

                    elif cat == "hats": prefix = "H"

                    elif cat == "shoes": prefix = "B"

                    else: prefix = "O"

                    prefixed_id = f"({prefix}){item_id}"

                    self.item_name_map[prefixed_id] = display_name

                if prefix not in self.item_name_map_by_prefix:

                    self.item_name_map_by_prefix[prefix] = {}

                self.item_name_map_by_prefix[prefix][clean_id] = display_name

        self.equipment_map = {

            "leftRing": "rings",

            "rightRing": "rings",

            "trinketItem": "trinkets",

            "boots": "shoes",

            "hat": "hats",

            "shirtItem": "clothes",

            "pantsItem": "clothes"

        }

        self.category_options = {}

        for attr, cat_key in self.equipment_map.items():

            options = [tr.translate("none")]

            items = ITEM_CATEGORIES.get(cat_key, {})

            for key, data in items.items():

                item_id = data["id"]

                if "(" not in item_id:

                    if cat_key == "rings": item_id = f"(O){item_id}"

                    elif cat_key == "trinkets": item_id = f"(TR){item_id}"

                    elif cat_key == "hats": item_id = f"(H){item_id}"

                    elif cat_key == "shoes": item_id = f"(B){item_id}"

                    elif cat_key == "clothes":

                        if attr == "shirtItem": item_id = f"(S){item_id}"

                        elif attr == "pantsItem": item_id = f"(P){item_id}"

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

                display_name = self.item_name_map.get(item_id, key)

                options.append(f"({item_id}) {display_name}")

            self.category_options[attr] = options

    # Attach real-time validation rules to numeric editor inputs.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def setup_realtime_limits(self):

        numeric_specs = [

            (self.player_fields["money"], 99999999, 0, False),

            (self.player_fields["totalMoneyEarned"], None, 0, False),

            (self.player_fields["qiGems"], None, 0, False),

            (self.player_fields["masteryExp"], None, 0, False),

            (self.player_fields["health"], None, 0, False),

            (self.player_fields["maxHealth"], None, 0, False),

            (self.player_fields["stamina"], None, 0, False),

            (self.player_fields["maxStamina"], None, 0, False),

            (self.player_fields["clubCoins"], None, 0, False),

            (self.player_fields["deepestMineLevel"], 120, 0, False),

            (self.player_fields["timesReachedMineBottom"], None, 0, False),

            (self.player_fields["trashCanLevel"], 4, 0, False),

            (self.player_fields["houseUpgradeLevel"], 3, 0, False),

            (self.player_fields["magneticRadius"], None, 0, False),

            (self.player_fields["resilience"], None, 0, False),

            (self.player_fields["immunity"], None, 0, False),

            (self.player_fields["farmingLevel"], 10, 0, False),

            (self.player_fields["miningLevel"], 10, 0, False),

            (self.player_fields["foragingLevel"], 10, 0, False),

            (self.player_fields["fishingLevel"], 10, 0, False),

            (self.player_fields["combatLevel"], 10, 0, False),

            (self.player_fields["luckLevel"], 10, 0, False),

            (self.player_fields["maxItems"], 36, 12, False),

            (self.player_fields["attack"], None, 0, False),

            (self.player_fields["hair"], None, 0, False),

            (self.player_fields["hairstyle"], 73, 0, False),

            (self.player_fields["accessory"], 29, -1, True),

            (self.player_fields["skin"], 23, 0, False),

            (self.player_fields["facialHair"], None, 0, False),

            (self.player_fields["whichPetBreed"], None, 0, False),

            (self.player_fields["daysUntilHouseUpgrade"], None, 0, False),

            (self.game_fields["goldenWalnuts"], 130, 0, False),

            (self.game_fields["stats/stepsTaken"], None, 0, False),

            (self.game_fields["stats/daysPlayed"], None, 0, False),

            (self.game_fields["stats/monstersKilled"], None, 0, False),

            (self.game_fields["stats/fishCaught"], None, 0, False),

            (self.game_fields["stats/itemsForaged"], None, 0, False),

            (self.game_fields["year"], None, 1, False),

            (self.game_fields["dayOfMonth"], 28, 1, False),

        ]

        for var, max_value, min_value, allow_negative in numeric_specs:

            bind_numeric_input_limit(

                var,

                max_value=max_value,

                min_value=min_value,

                allow_negative=allow_negative

            )

        for exp_var in self.exp_vars:

            bind_numeric_input_limit(exp_var, max_value=15000, min_value=0)

        bind_float_input_limit(self.game_fields["dailyLuck"], max_value=0.1, min_value=-0.1)

    # Refresh the save list.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def refresh_save_list(self):

        self.available_saves = list_save_folders(self.parent_save_dir)

        if hasattr(self, 'save_selector'):

            save_names = [s["name"] for s in self.available_saves]

            self.save_selector["values"] = save_names

            if save_names:

                self.save_selector.current(0)

                self.on_save_selected()

            else:

                self.status_var.set(f"{tr.translate('no_save_found_prefix')} {os.path.basename(self.parent_save_dir)} {tr.translate('no_save_found_suffix')}")

    # Load the selected save file into the editor.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def on_save_selected(self, event=None):

        idx = self.save_selector.current()

        if idx >= 0:

            self.save_dir = self.available_saves[idx]["path"]

            self.load_save_data()

    # Resolve the absolute path to a bundled resource file.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def resource_path(self, relative_path):

        try:

            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        except Exception:

            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        return os.path.join(base_path, relative_path)

    # Configure the shared ttk styles used across the editor interface.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def configure_widget_styles(self):

        style = ttk.Style(self.root)

        style.configure(

            "TCombobox",

            padding=(8, 5, 28, 5),

            arrowsize=16,

            borderwidth=1,

            relief="flat",

        )

        style.map(

            "TCombobox",

            fieldbackground=[("readonly", "#f8fbff"), ("focus", "#ffffff")],

            background=[("readonly", "#f8fbff")],

            foreground=[("readonly", "#1f2937"), ("focus", "#111827")],

            bordercolor=[("focus", "#3b82f6"), ("readonly", "#c7d2e0")],

            lightcolor=[("focus", "#60a5fa"), ("readonly", "#d9e2ec")],

            darkcolor=[("focus", "#3b82f6"), ("readonly", "#d9e2ec")],

            arrowcolor=[("readonly", "#28559a"), ("active", "#1d4ed8"), ("disabled", "#94a3b8")],

            selectbackground=[("readonly", "#dbeafe")],

            selectforeground=[("readonly", "#111827")],

        )

        self.root.option_add("*TCombobox*Listbox.font", "{Segoe UI} 10")

        self.root.option_add("*TCombobox*Listbox.background", "#ffffff")

        self.root.option_add("*TCombobox*Listbox.foreground", "#111827")

        self.root.option_add("*TCombobox*Listbox.selectBackground", "#dbeafe")

        self.root.option_add("*TCombobox*Listbox.selectForeground", "#111827")

    # Build the main editor layout and attach each top-level page.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def setup_ui(self):

        self.init_item_maps()

        self.configure_widget_styles()

        self.root.title(tr.translate("app_title"))

        toolbar = ttk.Frame(self.root, padding=5)

        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttkb.Button(
            toolbar,
            text=tr.translate("select_saves_dir_btn"),
            command=self.select_save_dir,
            bootstyle=PRIMARY,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(toolbar, text=tr.translate("select_save")).pack(side=tk.LEFT, padx=(10, 2))

        self.save_selector = ttk.Combobox(toolbar, state="readonly", width=40)

        self.save_selector.pack(side=tk.LEFT, padx=5)

        self.save_selector.bind("<<ComboboxSelected>>", self.on_save_selected)

        ttkb.Button(toolbar, text=tr.translate("refresh"), command=self.refresh_save_list, bootstyle=SECONDARY).pack(side=tk.LEFT, padx=5)

        language_frame = ttk.Frame(toolbar)

        language_frame.pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Label(language_frame, text=tr.translate("language")).pack(side=tk.LEFT, padx=(0, 5))

        self.language_var.set(tr.get_language_label(tr.current_lang))

        self.language_selector = ttk.Combobox(
            language_frame,
            textvariable=self.language_var,
            state="readonly",
            width=12,
            values=self.get_language_options(),
        )

        self.language_selector.pack(side=tk.LEFT)

        self.language_selector.bind("<<ComboboxSelected>>", self.change_language)

        self.status_var = tk.StringVar(value=tr.translate("detecting_saves"))

        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)

        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        main_notebook = ttk.Notebook(self.root)

        main_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.build_world_tab(main_notebook)

        self.build_player_tab(main_notebook)

        self.build_items_tab(main_notebook)

        self.build_mods_tab(main_notebook)

        save_btn = ttk.Button(self.root, text=tr.translate("save_all"), command=self.save_data, style="Header.TButton")

        save_btn.pack(pady=10)

    # Select the save dir.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def select_save_dir(self):

        new_dir = filedialog.askdirectory(initialdir=self.parent_save_dir, title=tr.translate("select_saves_dir"))

        if new_dir:

            self.parent_save_dir = new_dir

            self.refresh_save_list()

    # Save the current player to element.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def save_current_player_to_element(self):

        if self.current_player_idx is None: return

        player = self.all_players[self.current_player_idx]["model"]

        for attr, var in self.player_fields.items():

            if attr == "spouse":

                self.save_proxy.spouse = var.get() if var.get() != tr.translate("none") else ""

                continue

            val = str(var.get())

            if hasattr(player, attr):

                if attr == "gender":

                    player.gender = "0" if val == tr.translate("male") else "1"

                elif attr in ["hairColor", "eyeColor", "pantsColor"]:

                    try:

                        r, g, b = map(int, val.split(","))

                        setattr(player, attr, (r, g, b, 255))

                    except:

                        pass

                elif attr == "catPerson":

                    p_type_str = self.parse_display_pet_type(val)

                    cat_person_val = p_type_str == "Cat"

                    player.catPerson = cat_person_val

                    player.petType = p_type_str

                elif attr in self.equipment_map:

                    if val == tr.translate("none"):

                        setattr(player, attr, None)

                    elif val.startswith("(") and ") " in val:

                        last_bracket_idx = val.rfind(") ")

                        if last_bracket_idx != -1:

                            item_id = val[1:last_bracket_idx]

                            setattr(player, attr, item_id)

                        else:

                            setattr(player, attr, val)

                    else:

                        setattr(player, attr, val)

                else:

                    setattr(player, attr, val)

        for item_data in self.inventory_items:

            item_model = item_data['model']

            item_model.stack = int(item_data['stack'].get())

            item_model.quality = int(item_data['quality'].get())

        for chest in self.chests_data:

            for item_data in chest['items']:

                item_model = item_data['model']

                item_model.stack = int(item_data['stack'].get())

                item_model.quality = int(item_data['quality'].get())

        for attr, var in self.game_fields.items():

            if attr == "caveChoice":

                self.save_proxy.playerChoiceFruitCave = self.parse_display_cave_choice(var.get())

                continue

            if attr == "currentSeason":

                self.save_proxy.currentSeason = self.parse_display_season(var.get())

                continue

            if attr == "canCheat":

                self.save_proxy.canCheat = var.get()

                continue

            if attr == "stats/stepsTaken":

                self.save_proxy.stepsTaken = int(var.get())

                continue

            if attr == "stats/daysPlayed":

                self.save_proxy.daysPlayed = int(var.get())

                continue

            if attr == "stats/monstersKilled":

                self.save_proxy.monstersKilled = int(var.get())

                continue

            if attr == "stats/fishCaught":

                self.save_proxy.fishCaught = int(var.get())

                continue

            if attr == "stats/itemsForaged":

                self.save_proxy.itemsForaged = int(var.get())

                continue

            if attr == "goldenWalnuts":

                self.save_proxy.goldenWalnuts = int(var.get() if var.get() else 0)

                continue

            if attr == "dailyLuck":

                raw_value = var.get().strip()

                if raw_value in {"", "-", "0.", "-0."}:

                    luck_value = 0.0

                else:

                    try:

                        luck_value = float(raw_value)

                    except ValueError:

                        luck_value = 0.0

                luck_value = max(-0.1, min(0.1, luck_value))

                self.save_proxy.dailyLuck = f"{luck_value:g}"

                continue

            if attr == "weatherForTomorrow":

                self.save_proxy.weatherForTomorrow = self.parse_display_weather_tomorrow(var.get())

                continue

            if hasattr(self.save_proxy, attr):

                setattr(self.save_proxy, attr, var.get())

            else:

                self.save_proxy.set_text(attr, var.get())

        self.save_proxy.isRaining = self.weather_vars["isRaining"].get()

        self.save_proxy.isDebrisWeather = self.weather_vars["isDebrisWeather"].get()

        self.save_proxy.isLightning = self.weather_vars["isLightning"].get()

        self.save_proxy.isSnowing = self.weather_vars["isSnowing"].get()

        self.save_proxy.isGreenRain = self.weather_vars["isGreenRain"].get()

        for i, var in enumerate(self.exp_vars):

            player.set_experience(i, int(var.get() if var.get() else 0))

        player.set_professions(self.professions_list)

        for npc_name, data in self.friendship_data.items():

            player.update_friendship(npc_name, data["points"].get())

        for pet_data in self.pets_data:

            pet = pet_data["model"]

            pet.name = pet_data["name"].get()

            pet.petType = self.parse_display_pet_type(pet_data["type"].get())

            pet.whichBreed = int(pet_data["breed"].get() if pet_data["breed"].get() else 0)

            pet.friendshipTowardFarmer = int(pet_data["friendship"].get() if pet_data["friendship"].get() else 0)

            pet.timesPet = int(pet_data["timesPet"].get() if pet_data["timesPet"].get() else 0)

            pet.isSleepingOnFarmerBed = pet_data["isSleepingOnFarmerBed"].get()

            pet.grantedFriendshipForPet = pet_data["grantedFriendshipForPet"].get()

        for animal_data in self.animals_data:

            animal = animal_data["model"]

            animal.name = animal_data["name"].get()

            animal.gender = self.parse_display_gender(animal_data["gender"].get())

            animal.age = int(animal_data["age"].get() if animal_data["age"].get() else 0)

            animal.friendship = int(animal_data["friendship"].get() if animal_data["friendship"].get() else 0)

            animal.fullness = int(animal_data["fullness"].get() if animal_data["fullness"].get() else 0)

            animal.happiness = int(animal_data["happiness"].get() if animal_data["happiness"].get() else 0)

            animal.allowReproduction = animal_data["allowReproduction"].get()

            animal.hasEatenAnimalCracker = animal_data["hasEatenAnimalCracker"].get()

            animal.wasPet = animal_data["wasPet"].get()

            animal.isEating = animal_data["isEating"].get()

            animal.wasAutoPet = animal_data["wasAutoPet"].get()

            animal.buildingTypeILiveIn = parse_display_building_name(animal_data["buildingTypeILiveIn"].get())

    # Save the data.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def save_data(self):

        if not self.save_file: return

        self.save_current_player_to_element()

        try:

            bak = self.save_file + ".bak"

            if not os.path.exists(bak): shutil.copy2(self.save_file, bak)

            info_path = os.path.join(os.path.dirname(self.save_file), self.info_file)

            if os.path.exists(info_path):

                info_bak = info_path + ".bak"

                if not os.path.exists(info_bak): shutil.copy2(info_path, info_bak)

            self.save_proxy.save()

            messagebox.showinfo(tr.translate("success"), tr.translate("save_success").format(os.path.basename(bak)))

            self.status_var.set(f"{tr.translate('saved')}: {os.path.basename(self.save_file)}")

        except Exception as e:

            messagebox.showerror(tr.translate("save_fail"), f"{tr.translate('cannot_write_save').format(e)}")

    # Bind tooltip behavior to the provided widget.
    # It coordinates shared editor state across multiple tabs, dialogs, and services.
    def add_tooltip(self, widget, text):

        # Show the tooltip text in the status bar while the widget is hovered.
        # It coordinates shared editor state across multiple tabs, dialogs, and services.
        def enter(event):

            self.status_var.set(f"ℹ️ {text}")

        # Restore the default status message when the pointer leaves the widget.
        # It coordinates shared editor state across multiple tabs, dialogs, and services.
        def leave(event):

            self.status_var.set(f"{tr.translate('save_loaded')}: {os.path.basename(self.save_file)}")

        widget.bind("<Enter>", enter)

        widget.bind("<Leave>", leave)
