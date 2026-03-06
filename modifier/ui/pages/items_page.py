# Build the items page and keep item widgets synchronized with inventory state.
import tkinter as tk

from tkinter import messagebox, ttk

from utils import tr

from utils.item_localization import translate_item_name

from ..dialogs import AddItemDialog, ChestDialog

from ..helpers import bind_numeric_input_limit, setup_mousewheel

# Provide page-specific UI builders and behaviors that are mixed into the main editor window.
# It keeps tab-specific widgets synchronized with the current save model and editor state.
class ItemsPageMixin:

    # Build the items tab.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def build_items_tab(self, main_notebook):

        items_tab = ttk.Frame(main_notebook)

        main_notebook.add(items_tab, text=tr.translate("items_chests_tab_title"))

        tree_frame = ttk.Frame(items_tab, padding=10)

        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.items_tree = ttk.Treeview(tree_frame, columns=("name", "stack", "quality"), show="tree headings")

        self.items_tree.heading("#0", text=tr.translate("location"))

        self.items_tree.heading("name", text=tr.translate("item_name"))

        self.items_tree.heading("stack", text=tr.translate("quantity"))

        self.items_tree.heading("quality", text=tr.translate("quality"))

        self.items_tree.column("#0", width=250)

        self.items_tree.column("stack", width=80)

        self.items_tree.column("quality", width=80)

        tree_h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.items_tree.xview)

        tree_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        tree_v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.items_tree.yview)

        tree_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.items_tree.configure(yscrollcommand=tree_v_scroll.set, xscrollcommand=tree_h_scroll.set)

        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        setup_mousewheel(self.items_tree)

        self.items_tree.bind("<Double-1>", lambda e: self.edit_selected_item())

        item_btn_frame = ttk.Frame(items_tab, padding=5)

        item_btn_frame.pack(fill=tk.X)

        ttk.Button(item_btn_frame, text=tr.translate("edit_selected"), command=self.edit_selected_item).pack(side=tk.LEFT, padx=5)

        ttk.Button(item_btn_frame, text=tr.translate("add_new"), command=self.add_new_item).pack(side=tk.LEFT, padx=5)

        ttk.Button(item_btn_frame, text=tr.translate("delete_selected"), command=self.delete_selected_item).pack(side=tk.LEFT, padx=5)

    # Load the inventory for player.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def load_inventory_for_player(self, player):

        self.inventory_items = []

        if player is None: return

        self.inventory_max = player.maxItems

        for item in player.items:

            if item.is_empty: continue

            raw_name = item.name or tr.translate("unknown")

            item_id = item.itemId or ""

            display_name = translate_item_name(raw_name, raw_name)

            if item_id:

                prefixed_id = item.prefixedId

                mapped_name = self.item_name_map.get(prefixed_id)

                if not mapped_name:

                    mapped_name = self.item_name_map.get(item_id)

                if not mapped_name:

                    for prefix_items in self.item_name_map_by_prefix.values():

                        if item_id in prefix_items:

                            mapped_name = prefix_items[item_id]

                            break

                if mapped_name:

                    display_name = mapped_name

                elif raw_name in self.item_name_map:

                    display_name = self.item_name_map[raw_name]

                else:

                    display_name = translate_item_name(raw_name, raw_name)

            stack_var = tk.StringVar(value=str(item.stack))

            quality_var = tk.StringVar(value=str(item.quality))

            bind_numeric_input_limit(stack_var, min_value=1)

            bind_numeric_input_limit(quality_var, max_value=4, min_value=0)

            self.inventory_items.append({

                'display_name': display_name,

                'name': raw_name,

                'stack': stack_var,

                'quality': quality_var,

                'model': item,

                'item_id': item.prefixedId or item_id

            })

    # Refresh the items list.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def refresh_items_list(self):

        if not hasattr(self, "items_tree"): return

        for item in self.items_tree.get_children():

            self.items_tree.delete(item)

        inv_root = self.items_tree.insert("", tk.END, text=tr.translate("backpack_with_count").format(count=len(self.inventory_items), max=self.inventory_max), open=True)

        for item in self.inventory_items:

            self.items_tree.insert(inv_root, tk.END, values=(item['display_name'], item['stack'].get(), item['quality'].get()))

        for chest in self.chests_data:

            display_location = chest.get("display_location", chest["location"])

            chest_root = self.items_tree.insert("", tk.END, text=tr.translate("chest_with_location_count").format(location=display_location, count=len(chest['items']), max=chest['capacity']), open=False)

            for item in chest['items']:

                self.items_tree.insert(chest_root, tk.END, values=(item['display_name'], item['stack'].get(), item['quality'].get()))

    # Open the editor for the currently selected inventory item.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def edit_selected_item(self):

        selection = self.items_tree.selection()

        if not selection:

            messagebox.showwarning(tr.translate("info"), tr.translate("please_select_item_to_modify"))

            return

        item_id = selection[0]

        parent_id = self.items_tree.parent(item_id)

        if not parent_id:

            node_text = self.items_tree.item(item_id, "text")

            if tr.translate("chests") in node_text:

                for chest in self.chests_data:

                    display_location = chest.get("display_location", chest["location"])

                    if display_location in node_text or chest["location"] in node_text:

                        dialog = ChestDialog(self.root, chest)

                        self.root.wait_window(dialog)

                        if dialog.result:

                            self.refresh_items_list()

                            messagebox.showinfo(tr.translate("success"), tr.translate("chest_updated"))

                        return

            return

        item_index = self.items_tree.index(item_id)

        parent_text = self.items_tree.item(parent_id, "text")

        target_item = None

        if tr.translate("backpack") in parent_text:

            if 0 <= item_index < len(self.inventory_items):

                target_item = self.inventory_items[item_index]

        else:

            for chest in self.chests_data:

                display_location = chest.get("display_location", chest["location"])

                if display_location in parent_text or chest["location"] in parent_text:

                    if 0 <= item_index < len(chest['items']):

                        target_item = chest['items'][item_index]

                    break

        if not target_item: return

        initial_data = {

            "name": target_item["display_name"],

            "save_name": target_item["name"],

            "stack": target_item["stack"].get(),

            "quality": target_item["quality"].get(),

            "model": target_item["model"],

            "id": target_item.get("item_id", "")

        }

        dialog = AddItemDialog(self.root, title=tr.translate("modify_item"), initial_data=initial_data)

        self.root.wait_window(dialog)

        if dialog.result:

            new_name = dialog.result["name"]

            final_save_name = dialog.result.get("save_name") or new_name

            target_item["display_name"] = new_name

            target_item["name"] = final_save_name

            target_item["stack"].set(dialog.result["stack"])

            target_item["quality"].set(dialog.result["quality"])

            item_model = target_item["model"]

            item_model.name = final_save_name

            item_model.stack = int(dialog.result["stack"])

            item_model.quality = int(dialog.result["quality"])

            item_model.itemId = dialog.result["id"]

            target_item["item_id"] = item_model.prefixedId or dialog.result["id"]

            self.refresh_items_list()

            messagebox.showinfo(tr.translate("success"), tr.translate("item_modified_msg").format(name=new_name))

    # Open the dialog used to create a new inventory item.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def add_new_item(self):

        if not self.all_players:

            messagebox.showwarning(tr.translate("warning"), tr.translate("please_load_save"))

            return

        selection = self.items_tree.selection()

        target_container = tr.translate("backpack")

        target_model = None

        target_list = None

        if selection:

            item_id = selection[0]

            parent_id = self.items_tree.parent(item_id)

            if not parent_id:

                node_text = self.items_tree.item(item_id, "text")

            else:

                node_text = self.items_tree.item(parent_id, "text")

            if tr.translate("backpack") in node_text:

                target_container = tr.translate("backpack")

                target_model = self.all_players[self.current_player_idx]["model"]

                target_list = self.inventory_items

            else:

                for chest in self.chests_data:

                    display_location = chest.get("display_location", chest["location"])

                    if display_location in node_text or chest["location"] in node_text:

                        target_container = tr.translate("chest_at").format(location=display_location)

                        target_model = chest['model']

                        target_list = chest['items']

                        break

        if target_model is None:

            target_container = tr.translate("backpack")

            target_model = self.all_players[self.current_player_idx]["model"]

            target_list = self.inventory_items

        dialog = AddItemDialog(self.root, title=tr.translate("add_item_to").format(container=target_container))

        self.root.wait_window(dialog)

        if dialog.result:

            new_name = dialog.result["name"]

            final_save_name = dialog.result.get("save_name") or new_name

            item_model = target_model.add_item(

                name=final_save_name,

                item_id=dialog.result["id"],

                stack=int(dialog.result["stack"]),

                quality=int(dialog.result["quality"])

            )

            stack_var = tk.StringVar(value=str(dialog.result["stack"]))

            quality_var = tk.StringVar(value=str(dialog.result["quality"]))

            bind_numeric_input_limit(stack_var, min_value=1)

            bind_numeric_input_limit(quality_var, max_value=4, min_value=0)

            if target_list is not None:

                target_list.append({

                    'display_name': new_name,

                    'name': final_save_name,

                    'stack': stack_var,

                    'quality': quality_var,

                    'model': item_model,

                    'item_id': item_model.prefixedId or dialog.result["id"]

                })

            self.refresh_items_list()

            messagebox.showinfo(tr.translate("success"), tr.translate("item_added_to_container_msg").format(name=new_name, stack=dialog.result['stack'], container=target_container))

    # Remove the currently selected inventory item.
    # It keeps tab-specific widgets synchronized with the current save model and editor state.
    def delete_selected_item(self):

        selection = self.items_tree.selection()

        if not selection:

            messagebox.showwarning(tr.translate("info"), tr.translate("please_select_item_to_delete"))

            return

        item_id = selection[0]

        parent_id = self.items_tree.parent(item_id)

        if not parent_id:

            return

        item_index = self.items_tree.index(item_id)

        parent_text = self.items_tree.item(parent_id, "text")

        if tr.translate("backpack") in parent_text:

            if 0 <= item_index < len(self.inventory_items):

                item_data = self.inventory_items.pop(item_index)

                player = self.all_players[self.current_player_idx]["model"]

                player.remove_item(item_data['model'])

                messagebox.showinfo(tr.translate("success"), tr.translate("deleted_from_backpack_msg").format(name=item_data['display_name']))

        else:

            for chest in self.chests_data:

                display_location = chest.get("display_location", chest["location"])

                if display_location in parent_text or chest["location"] in parent_text:

                    if 0 <= item_index < len(chest['items']):

                        item_data = chest['items'].pop(item_index)

                        chest['model'].remove_item(item_data['model'])

                        messagebox.showinfo(tr.translate("success"), tr.translate("deleted_from_chest_msg").format(name=item_data['display_name']))

                    break

        self.refresh_items_list()
