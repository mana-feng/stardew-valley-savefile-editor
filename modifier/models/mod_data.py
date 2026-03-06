
# Discover local and installed mods, then coordinate install, backup, and toggle operations.
import os

import json

import shutil

import zipfile

from dataclasses import dataclass

from typing import List, Optional, Dict, Callable

from utils import tr

COMMON_MODS = {

    "quality_of_life": [

        {"id": "CJBAutomation", "name": "CJB Automation", "desc": "è‡ªåŠ¨æ”¶é›†ã€è‡ªåŠ¨æµ‡æ°´ç­‰è‡ªåŠ¨åŒ–åŠŸèƒ½"},

        {"id": "CJBCheatsMenu", "name": "CJB Cheats Menu", "desc": "æ¸¸æˆå†…ä½œå¼Šèœå•"},

        {"id": "CJBItemSpawner", "name": "CJB Item Spawner", "desc": "ç‰©å“ç”Ÿæˆå™¨"},

        {"id": "CJBShowItemSellPrice", "name": "CJB Show Item Sell Price", "desc": "æ˜¾ç¤ºç‰©å“å”®ä»·"},

        {"id": "SkipIntro", "name": "Skip Intro", "desc": "è·³è¿‡å¼€åœºåŠ¨ç”»"},

        {"id": "AutoGate", "name": "Auto Gate", "desc": "è‡ªåŠ¨å¼€å…³æ …æ é—¨"},

        {"id": "AutoAnimalDoor", "name": "Auto Animal Door", "desc": "è‡ªåŠ¨å¼€å…³ç•œæ£š/é¸¡èˆé—¨"},

        {"id": "BetterRanching", "name": "Better Ranching", "desc": "æ›´å¥½çš„ç‰§åœºç®¡ç†"},

    ],

    "visual": [

        {"id": "UIInfoSuite2", "name": "UI Info Suite 2", "desc": "æ˜¾ç¤ºæ›´å¤šæ¸¸æˆä¿¡æ¯ï¼ˆè¿æ°”ã€ä½œç‰©æˆç†Ÿæ—¶é—´ç­‰ï¼‰"},

        {"id": "NPCMapLocations", "name": "NPC Map Locations", "desc": "åœ¨åœ°å›¾ä¸Šæ˜¾ç¤ºNPCä½ç½®"},

        {"id": "LookupAnything", "name": "Lookup Anything", "desc": "æŸ¥çœ‹ä»»ä½•ç‰©å“çš„è¯¦ç»†ä¿¡æ¯"},

        {"id": "GiftTasteHelper", "name": "Gift Taste Helper", "desc": "æ˜¾ç¤ºNPCç¤¼ç‰©å–œå¥½"},

        {"id": "BetterFriendship", "name": "Better Friendship", "desc": "æ›´å¥½çš„å‹è°Šç³»ç»Ÿæ˜¾ç¤º"},

        {"id": "EventLookup", "name": "Event Lookup", "desc": "æŸ¥çœ‹äº‹ä»¶è§¦å‘æ¡ä»¶"},

    ],

    "gameplay": [

        {"id": "StardewValleyExpanded", "name": "Stardew Valley Expanded", "desc": "å¤§åž‹æ‰©å±•Modï¼Œæ–°å¢žåœ°å›¾ã€NPCã€å‰§æƒ…"},

        {"id": "RidgesideVillage", "name": "Ridgeside Village", "desc": "å¤§åž‹æ‰©å±•Modï¼Œæ–°å¢žæ‘åº„å’ŒNPC"},

        {"id": "EastScarp", "name": "East Scarp", "desc": "ä¸œéƒ¨æ‚¬å´–æ‰©å±•åŒºåŸŸ"},

        {"id": "AdventurerGuildExpanded", "name": "Adventurer's Guild Expanded", "desc": "æŽ¢é™©å®¶å…¬ä¼šæ‰©å±•"},

        {"id": "DeepWoods", "name": "Deep Woods", "desc": "æ·±é‚ƒæ£®æž—æ‰©å±•"},

        {"id": "Magic", "name": "Stardew Valley Magic", "desc": "é­”æ³•ç³»ç»ŸMod"},

        {"id": "SocializingSkill", "name": "Socializing Skill", "desc": "ç¤¾äº¤æŠ€èƒ½Mod"},

        {"id": "LuckSkill", "name": "Luck Skill", "desc": "è¿æ°”æŠ€èƒ½Mod"},

        {"id": "BinningSkill", "name": "Binning Skill", "desc": "åžƒåœ¾æ¡¶æŠ€èƒ½Mod"},

        {"id": "CookingSkill", "name": "Cooking Skill", "desc": "çƒ¹é¥ªæŠ€èƒ½Mod"},

    ],

    "farming": [

        {"id": "BetterJunimos", "name": "Better Junimos", "desc": "æ›´å¥½çš„ç¥å°¼é­”å°å±‹"},

        {"id": "JunimosAcceptCash", "name": "Junimos Accept Cash", "desc": "ç¥å°¼é­”æŽ¥å—é‡‘é’±æ”¯ä»˜"},

        {"id": "Automate", "name": "Automate", "desc": "è‡ªåŠ¨åŒ–æœºå™¨ç³»ç»Ÿ"},

        {"id": "BetterSprinklers", "name": "Better Sprinklers", "desc": "æ›´å¥½çš„æ´’æ°´å™¨èŒƒå›´"},

        {"id": "SmartBuilding", "name": "Smart Building", "desc": "æ™ºèƒ½å»ºç­‘ç³»ç»Ÿ"},

        {"id": "GreenhouseGatherers", "name": "Greenhouse Gatherers", "desc": "æ¸©å®¤æ”¶é›†è€…"},

        {"id": "CustomFarmingRedux", "name": "Custom Farming Redux", "desc": "è‡ªå®šä¹‰å†œä¸šæœºæ¢°"},

    ],

    "inventory": [

        {"id": "ChestsAnywhere", "name": "Chests Anywhere", "desc": "éšæ—¶éšåœ°è®¿é—®ç®±å­"},

        {"id": "CarryChest", "name": "Carry Chest", "desc": "å¯ä»¥æºå¸¦ç®±å­"},

        {"id": "StackSplitX", "name": "Stack Split X", "desc": "æ›´å¥½çš„ç‰©å“åˆ†å‰²"},

        {"id": "BetterChests", "name": "Better Chests", "desc": "æ›´å¥½çš„ç®±å­åŠŸèƒ½"},

        {"id": "RemoteFridgeStorage", "name": "Remote Fridge Storage", "desc": "è¿œç¨‹å†°ç®±å­˜å‚¨"},

        {"id": "InfiniteStorage", "name": "Infinite Storage", "desc": "æ— é™å­˜å‚¨ç©ºé—´"},

    ],

    "fishing": [

        {"id": "TehsFishingOverhaul", "name": "Teh's Fishing Overhaul", "desc": "é’“é±¼ç³»ç»Ÿå…¨é¢æ”¹è¿›"},

        {"id": "FishingInfoOverlays", "name": "Fishing Info Overlays", "desc": "é’“é±¼ä¿¡æ¯æ˜¾ç¤º"},

        {"id": "SkipFishingMinigame", "name": "Skip Fishing Minigame", "desc": "è·³è¿‡é’“é±¼å°æ¸¸æˆ"},

        {"id": "AutoFish", "name": "Auto Fish", "desc": "è‡ªåŠ¨é’“é±¼"},

    ],

    "mining_combat": [

        {"id": "CombatControls", "name": "Combat Controls", "desc": "æˆ˜æ–—æŽ§åˆ¶æ”¹è¿›"},

        {"id": "BetterSlingshots", "name": "Better Slingshots", "desc": "æ›´å¥½çš„å¼¹å¼“"},

        {"id": "MoreRings", "name": "More Rings", "desc": "æ›´å¤šæˆ’æŒ‡æ§½ä½"},

        {"id": "DualWield", "name": "Dual Wield", "desc": "åŒæŒæ­¦å™¨"},

        {"id": "MineAssist", "name": "Mine Assist", "desc": "çŸ¿äº•è¾…åŠ©åŠŸèƒ½"},

        {"id": "SkullCavernElevator", "name": "Skull Cavern Elevator", "desc": "éª·é«…æ´žç©´ç”µæ¢¯"},

    ],

    "misc": [

        {"id": "CustomMusic", "name": "Custom Music", "desc": "è‡ªå®šä¹‰éŸ³ä¹"},

        {"id": "CustomPortraits", "name": "Custom Portraits", "desc": "è‡ªå®šä¹‰è§’è‰²ç«‹ç»˜"},

        {"id": "SeasonalOutfits", "name": "Seasonal Outfits", "desc": "å­£èŠ‚æ€§æœè£…"},

        {"id": "AnimePortraits", "name": "Anime Portraits", "desc": "åŠ¨æ¼«é£Žæ ¼ç«‹ç»˜"},

        {"id": "ElleTownBuildings", "name": "Elle's Town Buildings", "desc": "åŸŽé•‡å»ºç­‘ç¾ŽåŒ–"},

        {"id": "Recolor", "name": "Recolor Mods", "desc": "åœ°å›¾é‡æ–°ç€è‰²"},

    ],

}

