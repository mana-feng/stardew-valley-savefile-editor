# Parse save files, sanitize XML content, and provide filesystem helpers for save discovery.
import os

import re

import xml.etree.ElementTree as ET

from models.base_proxy import BaseProxy

ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')

ET.register_namespace('xsd', 'http://www.w3.org/2001/XMLSchema')

from models.farmer import Farmer

from models.pet import Pet

from models.chest import Chest

_INVALID_AMP_PATTERN = re.compile(r"&(?!(?:#\d+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9._-]*);)")

_STATS_STEPS_TAG_PATTERN = re.compile(r"<stats/stepsTaken(?:\s+[^>]*)?>([^<]*)</stats/stepsTaken>")

_STATS_STEPS_SELF_PATTERN = re.compile(r"<stats/stepsTaken(?:\s+[^>]*)?\s*/>")

# Remove characters that are invalid in XML 1.0 documents.
# It keeps save parsing, sanitization, and filesystem discovery consistent.
def _strip_invalid_xml_chars(text):

    if not text:

        return text, 0

    removed = 0

    out = []

    for ch in text:

        code = ord(ch)

        if (

            code == 0x9

            or code == 0xA

            or code == 0xD

            or 0x20 <= code <= 0xD7FF

            or 0xE000 <= code <= 0xFFFD

            or 0x10000 <= code <= 0x10FFFF

        ):

            out.append(ch)

        else:

            removed += 1

    return "".join(out), removed

# Sanitize the XML text.
# It keeps save parsing, sanitization, and filesystem discovery consistent.
def _sanitize_xml_text(text):

    cleaned, removed = _strip_invalid_xml_chars(text)

    cleaned, amp_fixed = _INVALID_AMP_PATTERN.subn("&amp;", cleaned)

    return cleaned, removed, amp_fixed

# Remove the invalid steps taken tags.
# It keeps save parsing, sanitization, and filesystem discovery consistent.
def _remove_invalid_steps_taken_tags(text):

    values = [m.group(1) for m in _STATS_STEPS_TAG_PATTERN.finditer(text)]

    cleaned, tag_count = _STATS_STEPS_TAG_PATTERN.subn("", text)

    cleaned, self_count = _STATS_STEPS_SELF_PATTERN.subn("", cleaned)

    value = None

    for v in values:

        v = v.strip()

        if v != "":

            value = v

    return cleaned, value, tag_count + self_count

# Apply the steps taken to player.
# It keeps save parsing, sanitization, and filesystem discovery consistent.
def _apply_steps_taken_to_player(root, value):

    if value is None:

        return False

    value = value.strip()

    if value == "":

        return False

    try:

        int_value = int(float(value))

    except (ValueError, TypeError):

        return False

    player = root.find("player")

    if player is None:

        return False

    stats = player.find("stats")

    if stats is None:

        stats = ET.SubElement(player, "stats")

    steps_elem = stats.find("stepsTaken")

    if steps_elem is None:

        steps_elem = ET.SubElement(stats, "stepsTaken")

    nil_attr = "{http://www.w3.org/2001/XMLSchema-instance}nil"

    if nil_attr in steps_elem.attrib:

        del steps_elem.attrib[nil_attr]

    steps_elem.text = str(int_value)

    return True

# Parse the XML file.
# It keeps save parsing, sanitization, and filesystem discovery consistent.
def _parse_xml_file(path):

    try:

        return ET.parse(path)

    except ET.ParseError:

        with open(path, "rb") as f:

            raw = f.read()

        text = raw.decode("utf-8-sig", errors="replace")

        sanitized, removed, amp_fixed = _sanitize_xml_text(text)

        sanitized, steps_value, steps_removed = _remove_invalid_steps_taken_tags(sanitized)

        try:

            root = ET.fromstring(sanitized)

        except ET.ParseError as exc:

            print(f"XML parse failed after sanitization for {path}: {exc}")

            raise

        if steps_removed:

            steps_applied = _apply_steps_taken_to_player(root, steps_value)

            action = "moved to player stats" if steps_applied else "removed"

            print(f"Warning: fixed {steps_removed} invalid stats/stepsTaken tag(s) in {path} ({action}).")

        if removed or amp_fixed:

            print(

                f"Warning: sanitized XML in {path} (removed {removed} invalid chars, "

                f"fixed {amp_fixed} stray '&')."

            )

        return ET.ElementTree(root)

