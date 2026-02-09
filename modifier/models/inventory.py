import copy
import xml.etree.ElementTree as ET
from models.base_proxy import BaseProxy
from models.item import Item
from models.chest import Chest

def create_item_proxy(element: ET.Element):
    if element.find("playerChest") is not None or element.find("items") is not None:
        return Chest(element)
    return Item(element)

def is_nil_sentinel(element: ET.Element):
    return element.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"

class Inventory(BaseProxy):
    """
    背包管理代理类。
    管理普通背包槽位和装备栏槽位。
    """
    def __init__(self, element: ET.Element):
        super().__init__(element)
        self._items_elem = element.find("items")
        self._equip_slots = [
            "hat", "shirtItem", "pantsItem", "boots", 
            "leftRing", "rightRing", "trinketItem"
        ]

    @property
    def slot_count(self):
        if self._items_elem is not None:
            return len(self._items_elem.findall("Item"))
        return 0

    def get_item(self, index):
        """获取指定索引或名称的物品"""
        if isinstance(index, int):
            if self._items_elem is not None:
                items = self._items_elem.findall("Item")
                if 0 <= index < len(items):
                    item_elem = items[index]
                    if is_nil_sentinel(item_elem) or item_elem.findtext("name", "").startswith("Secret Note"):
                        return None
                    return create_item_proxy(item_elem)
        elif index in self._equip_slots:
            slot_elem = self._element.find(index)
            if slot_elem is not None:
                if is_nil_sentinel(slot_elem) or slot_elem.findtext("name", "").startswith("Secret Note"):
                    return None
                return create_item_proxy(slot_elem)
        return None

    def set_item(self, index, item_proxy_or_none):
        """????????????????????????????????????"""
        nil_qname = "{http://www.w3.org/2001/XMLSchema-instance}nil"

        if isinstance(index, int):
            if self._items_elem is None:
                self._items_elem = ET.SubElement(self._element, "items")
            items = self._items_elem.findall("Item")
            if index >= len(items):
                for _ in range(index - len(items) + 1):
                    nil_elem = ET.SubElement(self._items_elem, "Item")
                    nil_elem.set(nil_qname, "true")
                items = self._items_elem.findall("Item")
            if 0 <= index < len(items):
                old_elem = items[index]
                if item_proxy_or_none is None:
                    old_elem.clear()
                    old_elem.set(nil_qname, "true")
                else:
                    if old_elem is item_proxy_or_none.raw:
                        return
                    self._items_elem.remove(old_elem)
                    self._items_elem.insert(index, item_proxy_or_none.raw)
        elif index in self._equip_slots:
            if item_proxy_or_none is None:
                elem = self._element.find(index)
                if elem is not None:
                    self._element.remove(elem)
            else:
                # 增加前缀合法性检查，防止装备位放错物品
                item_id = item_proxy_or_none.prefixedId
                valid = True
                if index == "hat" and not item_id.startswith("(H)"): valid = False
                elif index == "shirtItem" and not item_id.startswith("(S)"): valid = False
                elif index == "pantsItem" and not item_id.startswith("(P)"): valid = False
                elif index == "boots" and not item_id.startswith("(B)"): valid = False
                elif index == "trinketItem" and not item_id.startswith("(TR)"): valid = False
                # 戒指比较特殊，可能是 (O) 或者没有前缀（视为 Object）
                elif index in ["leftRing", "rightRing"]:
                    if "(" in item_id and not item_id.startswith("(O)"): valid = False
                
                if not valid:
                    # 如果不合法，不进行设置（或者可以抛出异常，这里选择静默跳过或打印日志）
                    print(f"Warning: Attempted to set invalid item {item_id} to equipment slot {index}")
                    return

                new_elem = copy.deepcopy(item_proxy_or_none.raw)
                new_elem.tag = index
                existing = self._element.find(index)
                if existing is not None:
                    insert_at = list(self._element).index(existing)
                    self._element.remove(existing)
                    self._element.insert(insert_at, new_elem)
                else:
                    self._element.append(new_elem)

    def delete_item(self, index):
        """删除指定索引或名称的物品"""
        self.set_item(index, None)

    @property
    def all_items(self):
        """返回所有普通背包物品"""
        if self._items_elem is not None:
            return [create_item_proxy(i) for i in self._items_elem.findall("Item") if not is_nil_sentinel(i)]
        return []

    @property
    def equipment(self):
        """返回所有装备栏物品"""
        equip = {}
        for slot in self._equip_slots:
            item = self.get_item(slot)
            if item:
                equip[slot] = item
        return equip
