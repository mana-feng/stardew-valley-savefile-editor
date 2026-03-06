# Update Steam launch settings and registry values used by the SMAPI workflow.
import re

from pathlib import Path

import winreg

# Define the steam helper type used by this module.
# It supports mod discovery, backup, installation, and filesystem state checks.
class SteamHelper:

    APP_ID = "413150"

    def __init__(self, log_callback=None):

        self.log = log_callback if log_callback else (lambda msg: None)

    # Return the steam path.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _get_steam_path(self):

        keys = [

            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),

            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),

            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),

        ]

        for root, sub in keys:

            try:

                with winreg.OpenKey(root, sub) as key:

                    value, _ = winreg.QueryValueEx(key, "SteamPath")

                    if value:

                        return Path(value.replace("/", "\\"))

            except OSError:

                continue

        return None

    # Return the localconfig files.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _get_localconfig_files(self):

        steam_path = self._get_steam_path()

        if not steam_path:

            return []

        userdata = steam_path / "userdata"

        if not userdata.exists():

            return []

        files = []

        for user_dir in userdata.iterdir():

            if not user_dir.is_dir():

                continue

            cfg = user_dir / "config" / "localconfig.vdf"

            if cfg.exists():

                files.append(cfg)

        return files

    # Return the steam game path.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _get_steam_game_path(self):

        steam_path = self._get_steam_path()

        if not steam_path:

            return None

        candidates = []

        main = steam_path / "steamapps" / "common" / "Stardew Valley"

        candidates.append(main)

        lib_vdf = steam_path / "steamapps" / "libraryfolders.vdf"

        if lib_vdf.exists():

            try:

                text = lib_vdf.read_text(encoding="utf-8", errors="ignore")

                for match in re.finditer(r'"path"\s*"([^"]+)"', text):

                    raw = match.group(1).replace("\\\\", "\\")

                    p = Path(raw) / "steamapps" / "common" / "Stardew Valley"

                    candidates.append(p)

            except Exception:

                pass

        for p in candidates:

            if (p / "Stardew Valley.exe").exists():

                return p

        return None

    # Escape a value so it can be written back into a Steam VDF file.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    @staticmethod

    def _escape_vdf_value(value):

        return value.replace("\\", "\\\\").replace('"', '\\"')

    # Find the block range.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    @staticmethod

    def _find_block_range(lines, key):

        key_re = re.compile(r'^\s*"' + re.escape(key) + r'"\s*$')

        for i, line in enumerate(lines):

            if not key_re.match(line):

                continue

            j = i + 1

            while j < len(lines) and not lines[j].strip():

                j += 1

            if j >= len(lines) or "{" not in lines[j]:

                continue

            depth = lines[j].count("{") - lines[j].count("}")

            k = j + 1

            while k < len(lines):

                depth += lines[k].count("{") - lines[k].count("}")

                if depth == 0:

                    return i, k

                k += 1

        return None

    # Find the app block under apps.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _find_app_block_under_apps(self, lines, app_id):

        apps_range = self._find_block_range(lines, "apps")

        if not apps_range:

            return None

        apps_start, apps_end = apps_range

        key_re = re.compile(r'^\s*"' + re.escape(app_id) + r'"\s*$')

        i = apps_start + 1

        while i < apps_end:

            if not key_re.match(lines[i]):

                i += 1

                continue

            j = i + 1

            while j < apps_end and not lines[j].strip():

                j += 1

            if j >= apps_end or "{" not in lines[j]:

                i += 1

                continue

            depth = lines[j].count("{") - lines[j].count("}")

            k = j + 1

            while k <= apps_end:

                depth += lines[k].count("{") - lines[k].count("}")

                if depth == 0:

                    return i, k

                k += 1

            break

        return None

    # Set the or remove launch options.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def _set_or_remove_launch_options(self, text, launch_value=None, remove=False):

        newline = "\r\n" if "\r\n" in text else "\n"

        lines = text.splitlines(keepends=True)

        app_range = self._find_app_block_under_apps(lines, self.APP_ID)

        if not app_range:

            app_range = self._find_block_range(lines, self.APP_ID)

        changed = False

        if app_range:

            app_start, app_end = app_range

            launch_idx = None

            for idx in range(app_start, app_end + 1):

                if '"LaunchOptions"' in lines[idx]:

                    launch_idx = idx

                    break

            if remove:

                if launch_idx is not None and "StardewModdingAPI.exe" in lines[launch_idx]:

                    del lines[launch_idx]

                    changed = True

            else:

                indent = re.match(r"^(\s*)", lines[app_start]).group(1) + "\t"

                new_line = f'{indent}"LaunchOptions"\t\t"{self._escape_vdf_value(launch_value)}"{newline}'

                if launch_idx is not None:

                    if lines[launch_idx] != new_line:

                        lines[launch_idx] = new_line

                        changed = True

                else:

                    lines.insert(app_end, new_line)

                    changed = True

        elif not remove and launch_value:

            apps_range = self._find_block_range(lines, "apps")

            if apps_range:

                apps_start, apps_end = apps_range

                apps_indent = re.match(r"^(\s*)", lines[apps_start]).group(1)

                block_indent = apps_indent + "\t"

                v = self._escape_vdf_value(launch_value)

                block = [

                    f'{block_indent}"{self.APP_ID}"{newline}',

                    f"{block_indent}" + "{" + newline,

                    f'{block_indent}\t"LaunchOptions"\t\t"{v}"{newline}',

                    f"{block_indent}" + "}" + newline,

                ]

                lines[apps_end:apps_end] = block

                changed = True

        return "".join(lines), changed

    # Initialize the achievement metadata used by the Steam integration helpers.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def setup_achievements(self, game_path):

        preferred = Path(game_path) / "StardewModdingAPI.exe"

        steam_game = self._get_steam_game_path()

        steam_path_candidate = (steam_game / "StardewModdingAPI.exe") if steam_game else None

        smapi_exe = preferred

        if preferred.exists():

            smapi_exe = preferred

        elif steam_path_candidate and steam_path_candidate.exists():

            smapi_exe = steam_path_candidate

        else:

            self.log("StardewModdingAPI.exe was not found; Steam launch options will still be written. Verify the install path.")

        target = f'"{smapi_exe}" %command%'

        updated = 0

        for cfg in self._get_localconfig_files():

            try:

                text = cfg.read_text(encoding="utf-8", errors="ignore")

                new_text, changed = self._set_or_remove_launch_options(text, launch_value=target, remove=False)

                if changed:

                    cfg.write_text(new_text, encoding="utf-8")

                    updated += 1

            except Exception as e:

                self.log(f"Failed to update Steam launch options: {cfg} ({e})")

        if updated > 0:

            self.log(f"Steam launch options updated automatically ({updated} user config files).")

            return True

        self.log("No writable Steam user config was found; launch options were not changed.")

        return False

    # Remove the Stardew Valley launch options managed by this project.
    # It supports mod discovery, backup, installation, and filesystem state checks.
    def clear_launch_options(self):

        updated = 0

        for cfg in self._get_localconfig_files():

            try:

                text = cfg.read_text(encoding="utf-8", errors="ignore")

                new_text, changed = self._set_or_remove_launch_options(text, remove=True)

                if changed:

                    cfg.write_text(new_text, encoding="utf-8")

                    updated += 1

            except Exception as e:

                self.log(f"Failed to clear Steam launch options: {cfg} ({e})")

        if updated > 0:

            self.log(f"Steam launch options removed automatically ({updated} user config files).")

            return True

        self.log("No Steam launch options needed to be removed.")

        return False