# Find the save files.
# It keeps save parsing, sanitization, and filesystem discovery consistent.
def find_save_files(save_dir, info_file_name="SaveGameInfo"):

    if not save_dir or not os.path.exists(save_dir):

        return None, None

    folder_name = os.path.basename(os.path.abspath(save_dir))

    potential_main = os.path.join(save_dir, folder_name)

    if os.path.exists(potential_main) and os.path.isfile(potential_main):

        return potential_main, os.path.join(save_dir, info_file_name)

    if os.path.exists(os.path.join(save_dir, info_file_name)):

        files = [f for f in os.listdir(save_dir) if os.path.isfile(os.path.join(save_dir, f))

                 and f != info_file_name and not f.endswith((".py", ".bak", "_old", ".txt"))]

        if files:

            return os.path.join(save_dir, files[0]), os.path.join(save_dir, info_file_name)

    return None, None

# List the save folders.
# It keeps save parsing, sanitization, and filesystem discovery consistent.
def list_save_folders(parent_dir):

    if not parent_dir or not os.path.exists(parent_dir):

        return []

    save_folders = []

    try:

        for item in os.listdir(parent_dir):

            item_path = os.path.join(parent_dir, item)

            if os.path.isdir(item_path):

                main_file, info_file = find_save_files(item_path)

                if main_file:

                    save_folders.append({

                        "name": item,

                        "path": item_path,

                        "main_file": main_file,

                        "info_file": info_file

                    })

    except Exception:

        pass

    return save_folders

