# Model chest inventories and related item container behavior from save data.
from models.base_proxy import BaseProxy

from models.item import Item

import xml.etree.ElementTree as ET

# Return whether the nil sentinel flag is enabled.
# It reads or mutates the XML-backed save model used by the editor.
def is_nil_sentinel(element: ET.Element):

    return element.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"

# Define the chest type used by this module.
# It reads or mutates the XML-backed save model used by the editor.
class Chest(BaseProxy):

    def __init__(self, element: ET.Element):

        super().__init__(element)

    # Return the chest's items.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def items(self):

        items_elem = self._element.find("items")

        if items_elem is not None:

            return [Item(i) for i in items_elem.findall("Item")]

        return []

    # Return the chest's capacity.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def capacity(self): return self.get_int("capacity", 36)

    # Update the chest's capacity.
    # It reads or mutates the XML-backed save model used by the editor.
    @capacity.setter

    def capacity(self, value): self.set_int("capacity", value)

    # Return the chest's player choice color.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def playerChoiceColor(self):

        color_elem = self._element.find("playerChoiceColor")

        if color_elem is not None:

            return {

                "R": int(color_elem.findtext("R", "0")),

                "G": int(color_elem.findtext("G", "0")),

                "B": int(color_elem.findtext("B", "0")),

                "A": int(color_elem.findtext("A", "255"))

            }

        return None

    # Update the chest's player choice color.
    # It reads or mutates the XML-backed save model used by the editor.
    @playerChoiceColor.setter

    def playerChoiceColor(self, value):

        color_elem = self._element.find("playerChoiceColor")

        if color_elem is None:

            color_elem = ET.SubElement(self._element, "playerChoiceColor")

        for k, v in value.items():

            elem = color_elem.find(k)

            if elem is None:

                elem = ET.SubElement(color_elem, k)

            elem.text = str(v)

    # Return the chest's special chest type.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def specialChestType(self): return self.get_text("specialChestType", "None")

    # Update the chest's special chest type.
    # It reads or mutates the XML-backed save model used by the editor.
    @specialChestType.setter

    def specialChestType(self, value): self.set_text("specialChestType", value)

    # Return the chest's global inventory ID.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def globalInventoryId(self): return self.get_text("globalInventoryId/string", "")

    # Update the chest's global inventory ID.
    # It reads or mutates the XML-backed save model used by the editor.
    @globalInventoryId.setter

    def globalInventoryId(self, value): self.set_text("globalInventoryId/string", value)

    # Add an item to the current collection.
    # It reads or mutates the XML-backed save model used by the editor.
    def add_item(self, name, item_id=None, stack=1, quality=0, **kwargs):

        items_elem = self._element.find("items")

        if items_elem is None:

            items_elem = ET.SubElement(self._element, "items")

        item = Item.from_name(name, item_id=item_id)

        item.stack = stack

        item.quality = quality

        for key, value in kwargs.items():

            if hasattr(item, key):

                setattr(item, key, value)

            else:

                item.set_text(key, str(value))

        items = items_elem.findall("Item")

        target_index = None

        for idx, elem in enumerate(items):

            if is_nil_sentinel(elem):

                target_index = idx

                break

        if target_index is None:

            items_elem.append(item.raw)

        else:

            old_elem = items[target_index]

            items_elem.remove(old_elem)

            items_elem.insert(target_index, item.raw)

        return item

    # Remove the item.
    # It reads or mutates the XML-backed save model used by the editor.
    def remove_item(self, item_model):

        items_elem = self._element.find("items")

        if items_elem is None:

            return

        nil_qname = "{http://www.w3.org/2001/XMLSchema-instance}nil"

        items = items_elem.findall("Item")

        for elem in items:

            if elem is item_model.raw:

                elem.clear()

                elem.set(nil_qname, "true")

                return
