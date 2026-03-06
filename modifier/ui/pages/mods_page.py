# Build the mods page and coordinate local mod management workflows for the UI.
import os

import subprocess

import time

import tkinter as tk

from tkinter import filedialog, messagebox, ttk

from utils import tr

from utils.smapi_installer import SmapiInstaller

from ..helpers import setup_mousewheel

# Provide page-specific UI builders and behaviors that are mixed into the main editor window.
# It keeps tab-specific widgets synchronized with the current save model and editor state.
class ModsPageMixin:

    # Build the mods tab.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def build_mods_tab(self, main_notebook):

        mods_tab = ttk.Frame(main_notebook)

        main_notebook.add(mods_tab, text=tr.translate("mods_tab"))

        mod_frame = ttk.Frame(mods_tab, padding=15)

        mod_frame.pack(fill=tk.BOTH, expand=True)

        path_frame = ttk.Frame(mod_frame)

        path_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(path_frame, text=tr.translate("mods_game_path")).pack(side=tk.LEFT, padx=(0, 5))

        self.game_path_var = tk.StringVar(value="")

        path_entry = ttk.Entry(path_frame, textvariable=self.game_path_var, width=60)

        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        path_entry.bind("<KeyRelease>", lambda e: self._update_smapi_buttons())

        ttk.Button(path_frame, text=tr.translate("browse"), command=self._select_game_path).pack(side=tk.LEFT, padx=5)

        action_frame = ttk.Frame(mod_frame)

        action_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(action_frame, text=tr.translate("refresh_mod_list"), command=self._refresh_mods).pack(side=tk.LEFT, padx=5)

        self.backup_mods_btn = ttk.Button(action_frame, text=tr.translate("backup_missing_mods"), command=self._backup_missing_mods)

        self.backup_mods_btn.pack(side=tk.LEFT, padx=5)

        self.install_smapi_btn = ttk.Button(action_frame, text=tr.translate("install_smapi"), command=self._install_smapi)

        self.install_smapi_btn.pack(side=tk.LEFT, padx=5)

        self.uninstall_smapi_btn = ttk.Button(action_frame, text=tr.translate("uninstall_smapi"), command=self._uninstall_smapi)

        self.uninstall_smapi_btn.pack(side=tk.LEFT, padx=5)

        self.backup_mods_btn.config(state=tk.DISABLED)

        self.install_smapi_btn.config(state=tk.DISABLED)

        self.uninstall_smapi_btn.config(state=tk.DISABLED)

        search_frame = ttk.Frame(mod_frame)

        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text=tr.translate("search")).pack(side=tk.LEFT, padx=(0, 5))

        self.mod_search_var = tk.StringVar()

        search_entry = ttk.Entry(search_frame, textvariable=self.mod_search_var, width=40)

        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.mod_search_var.trace_add("write", self._on_mod_search_change)

        self.mod_status_var = tk.StringVar(value=tr.translate("mods_set_path_hint"))

        status_label = ttk.Label(mod_frame, textvariable=self.mod_status_var, foreground="blue", font=("", 9))

        status_label.pack(pady=(0, 10))

        log_frame = ttk.LabelFrame(mod_frame, text=tr.translate("operation_log"))

        log_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        self.mod_log_text = tk.Text(log_frame, height=5, wrap=tk.WORD, state=tk.DISABLED)

        self.mod_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(self.mod_log_text, command=self.mod_log_text.yview)

        self.mod_log_text.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.mod_notebook = ttk.Notebook(mod_frame)

        self.mod_notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.mod_category_frames = {}

        self.mod_vars = {}

        self.local_mod_rows = []

        local_tab = ttk.Frame(self.mod_notebook, padding=10)

        self.mod_notebook.add(local_tab, text=tr.translate("local_mods"))

        local_mod_container = ttk.Frame(local_tab)

        local_mod_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.local_mod_canvas = tk.Canvas(local_mod_container, highlightthickness=0)

        self.local_mod_scrollbar = ttk.Scrollbar(

            local_mod_container,

            orient=tk.VERTICAL,

            command=self.local_mod_canvas.yview,

        )

        self.local_mod_canvas.configure(yscrollcommand=self.local_mod_scrollbar.set)

        self.local_mod_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.local_mod_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.local_mod_frame = ttk.Frame(self.local_mod_canvas)

        self._local_mod_canvas_window = self.local_mod_canvas.create_window(

            (0, 0),

            window=self.local_mod_frame,

            anchor=tk.NW,

        )

        self.local_mod_frame.bind(

            "<Configure>",

            lambda _e: self.local_mod_canvas.configure(scrollregion=self.local_mod_canvas.bbox("all")),

        )

        self.local_mod_canvas.bind(

            "<Configure>",

            lambda e: self.local_mod_canvas.itemconfigure(self._local_mod_canvas_window, width=e.width),

        )

        setup_mousewheel(self.local_mod_canvas)

    # Bind hover handlers that show mod details next to the pointer.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _bind_mod_tooltip(self, widget, text):

        if not text:

            return

        # Show the mod tooltip when the pointer enters the widget.
        # It keeps tab-specific widgets synchronized with the current save model and editor state.
        def _on_enter(event):

            self._show_mod_tooltip(event, text)

        # Reposition the mod tooltip while the pointer moves.
        # It keeps tab-specific widgets synchronized with the current save model and editor state.
        def _on_motion(event):

            self._move_mod_tooltip(event)

        # Hide the mod tooltip when the pointer leaves the widget.
        # It keeps tab-specific widgets synchronized with the current save model and editor state.
        def _on_leave(_event):

            self._hide_mod_tooltip()

        widget.bind("<Enter>", _on_enter, add="+")

        widget.bind("<Motion>", _on_motion, add="+")

        widget.bind("<Leave>", _on_leave, add="+")

    # Show the mod tooltip.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _show_mod_tooltip(self, event, text):

        self._hide_mod_tooltip()

        tip = tk.Toplevel(self.root)

        tip.wm_overrideredirect(True)

        try:

            tip.wm_attributes("-topmost", True)

        except tk.TclError:

            pass

        label = tk.Label(

            tip,

            text=text,

            justify=tk.LEFT,

            bg="#fffbe6",

            fg="#222222",

            relief=tk.SOLID,

            borderwidth=1,

            padx=8,

            pady=6,

            wraplength=520,

        )

        label.pack()

        tip.geometry(f"+{event.x_root + 14}+{event.y_root + 14}")

        self._mod_tooltip = tip

    # Move the mod tooltip to follow the pointer.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _move_mod_tooltip(self, event):

        tip = getattr(self, "_mod_tooltip", None)

        if tip and tip.winfo_exists():

            tip.geometry(f"+{event.x_root + 14}+{event.y_root + 14}")

    # Hide the active mod tooltip window.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _hide_mod_tooltip(self):

        tip = getattr(self, "_mod_tooltip", None)

        if tip and tip.winfo_exists():

            tip.destroy()

        self._mod_tooltip = None

    # Apply the current mod search filter to the displayed mod list.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _on_mod_search_change(self, *args):

        search_text = self.mod_search_var.get().strip().lower()

        for row in getattr(self, "local_mod_rows", []):

            matches = (
                not search_text
                or search_text in row["name"]
                or search_text in row["desc"]
                or search_text in row["author"]
                or search_text in row["source"]
            )

            if matches:

                row["frame"].pack(fill=tk.X, pady=4, padx=10)

                if row["separator"] is not None:

                    row["separator"].pack(fill=tk.X, padx=10, pady=(0, 2))

            else:

                row["frame"].pack_forget()

                if row["separator"] is not None:

                    row["separator"].pack_forget()

        for category, data in self.mod_category_frames.items():

            for mod_info in data['mods']:

                if search_text in mod_info['name'] or search_text in mod_info['desc']:

                    mod_info['frame'].pack(fill=tk.X, pady=3, padx=5)

                else:

                    mod_info['frame'].pack_forget()

    # Detect the game path and update the mods page state.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _auto_detect_game_path(self):

        try:

            paths = self.game_path_detector.detect_all()

            if not paths:

                self.mod_status_var.set(tr.translate("mods_game_path_not_detected"))

                self._update_smapi_buttons()

                return

            detected = paths[0]

            self.game_path_var.set(detected)

            self.mod_status_var.set(tr.translate("mods_game_path_auto_detected").format(path=detected))

            self._update_smapi_buttons()

            self._refresh_mods()

        except Exception as e:

            self.mod_status_var.set(tr.translate("mods_game_path_auto_detect_failed"))

            self._log_mod_message(tr.translate("mods_game_path_auto_detect_failed_log").format(error=e))

            self._update_smapi_buttons()

    # Select the game path.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _select_game_path(self):

        path = filedialog.askdirectory(title=tr.translate("mods_select_game_path"))

        if path:

            self.game_path_var.set(path)

            self.mod_status_var.set(tr.translate("mods_game_path_set").format(path=path))

            self._log_mod_message(tr.translate("mods_game_path_set_log").format(path=path))

            self._update_smapi_buttons()

            self._refresh_mods()

    # Return whether the valid game path flag is enabled.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _is_valid_game_path(self, game_path):

        return bool(game_path and os.path.exists(os.path.join(game_path, "Stardew Valley.exe")))

    # Create the mod manager.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _create_mod_manager(self, require_valid_game_path=False):

        game_path = self.game_path_var.get().strip()

        if require_valid_game_path and not self._is_valid_game_path(game_path):

            messagebox.showwarning(tr.translate("warning"), tr.translate("valid_game_path_required"))

            return None

        from models.mod_data import ModManager

        return ModManager(game_path, log_callback=self._log_mod_message)

    # Update the SMAPI buttons.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _update_smapi_buttons(self):

        game_path = self.game_path_var.get().strip()

        if not self._is_valid_game_path(game_path):

            if hasattr(self, "backup_mods_btn"):

                self.backup_mods_btn.config(state=tk.DISABLED)

            self.install_smapi_btn.config(state=tk.DISABLED)

            self.uninstall_smapi_btn.config(state=tk.DISABLED)

            return

        if hasattr(self, "backup_mods_btn"):

            self.backup_mods_btn.config(state=tk.NORMAL)

        if SmapiInstaller.is_installed(game_path):

            self.install_smapi_btn.config(state=tk.DISABLED)

            self.uninstall_smapi_btn.config(state=tk.NORMAL)

        else:

            self.install_smapi_btn.config(state=tk.NORMAL)

            self.uninstall_smapi_btn.config(state=tk.DISABLED)

    # Return whether the process running flag is enabled.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _is_process_running(self, process_name):

        try:

            flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0

            result = subprocess.run(

                ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],

                capture_output=True,

                text=True,

                creationflags=flags

            )

            return process_name.lower() in result.stdout.lower()

        except Exception:

            return False

    # Return whether the steam running flag is enabled.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _is_steam_running(self):

        return self._is_process_running("steam.exe") or self._is_process_running("steamwebhelper.exe")

    # Close Steam before file operations when the current settings require it.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _auto_close_steam_if_enabled(self):

        if not self._is_steam_running():

            return True

        self._log_mod_message(tr.translate("steam_running_auto_close"))

        flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0

        try:

            subprocess.run(["cmd", "/c", "start", "", "steam://exit"], capture_output=True, text=True, creationflags=flags)

            time.sleep(2)

            for _ in range(5):

                subprocess.run(["taskkill", "/F", "/IM", "steam.exe"], capture_output=True, text=True, creationflags=flags)

                subprocess.run(["taskkill", "/F", "/IM", "steamwebhelper.exe"], capture_output=True, text=True, creationflags=flags)

                time.sleep(1)

                if not self._is_steam_running():

                    break

            if self._is_steam_running():

                self._log_mod_message(tr.translate("steam_auto_close_failed_manual"))

                messagebox.showerror(tr.translate("error"), tr.translate("steam_auto_close_failed_manual"))

                return False

            self._log_mod_message(tr.translate("steam_closed_automatically"))

            return True

        except Exception as e:

            self._log_mod_message(tr.translate("steam_auto_close_failed").format(error=e))

            messagebox.showerror(tr.translate("error"), tr.translate("steam_auto_close_failed").format(error=e))

            return False

    # Refresh the mods.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _refresh_mods(self):

        game_path = self.game_path_var.get().strip()

        if not game_path:

            paths = self.game_path_detector.detect_all() if hasattr(self, "game_path_detector") else []

            if paths:

                game_path = paths[0]

                self.game_path_var.set(game_path)

            else:

                self._log_mod_message(tr.translate("mods_no_game_path_local_only"))

        self.mod_status_var.set(tr.translate("mods_scanning"))

        self._log_mod_message(tr.translate("mods_scan_started"))

        try:

            self._hide_mod_tooltip()

            for widget in self.local_mod_frame.winfo_children():

                widget.destroy()

            manager = self._create_mod_manager()

            mods = manager.refresh_mods()

            local_count = sum(1 for mod in mods if mod.is_local_available)

            installed_count = sum(1 for mod in mods if mod.is_installed)

            actions_enabled = self._is_valid_game_path(game_path)

            self.local_mod_rows = []

            for i, mod in enumerate(mods):

                row_frame = ttk.Frame(self.local_mod_frame)

                row_frame.pack(fill=tk.X, pady=4, padx=10)

                info_frame = ttk.Frame(row_frame)

                info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

                status = tr.translate("mod_status_installed") if mod.is_installed else tr.translate("mod_status_not_installed")

                status_color = "green" if mod.is_installed else "red"

                source_parts = []

                if mod.is_local_available:

                    source_parts.append(tr.translate("mod_source_program"))

                if mod.is_installed:

                    source_parts.append(tr.translate("mod_source_game"))

                source_text = " / ".join(source_parts) if source_parts else tr.translate("mod_source_unknown")

                author_text = tr.translate("mod_author_label").format(author=mod.author or tr.translate("unknown"))

                mod_desc = self._ensure_english_text(mod.description, mod.name)

                tooltip_text = (

                    f"{mod.name} v{mod.version}\n"

                    f"{author_text}\n"

                    f"{tr.translate('mod_status_label').format(status=status)}\n"

                    f"{tr.translate('mod_sources_label').format(source=source_text)}\n\n"

                    f"{tr.translate('description')}:\n{mod_desc}"

                )

                name_label = ttk.Label(info_frame, text=f"{mod.name} v{mod.version}", font=("", 10, "bold"))

                name_label.pack(side=tk.LEFT, padx=(0, 8))

                author_label = ttk.Label(info_frame, text=author_text, foreground="gray")

                author_label.pack(side=tk.LEFT, padx=(0, 8))

                status_label = ttk.Label(info_frame, text=f"[{status}]", foreground=status_color)

                status_label.pack(side=tk.LEFT)

                source_label = ttk.Label(info_frame, text=f"[{source_text}]", foreground="#6a5acd")

                source_label.pack(side=tk.LEFT, padx=(8, 0))

                hint_label = ttk.Label(info_frame, text=f"({tr.translate('hover_for_details')})", foreground="gray")

                hint_label.pack(side=tk.LEFT, padx=(8, 0))

                self._bind_mod_tooltip(name_label, tooltip_text)

                self._bind_mod_tooltip(author_label, tooltip_text)

                self._bind_mod_tooltip(status_label, tooltip_text)

                self._bind_mod_tooltip(source_label, tooltip_text)

                self._bind_mod_tooltip(hint_label, tooltip_text)

                btn_frame = ttk.Frame(row_frame)

                btn_frame.pack(side=tk.RIGHT, padx=(8, 0))

                if not mod.is_installed:

                    install_btn = ttk.Button(btn_frame, text=tr.translate("install"), command=lambda m=mod: self._install_mod(m))

                    install_btn.pack(side=tk.LEFT, padx=5)

                    if not actions_enabled:

                        install_btn.config(state=tk.DISABLED)

                else:

                    uninstall_btn = ttk.Button(btn_frame, text=tr.translate("uninstall"), command=lambda m=mod: self._uninstall_mod(m))

                    uninstall_btn.pack(side=tk.LEFT, padx=5)

                    if mod.is_enabled:

                        toggle_btn = ttk.Button(btn_frame, text=tr.translate("disable"), command=lambda m=mod: self._disable_mod(m))

                    else:

                        toggle_btn = ttk.Button(btn_frame, text=tr.translate("enable"), command=lambda m=mod: self._enable_mod(m))

                    toggle_btn.pack(side=tk.LEFT, padx=5)

                    if not actions_enabled:

                        uninstall_btn.config(state=tk.DISABLED)

                        toggle_btn.config(state=tk.DISABLED)

                separator = None

                if i < len(mods) - 1:

                    separator = ttk.Separator(self.local_mod_frame, orient=tk.HORIZONTAL)

                    separator.pack(fill=tk.X, padx=10, pady=(0, 2))

                self.local_mod_rows.append({
                    "frame": row_frame,
                    "name": (mod.name or "").lower(),
                    "desc": (mod_desc or "").lower(),
                    "author": (mod.author or "").lower(),
                    "source": source_text.lower(),
                    "separator": separator,
                })

            self.mod_status_var.set(
                tr.translate("mods_found_summary").format(count=len(mods), local=local_count, installed=installed_count)
            )

            self._log_mod_message(
                tr.translate("mods_scan_complete").format(count=len(mods), local=local_count, installed=installed_count)
            )

            self._on_mod_search_change()

            self._update_smapi_buttons()

        except Exception as e:

            self.mod_status_var.set(tr.translate("mods_scan_failed"))

            self._log_mod_message(tr.translate("mods_scan_failed_log").format(error=e))

            messagebox.showerror(tr.translate("error"), tr.translate("mods_scan_failed_dialog").format(error=e))

            self._update_smapi_buttons()

    # Back up installed mods that are missing from the local mods source folder.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _backup_missing_mods(self):

        manager = self._create_mod_manager(require_valid_game_path=True)

        if manager is None:

            return

        try:

            self._log_mod_message(tr.translate("backup_missing_mods_started"))

            backed_up = manager.backup_missing_installed_mods()

            if backed_up:

                self.mod_status_var.set(tr.translate("backup_missing_mods_done").format(count=len(backed_up)))

                self._log_mod_message(tr.translate("backup_missing_mods_done").format(count=len(backed_up)))

                messagebox.showinfo(tr.translate("info"), tr.translate("backup_missing_mods_dialog_done").format(count=len(backed_up)))

                self._refresh_mods()

            else:

                self.mod_status_var.set(tr.translate("backup_missing_mods_none"))

                self._log_mod_message(tr.translate("backup_missing_mods_none"))

                messagebox.showinfo(tr.translate("info"), tr.translate("backup_missing_mods_dialog_none"))

        except Exception as e:

            self.mod_status_var.set(tr.translate("backup_failed"))

            self._log_mod_message(tr.translate("backup_failed_with_error").format(error=e))

            messagebox.showerror(tr.translate("error"), tr.translate("backup_failed_with_error").format(error=e))

    # Install the mod.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _install_mod(self, mod):

        manager = self._create_mod_manager(require_valid_game_path=True)

        if manager is None:

            return

        try:

            self._log_mod_message(tr.translate("mod_install_started").format(name=mod.name))

            success = manager.install_mod(mod)

            if success:

                self._log_mod_message(tr.translate("mod_installed_success").format(name=mod.name))

                messagebox.showinfo(tr.translate("info"), tr.translate("mod_installed_success").format(name=mod.name))

                self._refresh_mods()

            else:

                self._log_mod_message(tr.translate("mod_install_failed").format(name=mod.name))

                messagebox.showerror(tr.translate("error"), tr.translate("mod_install_failed").format(name=mod.name))

        except Exception as e:

            self._log_mod_message(tr.translate("mod_install_failed_with_error").format(error=e))

            messagebox.showerror(tr.translate("error"), tr.translate("mod_install_failed_with_error").format(error=e))

    # Uninstall the mod.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _uninstall_mod(self, mod):

        manager = self._create_mod_manager(require_valid_game_path=True)

        if manager is None:

            return

        try:

            self._log_mod_message(tr.translate("mod_uninstall_started").format(name=mod.name))

            success = manager.uninstall_mod(mod)

            if success:

                self._log_mod_message(tr.translate("mod_uninstalled_success").format(name=mod.name))

                messagebox.showinfo(tr.translate("info"), tr.translate("mod_uninstalled_success").format(name=mod.name))

                self._refresh_mods()

            else:

                self._log_mod_message(tr.translate("mod_uninstall_failed").format(name=mod.name))

                messagebox.showerror(tr.translate("error"), tr.translate("mod_uninstall_failed").format(name=mod.name))

        except Exception as e:

            self._log_mod_message(tr.translate("mod_uninstall_failed_with_error").format(error=e))

            messagebox.showerror(tr.translate("error"), tr.translate("mod_uninstall_failed_with_error").format(error=e))

    # Enable the mod.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _enable_mod(self, mod):

        manager = self._create_mod_manager(require_valid_game_path=True)

        if manager is None:

            return

        try:

            self._log_mod_message(tr.translate("mod_enable_started").format(name=mod.name))

            success = manager.enable_mod(mod)

            if success:

                self._log_mod_message(tr.translate("mod_enabled_success").format(name=mod.name))

                messagebox.showinfo(tr.translate("info"), tr.translate("mod_enabled_success").format(name=mod.name))

                self._refresh_mods()

            else:

                self._log_mod_message(tr.translate("mod_enable_failed").format(name=mod.name))

                messagebox.showerror(tr.translate("error"), tr.translate("mod_enable_failed").format(name=mod.name))

        except Exception as e:

            self._log_mod_message(tr.translate("mod_enable_failed_with_error").format(error=e))

            messagebox.showerror(tr.translate("error"), tr.translate("mod_enable_failed_with_error").format(error=e))

    # Disable the mod.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _disable_mod(self, mod):

        manager = self._create_mod_manager(require_valid_game_path=True)

        if manager is None:

            return

        try:

            self._log_mod_message(tr.translate("mod_disable_started").format(name=mod.name))

            success = manager.disable_mod(mod)

            if success:

                self._log_mod_message(tr.translate("mod_disabled_success").format(name=mod.name))

                messagebox.showinfo(tr.translate("info"), tr.translate("mod_disabled_success").format(name=mod.name))

                self._refresh_mods()

            else:

                self._log_mod_message(tr.translate("mod_disable_failed").format(name=mod.name))

                messagebox.showerror(tr.translate("error"), tr.translate("mod_disable_failed").format(name=mod.name))

        except Exception as e:

            self._log_mod_message(tr.translate("mod_disable_failed_with_error").format(error=e))

            messagebox.showerror(tr.translate("error"), tr.translate("mod_disable_failed_with_error").format(error=e))

    # Toggle the mod.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _toggle_mod(self, mod):

        if mod.is_enabled:

            self._disable_mod(mod)

        else:

            self._enable_mod(mod)

    # Install the SMAPI.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _install_smapi(self):

        game_path = self.game_path_var.get().strip()

        if not self._is_valid_game_path(game_path):

            messagebox.showwarning(tr.translate("warning"), tr.translate("valid_game_path_required"))

            return

        if SmapiInstaller.is_installed(game_path):

            messagebox.showinfo(tr.translate("info"), tr.translate("smapi_already_installed"))

            self._update_smapi_buttons()

            return

        result = messagebox.askyesno(

            tr.translate("info"),

            tr.translate("smapi_install_confirm").format(path=game_path),

        )

        if not result:

            return

        if not self._auto_close_steam_if_enabled():

            return

        try:

            self.install_smapi_btn.config(state=tk.DISABLED)

            self.uninstall_smapi_btn.config(state=tk.DISABLED)

            self.mod_status_var.set(tr.translate("smapi_installing"))

            self._log_mod_message(tr.translate("smapi_install_started").format(path=game_path))

            installer = SmapiInstaller(game_path, log_callback=self._log_mod_message)

            installer.install()

            self.steam_helper.setup_achievements(game_path)

            self.mod_status_var.set(tr.translate("smapi_install_done"))

            self._log_mod_message(tr.translate("smapi_install_done"))

            messagebox.showinfo(tr.translate("info"), tr.translate("smapi_install_done"))

        except Exception as e:

            self.mod_status_var.set(tr.translate("smapi_install_failed"))

            self._log_mod_message(tr.translate("smapi_install_failed_with_error").format(error=e))

            messagebox.showerror(tr.translate("error"), tr.translate("smapi_install_failed_with_error").format(error=e))

        finally:

            self._update_smapi_buttons()

    # Uninstall the SMAPI.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _uninstall_smapi(self):

        game_path = self.game_path_var.get().strip()

        if not self._is_valid_game_path(game_path):

            messagebox.showwarning(tr.translate("warning"), tr.translate("valid_game_path_required"))

            return

        if not SmapiInstaller.is_installed(game_path):

            messagebox.showinfo(tr.translate("info"), tr.translate("smapi_not_installed"))

            self._update_smapi_buttons()

            return

        result = messagebox.askyesno(

            tr.translate("warning"),

            tr.translate("smapi_uninstall_confirm").format(path=game_path),

        )

        if not result:

            return

        if not self._auto_close_steam_if_enabled():

            return

        try:

            self.install_smapi_btn.config(state=tk.DISABLED)

            self.uninstall_smapi_btn.config(state=tk.DISABLED)

            self.mod_status_var.set(tr.translate("smapi_uninstalling"))

            self._log_mod_message(tr.translate("smapi_uninstall_started").format(path=game_path))

            installer = SmapiInstaller(game_path, log_callback=self._log_mod_message)

            installer.uninstall()

            self.steam_helper.clear_launch_options()

            self.mod_status_var.set(tr.translate("smapi_uninstall_done"))

            self._log_mod_message(tr.translate("smapi_uninstall_done"))

            messagebox.showinfo(tr.translate("info"), tr.translate("smapi_uninstall_done"))

        except Exception as e:

            self.mod_status_var.set(tr.translate("smapi_uninstall_failed"))

            self._log_mod_message(tr.translate("smapi_uninstall_failed_with_error").format(error=e))

            messagebox.showerror(tr.translate("error"), tr.translate("smapi_uninstall_failed_with_error").format(error=e))

        finally:

            self._update_smapi_buttons()

    # Append a message to the mods operation log.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def _log_mod_message(self, message):

        self.mod_log_text.config(state=tk.NORMAL)

        self.mod_log_text.insert(tk.END, f"{message}\n")

        self.mod_log_text.see(tk.END)

        self.mod_log_text.config(state=tk.DISABLED)