MOD_CONFIG_TEMPLATES = {

    "CJBAutomation": {

        "AutoHarvest": True,

        "AutoWater": True,

        "AutoPet": True,

        "AutoCollect": True,

    },

    "BetterJunimos": {

        "WorkInRain": True,

        "WorkInWinter": True,

        "WorkEvenings": True,

        "InfiniteRange": False,

    },

    "Automate": {

        "Enabled": True,

        "MachineDelay": 0,

        "ChestPriority": 0,

    },

}

SMAPI_CONFIG = {

    "CheckForUpdates": True,

    "ShowUpdateInWindowTitle": True,

    "VerboseLogging": False,

    "RewriteInParallel": True,

    "UseBetaChannel": False,

}

# Define the mod info type used by this module.
# It supports mod discovery, backup, installation, and filesystem state checks.
@dataclass

class ModInfo:

    name: str

    version: str

    description: str

    author: str

    unique_id: str

    file_path: str

    is_local_available: bool = False

    is_installed: bool = False

    is_enabled: bool = True

    installed_folder: str = ""

    # Create a mod record from a parsed SMAPI manifest.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    @classmethod

    def from_manifest(cls, manifest_path: str, file_path: str = None) -> Optional['ModInfo']:

        try:

            with open(manifest_path, 'r', encoding='utf-8') as f:

                data = json.load(f)

            return cls(

                name=data.get('Name', 'Unknown'),

                version=data.get('Version', '1.0.0'),

                description=data.get('Description', ''),

                author=data.get('Author', 'Unknown'),

                unique_id=data.get('UniqueID', ''),

                file_path=file_path or os.path.dirname(manifest_path),

                is_local_available=False,

                is_installed=False,

                is_enabled=True

            )

        except Exception:

            return None

    # Return the folder name.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def get_folder_name(self) -> str:

        if self.installed_folder:

            return self.installed_folder

        if self.file_path and os.path.isdir(self.file_path):

            return os.path.basename(os.path.normpath(self.file_path))

        return self.name

    # Serialize the current object to a plain dictionary.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def to_dict(self) -> dict:

        return {

            'name': self.name,

            'version': self.version,

            'description': self.description,

            'author': self.author,

            'unique_id': self.unique_id,

            'file_path': self.file_path,

            'is_local_available': self.is_local_available,

            'is_installed': self.is_installed,

            'is_enabled': self.is_enabled,

            'installed_folder': self.installed_folder

        }

    # Create an object from a plain dictionary.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    @classmethod

    def from_dict(cls, data: dict) -> 'ModInfo':

        return cls(

            name=data.get('name', 'Unknown'),

            version=data.get('version', '1.0.0'),

            description=data.get('description', ''),

            author=data.get('author', 'Unknown'),

            unique_id=data.get('unique_id', ''),

            file_path=data.get('file_path', ''),

            is_local_available=data.get('is_local_available', False),

            is_installed=data.get('is_installed', False),

            is_enabled=data.get('is_enabled', True),

            installed_folder=data.get('installed_folder', '')

        )

