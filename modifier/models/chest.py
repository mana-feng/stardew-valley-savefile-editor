from models.base_proxy import BaseProxy
from models.item import Item
import xml.etree.ElementTree as ET

def is_nil_sentinel(element: ET.Element):
    return element.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"

class Chest(BaseProxy):
    """
    箱子模型类。
    """
    def __init__(self, element: ET.Element):
        super().__init__(element)

    @property
    def items(self):
        """返回箱子中的物品列表"""
        items_elem = self._element.find("items")
        if items_elem is not None:
            return [Item(i) for i in items_elem.findall("Item")]
        return []

    @property
    def capacity(self): return self.get_int("capacity", 36)
    @capacity.setter
    def capacity(self, value): self.set_int("capacity", value)

    @property
    def playerChoiceColor(self):
        """返回箱子的自定义颜色"""
        color_elem = self._element.find("playerChoiceColor")
        if color_elem is not None:
            return {
                "R": int(color_elem.findtext("R", "0")),
                "G": int(color_elem.findtext("G", "0")),
                "B": int(color_elem.findtext("B", "0")),
                "A": int(color_elem.findtext("A", "255"))
            }
        return None

    @playerChoiceColor.setter
    def playerChoiceColor(self, value):
        """设置箱子的自定义颜色"""
        color_elem = self._element.find("playerChoiceColor")
        if color_elem is None:
            color_elem = ET.SubElement(self._element, "playerChoiceColor")
        
        for k, v in value.items():
            elem = color_elem.find(k)
            if elem is None:
                elem = ET.SubElement(color_elem, k)
            elem.text = str(v)

    @property
    def specialChestType(self): return self.get_text("specialChestType", "None")
    @specialChestType.setter
    def specialChestType(self, value): self.set_text("specialChestType", value)

    @property
    def globalInventoryId(self): return self.get_text("globalInventoryId/string", "")
    @globalInventoryId.setter
    def globalInventoryId(self, value): self.set_text("globalInventoryId/string", value)

    def add_item(self, name, item_id=None, stack=1, quality=0, **kwargs):
        """?????????????????????"""
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

    def remove_item(self, item_model):
        """?????????????????????"""
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
