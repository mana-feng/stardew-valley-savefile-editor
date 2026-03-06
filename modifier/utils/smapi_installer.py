# Install or remove SMAPI files and validate the game environment before mod operations.
import json

import os

import shutil

import sys

import tempfile

import zipfile

from pathlib import Path

# Define the SMAPI installer type used by this module.
# It supports mod discovery, backup, installation, and filesystem state checks.
class SmapiInstaller:

    BUNDLED_MOD_IDS = {"SMAPI.SaveBackup", "SMAPI.ConsoleCommands"}

    def __init__(self, game_path, log_callback=None, progress_callback=None):

        self.game_path = Path(game_path)

        self.log = log_callback if log_callback else (lambda msg: None)

        self.progress = progress_callback if progress_callback else (lambda val: None)

    # Return whether the installed flag is enabled.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    @staticmethod

    def is_installed(game_path):

        return (Path(game_path) / "StardewModdingAPI.exe").exists()

    # Return the SMAPI dat path.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _get_smapi_dat_path(self):

        if getattr(sys, "frozen", False):

            base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))

        else:

            base_path = Path(__file__).resolve().parents[1]

        return base_path / "Installer" / "SMAPI" / "install.dat"

    # Extract the packaged SMAPI installer bundle when it is available locally.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _extract_install_bundle(self):

        smapi_dat = self._get_smapi_dat_path()

        if not smapi_dat.exists():

            raise FileNotFoundError(f"SMAPI install.dat not found: {smapi_dat}")

        temp_root = Path(tempfile.mkdtemp(prefix="smapi_install_"))

        with zipfile.ZipFile(smapi_dat, "r") as zf:

            zf.extractall(temp_root)

        windows_dir = temp_root / "windows"

        return (windows_dir if windows_dir.exists() else temp_root), temp_root

    # Return whether the current file should be copied during installation.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    @staticmethod

    def _should_copy(path_obj: Path):

        return path_obj.name not in {"mcs", "Mods"}

    # Copy a directory tree while applying the installer file filter rules.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _recursive_copy(self, source: Path, target_parent: Path):

        target_parent.mkdir(parents=True, exist_ok=True)

        target = target_parent / source.name

        if source.is_dir():

            target.mkdir(parents=True, exist_ok=True)

            for child in source.iterdir():

                self._recursive_copy(child, target)

        else:

            shutil.copy2(source, target)

    # Load the manifest unique ID.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    @staticmethod

    def _load_manifest_unique_id(mod_dir: Path):

        manifest_path = mod_dir / "manifest.json"

        if not manifest_path.exists():

            return None

        try:

            with open(manifest_path, "r", encoding="utf-8") as f:

                data = json.load(f)

            unique_id = data.get("UniqueID")

            if isinstance(unique_id, str) and unique_id.strip():

                return unique_id.strip()

        except Exception:

            return None

        return None

    # Collect the installed mod folders.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _collect_installed_mod_folders(self, mods_dir: Path):

        result = {}

        if not mods_dir.exists():

            return result

        for entry in mods_dir.iterdir():

            if not entry.is_dir():

                continue

            unique_id = self._load_manifest_unique_id(entry)

            if unique_id:

                result[unique_id.lower()] = entry

        return result

    # Copy the bundled mods.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _copy_bundled_mods(self, bundle_dir: Path):

        bundled_mods_dir = bundle_dir / "Mods"

        mods_dir = self.game_path / "Mods"

        mods_dir.mkdir(parents=True, exist_ok=True)

        if not bundled_mods_dir.exists():

            return

        installed_by_id = self._collect_installed_mod_folders(mods_dir)

        for mod_source in bundled_mods_dir.iterdir():

            if not mod_source.is_dir():

                continue

            unique_id = self._load_manifest_unique_id(mod_source)

            if not unique_id:

                self.log(f"Skip invalid bundled mod: {mod_source.name}")

                continue

            if unique_id not in self.BUNDLED_MOD_IDS:

                self.log(f"Skip unknown bundled mod: {mod_source.name} ({unique_id})")

                continue

            existing = installed_by_id.get(unique_id.lower())

            target_dir = existing if existing else (mods_dir / mod_source.name)

            if target_dir.exists():

                shutil.rmtree(target_dir)

            shutil.copytree(mod_source, target_dir)

            self.log(f"Installed bundled mod: {target_dir.name}")

    # Return the uninstall paths.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _get_uninstall_paths(self):

        appdata = Path(os.environ.get("APPDATA", "")) / "StardewValley" / "ErrorLogs"

        rel_paths = [

            "StardewModdingAPI",

            "StardewModdingAPI.deps.json",

            "StardewModdingAPI.dll",

            "StardewModdingAPI.exe",

            "StardewModdingAPI.exe.config",

            "StardewModdingAPI.exe.mdb",

            "StardewModdingAPI.pdb",

            "StardewModdingAPI.runtimeconfig.json",

            "StardewModdingAPI.xml",

            "smapi-internal",

            "steam_appid.txt",

            "libgdiplus.dylib",

            os.path.join("Mods", ".cache"),

            os.path.join("Mods", "ErrorHandler"),

            os.path.join("Mods", "TrainerMod"),

            "Mono.Cecil.Rocks.dll",

            "StardewModdingAPI-settings.json",

            "StardewModdingAPI.AssemblyRewriters.dll",

            "0Harmony.dll",

            "0Harmony.pdb",

            "Mono.Cecil.dll",

            "Newtonsoft.Json.dll",

            "StardewModdingAPI.config.json",

            "StardewModdingAPI.crash.marker",

            "StardewModdingAPI.metadata.json",

            "StardewModdingAPI.update.marker",

            "StardewModdingAPI.Toolkit.dll",

            "StardewModdingAPI.Toolkit.pdb",

            "StardewModdingAPI.Toolkit.xml",

            "StardewModdingAPI.Toolkit.CoreInterfaces.dll",

            "StardewModdingAPI.Toolkit.CoreInterfaces.pdb",

            "StardewModdingAPI.Toolkit.CoreInterfaces.xml",

            "StardewModdingAPI-x64.exe",

        ]

        return [self.game_path / p for p in rel_paths] + [appdata]

    # Delete the target path when it already exists.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _delete_if_exists(self, path_obj: Path):

        if not path_obj.exists():

            return

        if path_obj.is_dir():

            shutil.rmtree(path_obj)

        else:

            path_obj.unlink()

        self.log(f"Removed: {path_obj}")

    # Remove the previous SMAPI files.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _remove_previous_smapi_files(self):

        for path_obj in self._get_uninstall_paths():

            self._delete_if_exists(path_obj)

    # Run the installation workflow for the current object.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def install(self):

        bundle_dir = None

        temp_root = None

        try:

            self.log("========== Start SMAPI install ==========")

            self.progress(0)

            bundle_dir, temp_root = self._extract_install_bundle()

            self.progress(20)

            self.log("Cleaning previous SMAPI files...")

            self._remove_previous_smapi_files()

            self.progress(45)

            self.log("Copying SMAPI core files...")

            for item in bundle_dir.iterdir():

                if not self._should_copy(item):

                    continue

                self._delete_if_exists(self.game_path / item.name)

                self._recursive_copy(item, self.game_path)

            self.progress(70)

            game_deps = self.game_path / "Stardew Valley.deps.json"

            smapi_deps = self.game_path / "StardewModdingAPI.deps.json"

            if game_deps.exists():

                shutil.copy2(game_deps, smapi_deps)

                self.log("Created StardewModdingAPI.deps.json")

            self._copy_bundled_mods(bundle_dir)

            self.progress(100)

            self.log("========== SMAPI install completed ==========")

            return True

        except Exception as e:

            self.log(f"SMAPI install failed: {e}")

            raise

        finally:

            if temp_root and temp_root.exists():

                shutil.rmtree(temp_root, ignore_errors=True)

    # Run the uninstall workflow for the current object.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def uninstall(self):

        try:

            self.log("========== Start SMAPI uninstall ==========")

            self.progress(0)

            self._remove_previous_smapi_files()

            self.progress(100)

            self.log("========== SMAPI uninstall completed ==========")

            return True

        except Exception as e:

            self.log(f"SMAPI uninstall failed: {e}")

            raise