# Define the mod scanner type used by this module.
# It supports mod discovery, backup, installation, and filesystem state checks.
class ModScanner:

    def __init__(self, log_callback=None):

        self.log = log_callback if log_callback else lambda msg: None

    # Return a stable identity key for the current mod entry.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    @staticmethod
    def _get_mod_identity(mod: ModInfo) -> str:

        if mod.unique_id:

            return f"id:{mod.unique_id.strip().lower()}"

        name = (mod.name or "").strip().lower()

        author = (mod.author or "").strip().lower()

        if name or author:

            return f"name:{author}|{name}"

        folder = mod.installed_folder or os.path.basename(os.path.normpath(mod.file_path or ""))

        return f"path:{folder.strip().lower()}"

    # Return the mods source dir.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def get_mods_source_dir(self) -> str:

        import sys

        if getattr(sys, 'frozen', False):

            return os.path.dirname(sys.executable)

        else:

            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Return the mods packed dir.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def get_mods_packed_dir(self) -> str:

        source_dir = self.get_mods_source_dir()

        parent_dir = os.path.dirname(source_dir)

        candidates = [

            os.path.join(source_dir, "mods"),

            os.path.join(source_dir, "Mods"),

            os.path.join(source_dir, "Mod", "SplitMods"),

            os.path.join(source_dir, "Mod"),

            os.path.join(source_dir, "Installer", "Mods"),

            os.path.join(parent_dir, "mods"),

            os.path.join(parent_dir, "Mods"),

            os.path.join(parent_dir, "Mod", "SplitMods"),

            os.path.join(parent_dir, "Mod"),

        ]

        for path in candidates:

            if os.path.exists(path):

                self.log(tr.translate("mods_source_dir_used").format(path=path))

                return path

        default_dir = os.path.join(source_dir, "mods")

        os.makedirs(default_dir, exist_ok=True)

        self.log(tr.translate("mods_source_dir_created").format(path=default_dir))

        return default_dir

    # Scan the packed mods.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def scan_packed_mods(self) -> List[ModInfo]:

        mods = []

        seen_ids = set()

        packed_dir = self.get_mods_packed_dir()

        if not os.path.exists(packed_dir):

            self.log(tr.translate("mods_source_dir_missing").format(path=packed_dir))

            return mods

        for root, dirs, files in os.walk(packed_dir):

            dirs[:] = [d for d in dirs if d.lower() not in {"bin", "obj", ".git", "__pycache__"}]

            if "manifest.json" in files:

                manifest_path = os.path.join(root, "manifest.json")

                mod_info = ModInfo.from_manifest(manifest_path, root)

                if mod_info:

                    identity = self._get_mod_identity(mod_info)

                    if identity in seen_ids:

                        dirs[:] = []

                        continue

                    mod_info.is_local_available = True

                    seen_ids.add(identity)

                    mods.append(mod_info)

                    self.log(tr.translate("mod_found").format(name=mod_info.name, version=mod_info.version))

                dirs[:] = []

        for item in os.listdir(packed_dir):

            item_path = os.path.join(packed_dir, item)

            if os.path.isfile(item_path) and (item.endswith('.zip') or item.endswith('.sdvmod')):

                mod_info = self._scan_packed_mod(item_path)

                if mod_info:

                    identity = self._get_mod_identity(mod_info)

                    if identity in seen_ids:

                        continue

                    mod_info.is_local_available = True

                    seen_ids.add(identity)

                    mods.append(mod_info)

                    self.log(tr.translate("mod_archive_found").format(name=mod_info.name, version=mod_info.version))

        return mods

    # Scan the packed mod.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _scan_packed_mod(self, file_path: str) -> Optional[ModInfo]:

        try:

            with zipfile.ZipFile(file_path, 'r') as zf:

                manifest_files = [f for f in zf.namelist() if f.endswith('manifest.json')]

                if not manifest_files:

                    return None

                manifest_path = manifest_files[0]

                with zf.open(manifest_path) as f:

                    data = json.load(f)

                return ModInfo(

                    name=data.get('Name', 'Unknown'),

                    version=data.get('Version', '1.0.0'),

                    description=data.get('Description', ''),

                    author=data.get('Author', 'Unknown'),

                    unique_id=data.get('UniqueID', ''),

                    file_path=file_path,

                    is_local_available=False,

                    is_installed=False,

                    is_enabled=True

                )

        except Exception as e:

            self.log(tr.translate("mod_archive_scan_failed").format(path=file_path, error=e))

            return None

    # Scan the installed mods.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def scan_installed_mods(self, game_path: str) -> Dict[str, dict]:

        installed = {}

        for mod_info in self.scan_installed_mod_infos(game_path):

            if mod_info.unique_id:

                installed[mod_info.unique_id] = {

                    "enabled": mod_info.is_enabled,

                    "folder": mod_info.installed_folder or os.path.basename(mod_info.file_path),

                }

        return installed

    # Scan the installed mod infos.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def scan_installed_mod_infos(self, game_path: str) -> List[ModInfo]:

        installed = []

        if not game_path:

            return installed

        if not os.path.exists(os.path.join(game_path, "Stardew Valley.exe")):

            return installed

        mods_dir = os.path.join(game_path, "Mods")

        if not os.path.exists(mods_dir):

            return installed

        for item in os.listdir(mods_dir):

            item_path = os.path.join(mods_dir, item)

            if os.path.isdir(item_path):

                manifest_path = os.path.join(item_path, "manifest.json")

                if os.path.exists(manifest_path):

                    mod_info = ModInfo.from_manifest(manifest_path, item_path)

                    if mod_info:

                        mod_info.is_installed = True

                        mod_info.is_enabled = not os.path.exists(os.path.join(item_path, "disabled"))

                        mod_info.installed_folder = item

                        installed.append(mod_info)

        return installed

