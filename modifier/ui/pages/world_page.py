# Build the world page and expose editable world-state widgets to the editor.
import os

import tkinter as tk

from tkinter import messagebox, ttk

from models.pet_data import PET_DATA

from utils import tr

from utils.game_text_localization import (
    translate_animal_type,
    translate_building_name,
    translate_location_name,
)

from utils.save_utils import SaveProxy, find_save_files

from ..dialogs import BundlesDialog

from ..helpers import bind_numeric_input_limit, setup_mousewheel

# Provide page-specific UI builders and behaviors that are mixed into the main editor window.
# It keeps tab-specific widgets synchronized with the current save model and editor state.
class WorldPageMixin:

    # Build the world tab.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def build_world_tab(self, main_notebook):

        world_tab = ttk.Frame(main_notebook)

        main_notebook.add(world_tab, text=tr.translate("env_time_pet_tab"))

        world_container = ttk.Frame(world_tab)

        world_container.pack(fill=tk.BOTH, expand=True)

        world_canvas = tk.Canvas(world_container, highlightthickness=0)

        world_scrollbar = ttk.Scrollbar(world_container, orient="vertical", command=world_canvas.yview)

        scrollable_world = ttk.Frame(world_canvas)

        scrollable_world.bind(

            "<Configure>",

            lambda e: world_canvas.configure(scrollregion=world_canvas.bbox("all"))

        )

        world_canvas_window = world_canvas.create_window((0, 0), window=scrollable_world, anchor="nw")

        world_canvas.bind("<Configure>", lambda e: world_canvas.itemconfig(world_canvas_window, width=e.width))

        world_canvas.configure(yscrollcommand=world_scrollbar.set)

        world_scrollbar.pack(side="right", fill="y")

        world_canvas.pack(side="left", fill="both", expand=True)

        setup_mousewheel(world_canvas)

        env_frame = ttk.LabelFrame(scrollable_world, text=tr.translate("env_time_settings"), padding=10)

        env_frame.pack(fill=tk.X, padx=10, pady=5)

        time_fields = [

            ("current_year", "year"),

            ("current_day", "dayOfMonth"),

            ("current_season", "currentSeason"),

            ("daily_luck", "dailyLuck"),

            ("weather_tomorrow", "weatherForTomorrow"),

            ("days_played", "stats/daysPlayed"),

            ("total_steps", "stats/stepsTaken"),

            ("monsters_killed", "stats/monstersKilled"),

            ("fish_caught", "stats/fishCaught"),

            ("items_foraged", "stats/itemsForaged"),

        ]

        for i, (label_key, attr) in enumerate(time_fields):

            row, col = divmod(i, 2)

            ttk.Label(env_frame, text=tr.translate(label_key)).grid(row=row, column=col * 2, sticky=tk.W, pady=2)

            if attr == "currentSeason":

                cb = ttk.Combobox(

                    env_frame,

                    textvariable=self.game_fields[attr],

                    values=self.get_season_options(),

                    state="readonly",

                    width=12,

                )

                cb.grid(row=row, column=col * 2 + 1, sticky=tk.W, padx=5, pady=2)

            elif attr == "weatherForTomorrow":

                self.weather_tomorrow_cb = ttk.Combobox(

                    env_frame,

                    textvariable=self.game_fields[attr],

                    values=self.get_weather_tomorrow_options(),

                    state="readonly",

                    width=15,

                )

                self.weather_tomorrow_cb.grid(row=row, column=col * 2 + 1, sticky=tk.W, padx=5, pady=2)

            else:

                ttk.Entry(env_frame, textvariable=self.game_fields[attr], width=15).grid(

                    row=row,

                    column=col * 2 + 1,

                    sticky=tk.W,

                    padx=5,

                    pady=2,

                )

        weather_frame = ttk.LabelFrame(scrollable_world, text=tr.translate("weather_settings"), padding=10)

        weather_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Checkbutton(weather_frame, text=tr.translate("is_raining"), variable=self.weather_vars["isRaining"]).pack(side=tk.LEFT, padx=10)

        ttk.Checkbutton(weather_frame, text=tr.translate("is_lightning"), variable=self.weather_vars["isLightning"]).pack(side=tk.LEFT, padx=10)

        ttk.Checkbutton(weather_frame, text=tr.translate("is_snowing"), variable=self.weather_vars["isSnowing"]).pack(side=tk.LEFT, padx=10)

        ttk.Checkbutton(weather_frame, text=tr.translate("is_debris"), variable=self.weather_vars["isDebrisWeather"]).pack(side=tk.LEFT, padx=10)

        ttk.Checkbutton(weather_frame, text=tr.translate("is_green_rain"), variable=self.weather_vars["isGreenRain"]).pack(side=tk.LEFT, padx=10)

        cheat_cb = ttk.Checkbutton(weather_frame, text=tr.translate("can_cheat"), variable=self.game_fields["canCheat"])

        cheat_cb.pack(side=tk.LEFT, padx=10)

        bundles_frame = ttk.LabelFrame(scrollable_world, text=tr.translate("community_center"), padding=10)

        bundles_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(bundles_frame, text=tr.translate("manage_bundles"), command=self.show_bundles_window).pack(side=tk.LEFT, padx=5)

        self.pets_frame = ttk.LabelFrame(scrollable_world, text=tr.translate("pets_list"), padding=10)

        self.pets_frame.pack(fill=tk.X, padx=10, pady=5)

        self.animals_frame = ttk.LabelFrame(scrollable_world, text=tr.translate("animals_list"), padding=10)

        self.animals_frame.pack(fill=tk.X, padx=10, pady=5)

    # Load the save data.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def load_save_data(self):

        save_file, info_file = find_save_files(self.save_dir)

        if not save_file:

            self.status_var.set(tr.translate('no_valid_save_found').format(os.path.basename(self.save_dir) or self.save_dir))

            return

        self.status_var.set(tr.translate('loading_from').format(name=os.path.basename(self.save_dir)))

        self.root.update_idletasks()

        try:

            self.save_proxy = SaveProxy(save_file, info_file)

            self.save_file = save_file

            self.info_file = os.path.basename(info_file) if info_file else "SaveGameInfo"

            root = self.save_proxy.root

            self.weather_vars["isRaining"].set(bool(self.save_proxy.isRaining))

            self.weather_vars["isDebrisWeather"].set(bool(self.save_proxy.isDebrisWeather))

            self.weather_vars["isLightning"].set(bool(self.save_proxy.isLightning))

            self.weather_vars["isSnowing"].set(bool(self.save_proxy.isSnowing))

            self.weather_vars["isGreenRain"].set(bool(self.save_proxy.isGreenRain))

            self.all_players = []

            if self.save_proxy.player:

                p = self.save_proxy.player

                self.all_players.append({"role": "host", "type": tr.translate("host"), "name": p.name, "model": p})

            for hand in self.save_proxy.farmhands:

                self.all_players.append({"role": "farmhand", "type": tr.translate("farmhand"), "name": hand.name, "model": hand})

            self.pets_data = []

            for pet_info in self.save_proxy.get_all_pets():

                pet = pet_info["model"]

                breed_var = tk.StringVar(value=str(pet.whichBreed))

                friendship_var = tk.StringVar(value=str(pet.friendshipTowardFarmer))

                times_pet_var = tk.StringVar(value=str(pet.timesPet))

                bind_numeric_input_limit(breed_var, min_value=0)

                bind_numeric_input_limit(friendship_var, min_value=0)

                bind_numeric_input_limit(times_pet_var, min_value=0)

                self.pets_data.append({

                    'name': tk.StringVar(value=pet.name),

                    'type': tk.StringVar(value=self.get_display_pet_type(pet.petType)),

                    'breed': breed_var,

                    'friendship': friendship_var,

                    'timesPet': times_pet_var,

                    'isSleepingOnFarmerBed': tk.BooleanVar(value=pet.isSleepingOnFarmerBed),

                    'grantedFriendshipForPet': tk.BooleanVar(value=pet.grantedFriendshipForPet),

                    'model': pet,

                    'location': pet_info["location"],

                    'display_location': translate_location_name(pet_info["location"])

                })

            self.chests_data = []

            for chest_info in self.save_proxy.get_all_chests():

                chest = chest_info["model"]

                chest_items = []

                for item in chest.items:

                    if item.is_empty: continue

                    raw_name = item.name or tr.translate("unknown")

                    item_id = item.itemId or ""

                    display_name = raw_name

                    if item_id and item_id in self.item_name_map:

                        display_name = self.item_name_map[item_id]

                    elif raw_name in self.item_name_map:

                        display_name = self.item_name_map[raw_name]

                    stack_var = tk.StringVar(value=str(item.stack))

                    quality_var = tk.StringVar(value=str(item.quality))

                    bind_numeric_input_limit(stack_var, min_value=1)

                    bind_numeric_input_limit(quality_var, max_value=4, min_value=0)

                    chest_items.append({

                        'display_name': display_name,

                        'name': raw_name,

                        'stack': stack_var,

                        'quality': quality_var,

                        'model': item

                    })

                self.chests_data.append({

                    'location': chest_info["location"],

                    'display_location': translate_location_name(chest_info["location"]),

                    'capacity': str(chest.capacity),

                    'items': chest_items,

                    'model': chest

                })

            self.animals_data = []

            for animal_info in self.save_proxy.get_all_animals():

                animal = animal_info["model"]

                age_var = tk.StringVar(value=str(animal.age))

                friendship_var = tk.StringVar(value=str(animal.friendship))

                fullness_var = tk.StringVar(value=str(animal.fullness))

                happiness_var = tk.StringVar(value=str(animal.happiness))

                bind_numeric_input_limit(age_var, min_value=0)

                bind_numeric_input_limit(friendship_var, min_value=0)

                bind_numeric_input_limit(fullness_var, min_value=0)

                bind_numeric_input_limit(happiness_var, min_value=0)

                self.animals_data.append({

                    'name': tk.StringVar(value=animal.name),

                    'type': tk.StringVar(value=translate_animal_type(animal.type)),

                    'gender': tk.StringVar(value=self.get_display_gender(animal.gender)),

                    'age': age_var,

                    'friendship': friendship_var,

                    'fullness': fullness_var,

                    'happiness': happiness_var,

                    'allowReproduction': tk.BooleanVar(value=animal.allowReproduction),

                    'hasEatenAnimalCracker': tk.BooleanVar(value=animal.hasEatenAnimalCracker),

                    'wasPet': tk.BooleanVar(value=animal.wasPet),

                    'isEating': tk.BooleanVar(value=animal.isEating),

                    'wasAutoPet': tk.BooleanVar(value=animal.wasAutoPet),

                    'buildingTypeILiveIn': tk.StringVar(value=translate_building_name(animal.buildingTypeILiveIn)),

                    'model': animal,

                    'location': animal_info["location"],

                    'display_location': translate_location_name(animal_info["location"])

                })

            if self.all_players:

                self.player_selector["values"] = [f"[{p['type']}] {p['name']}" for p in self.all_players]

                self.player_selector.current(0)

                self.load_player_data(0)

            self.refresh_pets_list()

            self.refresh_animals_list()

            self.refresh_items_list()

            self.status_var.set(tr.translate('save_loaded').format(name=os.path.basename(self.save_file)))

        except Exception as e:

            import traceback

            error_details = traceback.format_exc()

            print(f"Parse error details:\n{error_details}")

            messagebox.showerror(tr.translate("load_failed"), tr.translate("parse_save_failed").format(error=e))

    # Refresh the pets list.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def refresh_pets_list(self):

        for widget in self.pets_frame.winfo_children(): widget.destroy()

        if not self.pets_data:

            ttk.Label(self.pets_frame, text=tr.translate("no_pets_found")).pack(pady=10)

            return

        self.pets_frame.columnconfigure(0, weight=1)

        self.pets_frame.rowconfigure(1, weight=1)

        headers = [

            ("pet_name", 15), ("pet_type", 12), ("pet_breed", 20),

            ("friendship", 12), ("times_pet", 12), ("on_bed", 10),

            ("pet_today", 10), ("location", 15)

        ]

        header_frame = ttk.Frame(self.pets_frame)

        header_frame.grid(row=0, column=0, sticky="ew")

        for col, (key, width) in enumerate(headers):

            header_frame.columnconfigure(col, weight=1, minsize=width*8)

            lbl = ttk.Label(header_frame, text=tr.translate(key), width=width, anchor=tk.CENTER)

            lbl.grid(row=0, column=col, padx=5, pady=5)

        canvas_container = ttk.Frame(self.pets_frame)

        canvas_container.grid(row=1, column=0, sticky="nsew")

        canvas = tk.Canvas(canvas_container, height=150, highlightthickness=0)

        v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)

        h_scrollbar = ttk.Scrollbar(self.pets_frame, orient="horizontal", command=canvas.xview)

        list_frame = ttk.Frame(canvas)

        for col, (key, width) in enumerate(headers):

            list_frame.columnconfigure(col, weight=1, minsize=width*8)

        # Update the pet scrollbars.
        # It keeps tab-specific widgets synchronized with the current save model and editor state.
        def update_pet_scrollbars(event=None):

            canvas.configure(scrollregion=canvas.bbox("all"))

            if canvas.bbox("all")[3] <= 150:

                v_scrollbar.pack_forget()

            else:

                v_scrollbar.pack(side="right", fill="y")

            if canvas.bbox("all")[2] <= canvas.winfo_width():

                h_scrollbar.grid_forget()

            else:

                h_scrollbar.grid(row=2, column=0, sticky="ew")

        list_frame.bind("<Configure>", update_pet_scrollbars)

        canvas.bind("<Configure>", update_pet_scrollbars)

        canvas.create_window((0, 0), window=list_frame, anchor="nw")

        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)

        setup_mousewheel(canvas)

        for i, pet in enumerate(self.pets_data):

            ttk.Entry(list_frame, textvariable=pet['name'], width=15).grid(row=i, column=0, padx=5, pady=2, sticky="ew")

            type_cb = ttk.Combobox(list_frame, textvariable=pet['type'], values=self.get_pet_type_options(), state="readonly", width=12)

            type_cb.grid(row=i, column=1, padx=5, pady=2, sticky="ew")

            # Return the breed values.
            # It keeps tab-specific widgets synchronized with the current save model and editor state.
            def get_breed_values(p_type):

                data = PET_DATA.get(self.parse_display_pet_type(p_type), {})

                breeds = data.get("breeds", {})

                return [f"{k}: {tr.translate(v)}" for k, v in breeds.items()]

            breed_var = tk.StringVar()

            curr_type = pet['type'].get()

            curr_breed_idx = int(pet['breed'].get() if pet['breed'].get() else 0)

            breeds_list = get_breed_values(curr_type)

            initial_breed_text = f"{curr_breed_idx}"

            for b_text in breeds_list:

                if b_text.startswith(f"{curr_breed_idx}:"):

                    initial_breed_text = b_text

                    break

            breed_var.set(initial_breed_text)

            breed_cb = ttk.Combobox(list_frame, textvariable=breed_var, values=breeds_list, state="readonly", width=20)

            breed_cb.grid(row=i, column=2, padx=5, pady=2, sticky="ew")

            # Update the pet breed value after the combobox selection changes.
            # It keeps tab-specific widgets synchronized with the current save model and editor state.
            def on_breed_change(event, b_var=breed_var, p_ref=pet):

                val = b_var.get()

                if ":" in val:

                    idx = val.split(":")[0]

                    p_ref['breed'].set(idx)

            breed_cb.bind("<<ComboboxSelected>>", on_breed_change)

            # Refresh the breed choices after the pet type selection changes.
            # It keeps tab-specific widgets synchronized with the current save model and editor state.
            def on_type_change(event, t_cb=type_cb, b_cb=breed_cb, b_var=breed_var, p_ref=pet):

                new_type = self.parse_display_pet_type(t_cb.get())

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

            cb_bed.grid(row=i, column=5, padx=5, pady=2)

            self.add_tooltip(cb_bed, tr.translate("on_bed_tip"))

            cb_pet = ttk.Checkbutton(list_frame, variable=pet['grantedFriendshipForPet'])

            cb_pet.grid(row=i, column=6, padx=5, pady=2)

            self.add_tooltip(cb_pet, tr.translate("pet_today_tip"))

            ttk.Label(list_frame, text=pet.get('display_location', pet['location']), width=15, anchor=tk.CENTER).grid(row=i, column=7, padx=5, pady=2, sticky="ew")

    # Refresh the animals list.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def refresh_animals_list(self):

        for widget in self.animals_frame.winfo_children(): widget.destroy()

        if not self.animals_data:

            ttk.Label(self.animals_frame, text=tr.translate("no_animals_found")).pack(pady=10)

            return

        self.animals_frame.columnconfigure(0, weight=1)

        self.animals_frame.rowconfigure(1, weight=1)

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

            lbl.grid(row=0, column=col, padx=5, pady=5)

        canvas_container = ttk.Frame(self.animals_frame)

        canvas_container.grid(row=1, column=0, sticky="nsew")

        canvas = tk.Canvas(canvas_container, height=300, highlightthickness=0)

        v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)

        h_scrollbar = ttk.Scrollbar(self.animals_frame, orient="horizontal", command=canvas.xview)

        scroll_frame = ttk.Frame(canvas)

        for col, (key, width) in enumerate(headers):

            scroll_frame.columnconfigure(col, weight=1, minsize=width*8)

        # Update the animal scrollbars.
        # It keeps tab-specific widgets synchronized with the current save model and editor state.
        def update_animal_scrollbars(event=None):

            canvas.configure(scrollregion=canvas.bbox("all"))

            if canvas.bbox("all")[3] <= 300:

                v_scrollbar.pack_forget()

            else:

                v_scrollbar.pack(side="right", fill="y")

            if canvas.bbox("all")[2] <= canvas.winfo_width():

                h_scrollbar.grid_forget()

            else:

                h_scrollbar.grid(row=2, column=0, sticky="ew")

        scroll_frame.bind("<Configure>", update_animal_scrollbars)

        canvas.bind("<Configure>", update_animal_scrollbars)

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)

        setup_mousewheel(canvas)

        for i, animal in enumerate(self.animals_data):

            row = i

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

            ttk.Label(scroll_frame, text=animal.get('display_location', animal['location']), width=15, anchor=tk.CENTER).grid(row=row, column=13, padx=5, pady=2, sticky="ew")

    # Show the bundles window.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def show_bundles_window(self):

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
