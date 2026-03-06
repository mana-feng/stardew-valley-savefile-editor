# Locate the game installation directory by checking registries and common install paths.
import os

import re

try:

    import winreg

except Exception:

    winreg = None

# Define the game path detector type used by this module.
# It keeps save parsing, sanitization, and filesystem discovery consistent.
class GamePathDetector:

    def __init__(self, log_callback=None):

        self.log = log_callback if log_callback else (lambda msg: None)

    # Detect the from registry.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    def detect_from_registry(self):

        if winreg is None:

            return []

        paths = []

        registry_keys = [

            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 413150", "InstallLocation"),

            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 413150", "InstallLocation"),

            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GOG.com\Games\1453375253", "PATH"),

            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\GOG.com\Games\1453375253", "PATH"),

            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),

        ]

        for root_key, sub_key, value_name in registry_keys:

            try:

                with winreg.OpenKey(root_key, sub_key) as key:

                    value, _ = winreg.QueryValueEx(key, value_name)

                    if value and os.path.exists(value):

                        if "SteamPath" in sub_key:

                            steam_path = value

                            appmanifest_path = os.path.join(steam_path, "steamapps", "appmanifest_413150.acf")

                            if os.path.exists(appmanifest_path):

                                game_dir = os.path.join(steam_path, "steamapps", "common", "Stardew Valley")

                                if self.is_valid_path(game_dir):

                                    paths.append(game_dir)

                                    self.log(f"Detected game path (Steam): {game_dir}")

                        else:

                            if self.is_valid_path(value):

                                paths.append(value)

                                self.log(f"Detected game path: {value}")

            except OSError:

                continue

        try:

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:

                steam_path, _ = winreg.QueryValueEx(key, "SteamPath")

                library_vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")

                if os.path.exists(library_vdf):

                    with open(library_vdf, "r", encoding="utf-8", errors="ignore") as f:

                        content = f.read()

                    for match in re.findall(r'"path"\s*"([^"]+)"', content):

                        library_path = match.replace("\\\\", "\\")

                        game_dir = os.path.join(library_path, "steamapps", "common", "Stardew Valley")

                        if self.is_valid_path(game_dir) and game_dir not in paths:

                            paths.append(game_dir)

                            self.log(f"Detected game path (library): {game_dir}")

        except OSError:

            pass

        return paths

    # Detect the common paths.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    def detect_common_paths(self):

        common_paths = [

            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Steam", "steamapps", "common", "Stardew Valley"),

            os.path.join(os.environ.get("ProgramFiles", ""), "Steam", "steamapps", "common", "Stardew Valley"),

            r"D:\SteamLibrary\steamapps\common\Stardew Valley",

            r"E:\SteamLibrary\steamapps\common\Stardew Valley",

            r"F:\SteamLibrary\steamapps\common\Stardew Valley",

            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "GOG Galaxy", "Games", "Stardew Valley"),

            r"C:\Program Files\GOG Galaxy\Games\Stardew Valley",

        ]

        result = []

        for path in common_paths:

            if self.is_valid_path(path) and path not in result:

                result.append(path)

        return result

    # Detect the all.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    def detect_all(self):

        all_paths = []

        all_paths.extend(self.detect_from_registry())

        all_paths.extend(self.detect_common_paths())

        unique = []

        for path in all_paths:

            if path not in unique:

                unique.append(path)

        return unique

    # Return whether the valid path flag is enabled.
    # It keeps save parsing, sanitization, and filesystem discovery consistent.
    @staticmethod

    def is_valid_path(game_path):

        return bool(game_path and os.path.exists(game_path) and os.path.exists(os.path.join(game_path, "Stardew Valley.exe")))