# Coordinate application state and filesystem operations for this feature area.
# It supports mod discovery, backup, installation, and filesystem state checks.
class ModManager:

    def __init__(self, game_path: str, log_callback: Callable = None, progress_callback: Callable = None):

        self.game_path = game_path

        self.log = log_callback if log_callback else lambda msg: None

        self.progress = progress_callback if progress_callback else lambda val: None

        self.scanner = ModScanner(log_callback=log_callback)

        self.available_mods: List[ModInfo] = []

    # Return the mods directory.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def get_mods_directory(self) -> str:

        return os.path.join(self.game_path, "Mods")

    # Refresh the mods.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def refresh_mods(self) -> List[ModInfo]:

        local_mods = self.scanner.scan_packed_mods()

        installed_mods = self.scanner.scan_installed_mod_infos(self.game_path)

        merged_mods: Dict[str, ModInfo] = {}

        for mod in local_mods:

            merged_mods[self._get_mod_identity(mod)] = mod

        for installed_mod in installed_mods:

            identity = self._get_mod_identity(installed_mod)

            existing = merged_mods.get(identity)

            if existing is None:

                installed_mod.is_local_available = False

                merged_mods[identity] = installed_mod

                continue

            existing.is_installed = True

            existing.is_enabled = installed_mod.is_enabled

            existing.installed_folder = installed_mod.installed_folder

            if not existing.unique_id:

                existing.unique_id = installed_mod.unique_id

            if not existing.description and installed_mod.description:

                existing.description = installed_mod.description

            if not existing.author and installed_mod.author:

                existing.author = installed_mod.author

            if not existing.version and installed_mod.version:

                existing.version = installed_mod.version

        self.available_mods = sorted(

            merged_mods.values(),

            key=lambda mod: ((mod.name or "").lower(), (mod.author or "").lower(), (mod.unique_id or "").lower()),

        )

        return self.available_mods

    # Return the local source directory.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def get_local_source_directory(self) -> str:

        return self.scanner.get_mods_packed_dir()

    # Return a stable identity key for the current mod entry.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    @staticmethod

    def _get_mod_identity(mod: ModInfo) -> str:

        if mod.unique_id:

            return f"id:{mod.unique_id.strip().lower()}"

        name = (mod.name or "").strip().lower()

        author = (mod.author or "").strip().lower()

        if name or author:

            return f"name:{author}|{name}"

        folder = mod.installed_folder or os.path.basename(os.path.normpath(mod.file_path or ""))

        return f"path:{folder.strip().lower()}"

    # Find the installed folder by unique ID.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _find_installed_folder_by_unique_id(self, unique_id: str) -> Optional[str]:

        if not unique_id:

            return None

        mods_dir = self.get_mods_directory()

        if not os.path.isdir(mods_dir):

            return None

        for item in os.listdir(mods_dir):

            item_path = os.path.join(mods_dir, item)

            manifest_path = os.path.join(item_path, "manifest.json")

            if not os.path.isdir(item_path) or not os.path.exists(manifest_path):

                continue

            try:

                with open(manifest_path, 'r', encoding='utf-8') as f:

                    data = json.load(f)

                if data.get("UniqueID", "") == unique_id:

                    return item

            except Exception:

                continue

        return None

    # Resolve the installed mod dir.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _resolve_installed_mod_dir(self, mod: ModInfo) -> Optional[str]:

        mods_dir = self.get_mods_directory()

        if not os.path.isdir(mods_dir):

            return None

        candidate_names = []

        for folder_name in (mod.installed_folder, mod.get_folder_name()):

            if folder_name and folder_name not in candidate_names:

                candidate_names.append(folder_name)

        for folder_name in candidate_names:

            target_dir = os.path.join(mods_dir, folder_name)

            if not os.path.isdir(target_dir):

                continue

            if not mod.unique_id:

                mod.installed_folder = folder_name

                return target_dir

            manifest_path = os.path.join(target_dir, "manifest.json")

            if not os.path.exists(manifest_path):

                continue

            try:

                with open(manifest_path, 'r', encoding='utf-8') as f:

                    data = json.load(f)

                if data.get("UniqueID", "") == mod.unique_id:

                    mod.installed_folder = folder_name

                    return target_dir

            except Exception:

                continue

        real_folder = self._find_installed_folder_by_unique_id(mod.unique_id)

        if real_folder:

            mod.installed_folder = real_folder

            return os.path.join(mods_dir, real_folder)

        return None

    # Create a unique backup directory name for a copied mod.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    @staticmethod

    def _make_unique_backup_dir(target_dir: str) -> str:

        if not os.path.exists(target_dir):

            return target_dir

        suffix = 2

        while True:

            candidate = f"{target_dir}_{suffix}"

            if not os.path.exists(candidate):

                return candidate

            suffix += 1

    # Back up installed mods that are missing from the local source library.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def backup_missing_installed_mods(self) -> List[ModInfo]:

        source_dir = self.get_local_source_directory()

        local_mods = self.scanner.scan_packed_mods()

        local_unique_ids = {mod.unique_id for mod in local_mods if mod.unique_id}

        installed_mods = self.scanner.scan_installed_mod_infos(self.game_path)

        backed_up = []

        for mod in installed_mods:

            if not mod.unique_id or mod.unique_id in local_unique_ids:

                continue

            installed_dir = self._resolve_installed_mod_dir(mod)

            if not installed_dir:

                self.log(tr.translate("backup_skip_missing_folder").format(name=mod.name))

                continue

            target_name = mod.installed_folder or os.path.basename(installed_dir) or mod.get_folder_name()

            target_dir = self._make_unique_backup_dir(os.path.join(source_dir, target_name))

            shutil.copytree(

                installed_dir,

                target_dir,

                ignore=shutil.ignore_patterns("__pycache__", "disabled"),

            )

            local_unique_ids.add(mod.unique_id)

            backed_up.append(mod)

            self.log(tr.translate("mod_backed_up").format(name=mod.name, path=target_dir))

        return backed_up

    # Return the mod by ID.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def get_mod_by_id(self, unique_id: str) -> Optional[ModInfo]:

        for mod in self.available_mods:

            if mod.unique_id == unique_id:

                return mod

        return None

    # Return the mod by name.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def get_mod_by_name(self, name: str) -> Optional[ModInfo]:

        for mod in self.available_mods:

            if mod.name == name:

                return mod

        return None

    # Return whether the SMAPI installed flag is enabled.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def is_smapi_installed(self) -> bool:

        smapi_exe = os.path.join(self.game_path, "StardewModdingAPI.exe")

        return os.path.exists(smapi_exe)

    # Install the mod.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def install_mod(self, mod: ModInfo) -> bool:

        if not self.is_smapi_installed():

            self.log(tr.translate("smapi_install_required"))

            return False

        try:

            self.log(tr.translate("mod_install_begin_banner").format(name=mod.name))

            self.progress(0)

            mods_dir = self.get_mods_directory()

            if not os.path.exists(mods_dir):

                os.makedirs(mods_dir)

                self.log(tr.translate("mods_game_dir_created").format(path=mods_dir))

            target_dir = os.path.join(mods_dir, mod.get_folder_name())

            self.progress(20)

            if os.path.isdir(mod.file_path):

                self._install_from_folder(mod.file_path, target_dir)

            elif mod.file_path.endswith(('.zip', '.sdvmod')):

                self._install_from_archive(mod.file_path, target_dir)

            else:

                raise Exception(f"ä¸æ”¯æŒçš„Modæ ¼å¼: {mod.file_path}")

            self.progress(100)

            mod.is_installed = True

            mod.is_enabled = True

            self.log(tr.translate("mod_install_done_banner").format(name=mod.name))

            return True

        except Exception as e:

            self.log(tr.translate("mod_install_failed_with_error").format(error=e))

            raise

    # Install the from folder.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _install_from_folder(self, source_dir: str, target_dir: str):

        if os.path.exists(target_dir):

            shutil.rmtree(target_dir)

        shutil.copytree(source_dir, target_dir)

        self.log(tr.translate("mod_install_copy_folder").format(source=source_dir, target=target_dir))

    # Install the from archive.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _install_from_archive(self, archive_path: str, target_dir: str):

        if os.path.exists(target_dir):

            shutil.rmtree(target_dir)

        os.makedirs(target_dir)

        with zipfile.ZipFile(archive_path, 'r') as zf:

            members = zf.namelist()

            if members and members[0].endswith('/'):

                prefix = members[0]

                members = [m for m in members if not m.endswith('/')]

                for member in members:

                    relative_path = member[len(prefix):]

                    if relative_path:

                        target_path = os.path.join(target_dir, relative_path)

                        os.makedirs(os.path.dirname(target_path), exist_ok=True)

                        with zf.open(member) as source, open(target_path, 'wb') as target:

                            target.write(source.read())

            else:

                zf.extractall(target_dir)

        self.log(tr.translate("mod_install_extract_archive").format(source=archive_path, target=target_dir))

    # Uninstall the mod.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def uninstall_mod(self, mod: ModInfo) -> bool:

        try:

            self.log(tr.translate("mod_uninstall_begin_banner").format(name=mod.name))

            self.progress(0)

            target_dir = self._resolve_installed_mod_dir(mod)

            if not target_dir:

                self.log(tr.translate("mod_not_installed_or_missing_dir").format(name=mod.name))

                return False

            self.progress(50)

            shutil.rmtree(target_dir)

            self.log(tr.translate("mod_removed_dir").format(path=target_dir))

            self.progress(100)

            mod.is_installed = False

            mod.is_enabled = True

            self.log(tr.translate("mod_uninstall_done_banner").format(name=mod.name))

            return True

        except Exception as e:

            self.log(tr.translate("mod_uninstall_failed_with_error").format(error=e))

            raise

    # Enable the mod.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def enable_mod(self, mod: ModInfo) -> bool:

        if not mod.is_installed:

            self.log(tr.translate("mod_not_installed").format(name=mod.name))

            return False

        target_dir = self._resolve_installed_mod_dir(mod)

        if not target_dir:

            self.log(tr.translate("mod_enable_dir_missing").format(name=mod.name))

            return False

        disabled_file = os.path.join(target_dir, "disabled")

        if os.path.exists(disabled_file):

            os.remove(disabled_file)

            self.log(tr.translate("mod_enabled_log").format(name=mod.name))

        else:

            self.log(tr.translate("mod_already_enabled").format(name=mod.name))

        mod.is_enabled = True

        return True

    # Disable the mod.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def disable_mod(self, mod: ModInfo) -> bool:

        if not mod.is_installed:

            self.log(tr.translate("mod_not_installed").format(name=mod.name))

            return False

        target_dir = self._resolve_installed_mod_dir(mod)

        if not target_dir:

            self.log(tr.translate("mod_disable_dir_missing").format(name=mod.name))

            return False

        disabled_file = os.path.join(target_dir, "disabled")

        if not os.path.exists(disabled_file):

            with open(disabled_file, 'w') as f:

                f.write("")

            self.log(tr.translate("mod_disabled_log").format(name=mod.name))

        else:

            self.log(tr.translate("mod_already_disabled").format(name=mod.name))

        mod.is_enabled = False

        return True

    # Toggle the mod.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def toggle_mod(self, mod: ModInfo) -> bool:

        if mod.is_enabled:

            return self.disable_mod(mod)

        else:

            return self.enable_mod(mod)

# Return the mods by category.
# It supports mod discovery, backup, installation, and filesystem state checks.
def get_mods_by_category(category):

    return COMMON_MODS.get(category, [])

# Return every curated mod definition across all categories.
# It supports mod discovery, backup, installation, and filesystem state checks.
def get_all_mods():

    all_mods = []

    for category, mods in COMMON_MODS.items():

        for mod in mods:

            all_mods.append({

                **mod,

                "category": category

            })

    return all_mods

# Return the mod categories.
# It supports mod discovery, backup, installation, and filesystem state checks.
def get_mod_categories():

    return list(COMMON_MODS.keys())