# Wrap XML elements with higher-level accessors used by the save editor.
# It keeps save parsing, sanitization, and filesystem discovery consistent.
class SaveProxy(BaseProxy):

    def __init__(self, main_path, info_path=None):

        self.main_path = main_path

        self.info_path = info_path

        self.tree = _parse_xml_file(main_path)

        root = self.tree.getroot()

        if root is None:

            raise ValueError(f"Failed to get root element from {main_path}")

        super().__init__(root)

        player_elem = self.root.find("player")

        self.player = Farmer(player_elem) if player_elem is not None else None

        self.farmhands = []

        farmhands_elem = self.root.find("farmhands")

        if farmhands_elem is not None:

            for f_elem in farmhands_elem.findall("Farmer"):

                self.farmhands.append(Farmer(f_elem))

    # Return the save's root.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def root(self):

        return self._element

    # Return the save's year.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def year(self): return self.get_int("year")

    # Update the save's year.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @year.setter

    def year(self, value): self.set_int("year", value)

    # Return the save's current season.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def currentSeason(self): return self.get_text("currentSeason")

    # Update the save's current season.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @currentSeason.setter

    def currentSeason(self, value): self.set_text("currentSeason", value)

    # Return the save's day of month.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def dayOfMonth(self): return self.get_int("dayOfMonth")

    # Update the save's day of month.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @dayOfMonth.setter

    def dayOfMonth(self, value): self.set_int("dayOfMonth", value)

    # Return the save's is raining.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def isRaining(self): return self.get_bool("isRaining")

    # Update the save's is raining.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @isRaining.setter

    def isRaining(self, value): self.set_bool("isRaining", value)

    # Return the save's is debris weather.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def isDebrisWeather(self):

        return self.get_bool("isDebrisWeather", False)

    # Update the save's is debris weather.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @isDebrisWeather.setter

    def isDebrisWeather(self, value): self.set_bool("isDebrisWeather", value)

    # Return the save's is lightning.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def isLightning(self): return self.get_bool("isLightning")

    # Update the save's is lightning.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @isLightning.setter

    def isLightning(self, value): self.set_bool("isLightning", value)

    # Return the save's is snowing.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def isSnowing(self): return self.get_bool("isSnowing")

    # Update the save's is snowing.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @isSnowing.setter

    def isSnowing(self, value): self.set_bool("isSnowing", value)

    # Return the save's is green rain.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def isGreenRain(self): return self.get_bool("isGreenRain", False)

    # Update the save's is green rain.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @isGreenRain.setter

    def isGreenRain(self, value): self.set_bool("isGreenRain", value)

    # Return the save's can cheat.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def canCheat(self): return self.get_bool("canCheat", False)

    # Update the save's can cheat.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @canCheat.setter

    def canCheat(self, value): self.set_bool("canCheat", value)

    # Return the save's spouse.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def spouse(self): return self.get_text("spouse")

    # Update the save's spouse.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @spouse.setter

    def spouse(self, value): self.set_text("spouse", value)

    # Return the save's player choice fruit cave.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def playerChoiceFruitCave(self): return self.get_text("playerChoiceFruitCave", "0")

    # Update the save's player choice fruit cave.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @playerChoiceFruitCave.setter

    def playerChoiceFruitCave(self, value): self.set_text("playerChoiceFruitCave", value)

    # Return the save's daily luck.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def dailyLuck(self): return self.get_text("dailyLuck")

    # Update the save's daily luck.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @dailyLuck.setter

    def dailyLuck(self, value): self.set_text("dailyLuck", value)

    # Return the save's golden walnuts.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def goldenWalnuts(self): return self.get_int("goldenWalnuts", 0)

    # Update the save's golden walnuts.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @goldenWalnuts.setter

    def goldenWalnuts(self, value): self.set_int("goldenWalnuts", value)

    # Return the save's steps taken.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def stepsTaken(self):

        if self.player:

            return self.player.get_int("stats/stepsTaken")

        return self.get_int("stats/stepsTaken")

    # Update the save's steps taken.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @stepsTaken.setter

    def stepsTaken(self, value):

        if self.player:

            self.player.set_int("stats/stepsTaken", value)

        else:

            self.set_int("stats/stepsTaken", value)

    # Return the save's days played.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def daysPlayed(self):

        if self.player:

            return self.player.get_int("stats/daysPlayed")

        return self.get_int("stats/daysPlayed")

    # Update the save's days played.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @daysPlayed.setter

    def daysPlayed(self, value):

        if self.player:

            self.player.set_int("stats/daysPlayed", value)

        else:

            self.set_int("stats/daysPlayed", value)

    # Return the save's monsters killed.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def monstersKilled(self):

        if self.player:

            return self.player.get_int("stats/monstersKilled")

        return self.get_int("stats/monstersKilled")

    # Update the save's monsters killed.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @monstersKilled.setter

    def monstersKilled(self, value):

        if self.player:

            self.player.set_int("stats/monstersKilled", value)

        else:

            self.set_int("stats/monstersKilled", value)

    # Return the save's fish caught.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def fishCaught(self):

        if self.player:

            return self.player.get_int("stats/fishCaught")

        return self.get_int("stats/fishCaught")

    # Update the save's fish caught.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @fishCaught.setter

    def fishCaught(self, value):

        if self.player:

            self.player.set_int("stats/fishCaught", value)

        else:

            self.set_int("stats/fishCaught", value)

    # Return the save's items foraged.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def itemsForaged(self):

        if self.player:

            return self.player.get_int("stats/itemsForaged")

        return self.get_int("stats/itemsForaged")

    # Update the save's items foraged.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @itemsForaged.setter

    def itemsForaged(self, value):

        if self.player:

            self.player.set_int("stats/itemsForaged", value)

        else:

            self.set_int("stats/itemsForaged", value)

    # Return the save's weather for tomorrow.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @property

    def weatherForTomorrow(self): return self.get_text("weatherForTomorrow")

    # Update the save's weather for tomorrow.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @weatherForTomorrow.setter

    def weatherForTomorrow(self, value): self.set_text("weatherForTomorrow", value)

    # Return every pet found across all save locations.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    def get_all_pets(self):

        pets = []

        try:

            locations_elem = self.root.find("locations")

            if locations_elem is not None:

                for loc in locations_elem.findall("GameLocation"):

                    name_elem = loc.find("name")

                    loc_name = name_elem.text if name_elem is not None and name_elem.text is not None else "Unknown"

                    chars = loc.find("characters")

                    if chars is not None:

                        for char in chars:

                            if char is not None and char.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "Pet":

                                pets.append({

                                    "model": Pet(char),

                                    "location": loc_name

                                })

        except Exception as e:

            print(f"Error getting pet list: {e}")

        return pets

    # Return every chest found across all save locations.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    def get_all_chests(self):

        chests = []

        try:

            locations_elem = self.root.find("locations")

            if locations_elem is not None:

                for loc in locations_elem.findall("GameLocation"):

                    name_elem = loc.find("name")

                    loc_name = name_elem.text if name_elem is not None and name_elem.text is not None else "Unknown"

                    objs = loc.find("objects")

                    if objs is not None:

                        for item in objs.findall("item"):

                            obj = item.find("value/Object")

                            if obj is not None and obj.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "Chest":

                                chests.append({

                                    "model": Chest(obj),

                                    "location": loc_name

                                })

        except Exception as e:

            print(f"Error getting chest list: {e}")

        return chests

    # Return every farm animal found across all save locations.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    def get_all_animals(self):

        from models.farm_animal import FarmAnimal

        animals = []

        try:

            locations_elem = self.root.find("locations")

            if locations_elem is not None:

                for loc in locations_elem.findall("GameLocation"):

                    name_elem = loc.find("name")

                    loc_name = name_elem.text if name_elem is not None and name_elem.text is not None else "Unknown"

                    animals_elem = loc.find("animals")

                    if animals_elem is not None:

                        for item in animals_elem.findall("item"):

                            animals.append({

                                "model": FarmAnimal(item),

                                "location": loc_name

                            })

        except Exception as e:

            print(f"Error getting animal list: {e}")

        return animals

    # Write the current in-memory state back to the save files.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    def save(self):

        root = self.tree.getroot()

        if root is None:

            return

        to_remove = [k for k in root.attrib if k.startswith("xmlns:")]

        for k in to_remove:

            del root.attrib[k]

        root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")

        for elem in self.tree.iter():

            if elem.text is None and len(elem) == 0:

                elem.text = ""

        import io

        output = io.BytesIO()

        self.tree.write(output, encoding="utf-8", xml_declaration=False)

        xml_str = output.getvalue().decode("utf-8")

        xml_str = xml_str.replace("/>", " />").replace("&apos;", "'")

        with open(self.main_path, "wb") as f:

            f.write('<?xml version="1.0" encoding="utf-8"?>'.encode("utf-8-sig"))

            f.write(xml_str.encode("utf-8"))

        if self.info_path and os.path.exists(self.info_path):

            try:

                info_tree = _parse_xml_file(self.info_path)

                info_root = info_tree.getroot()

                if info_root is None:

                    return

                for k in list(info_root.attrib):

                    if k.startswith("xmlns:"):

                        del info_root.attrib[k]

                info_root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")

                info_proxy = BaseProxy(info_root)

                info_proxy.set_text("year", self.year)

                info_proxy.set_text("currentSeason", self.currentSeason)

                info_proxy.set_text("dayOfMonth", self.dayOfMonth)

                if self.player:

                    sync_player_xml(info_root, self.player.raw)

                info_output = io.BytesIO()

                info_tree.write(info_output, encoding="utf-8", xml_declaration=False)

                info_xml_str = info_output.getvalue().decode("utf-8")

                info_xml_str = info_xml_str.replace("/>", " />").replace("&apos;", "'")

                with open(self.info_path, "wb") as f:

                    f.write('<?xml version="1.0" encoding="utf-8"?>'.encode("utf-8-sig"))

                    f.write(info_xml_str.encode("utf-8"))

            except Exception as e:

                print(f"Error syncing SaveGameInfo: {e}")

# Copy the editable player fields into the SaveGameInfo XML tree.
# It keeps save parsing, sanitization, and filesystem discovery consistent.
def sync_player_xml(target_elem, source_elem):

    s_player = Farmer(source_elem)

    t_player = Farmer(target_elem)

    t_player.name = s_player.name

    t_player.money = s_player.money

    t_player.maxHealth = s_player.maxHealth

    t_player.maxStamina = s_player.maxStamina

    t_player.gender = s_player.gender

    t_player.houseUpgradeLevel = s_player.houseUpgradeLevel

    t_player.totalMoneyEarned = s_player.totalMoneyEarned

    for i, exp in enumerate(s_player.experiencePoints):

        t_player.set_experience(i, exp)

    t_player.set_professions(s_player.get_professions())

    s_friend = source_elem.find("friendshipData")

    t_friend = target_elem.find("friendshipData")

    if s_friend is not None and t_friend is not None:

        for s_item in s_friend.findall("item"):

            s_key = s_item.find("key/string")

            s_val = s_item.find("value/Friendship/Points")

            if s_key is not None and s_val is not None:

                for t_item in t_friend.findall("item"):

                    t_key = t_item.find("key/string")

                    t_val = t_item.find("value/Friendship/Points")

                    if t_key is not None and t_key.text == s_key.text and t_val is not None:

                        t_val.text = s_val.text

                        break
