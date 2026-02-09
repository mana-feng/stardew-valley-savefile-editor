import xml.etree.ElementTree as ET
import json
import os
import random
import re
from models.base_proxy import BaseProxy

_XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"
_XSI_NIL = "{http://www.w3.org/2001/XMLSchema-instance}nil"

TYPE_TO_ITEM_TYPE_MAP = {
    "Object": "Object",
    "BigCraftable": "Object",
    "Furniture": "Furniture",
    "Weapon": "MeleeWeapon",
    "Hat": "Hat",
    "Shirt": "Clothing",
    "Pants": "Clothing",
    "Boots": "Boots",
    "Trinket": "Trinket",
    "Mannequin": "Mannequin",
}

TOOL_TYPE_MAP = {
    "Pail": "MilkPail",
    "Pickaxe": "Pickaxe",
    "Axe": "Axe",
    "Hoe": "Hoe",
    "Can": "WateringCan",
    "Rod": "FishingRod",
    "Pan": "Pan",
    "Wand": "Wand",
}

TOOL_NAME_MAP = {
    "Can": "Watering Can",
    "Rod": "Fishing Rod",
    "Pan": "Copper Pan",
}

UPGRADE_LEVELS = [
    ("Copper", 1),
    ("Steel", 2),
    ("Gold", 3),
    ("Iridium", 4),
]

FISHING_ROD_UPGRADE_NUMBER = {
    "Bamboo Pole": 0,
    "Training Rod": 1,
    "Fiberglass Rod": 2,
    "Iridium Rod": 3,
}

FISHING_ROD_SPRITE_INDEX = {
    "Bamboo Pole": 8,
    "Training Rod": 9,
    "Fiberglass Rod": 10,
    "Iridium Rod": 11,
}

TYPE_TO_CATEGORY = {
    "BigCraftable": -9,
    "Boots": -97,
    "Pants": -100,
    "Shirt": -100,
    "Furniture": -24,
    "Hat": -95,
    "Weapon": -98,
    "Tool": -99,
    "Trinket": -101,
    "Mannequin": -24,
}

PREFIX_TYPE_MAP = {
    "O": "Object",
    "BC": "BigCraftable",
    "F": "Furniture",
    "W": "Weapon",
    "H": "Hat",
    "S": "Shirt",
    "P": "Pants",
    "B": "Boots",
    "TR": "Trinket",
}

TYPE_TO_PREFIX_MAP = {v: k for k, v in PREFIX_TYPE_MAP.items()}
# 补充一些映射
TYPE_TO_PREFIX_MAP["MeleeWeapon"] = "W"
TYPE_TO_PREFIX_MAP["Ring"] = "O"

RINGS_UNIQUE_ID = {
    "Small Glow Ring": 1267,
    "Glow Ring": 1238,
    "Small Magnet Ring": 1269,
    "Magnet Ring": 1270,
    "Slime Charmer Ring": 1271,
    "Warrior Ring": 1272,
    "Vampire Ring": 1273,
    "Savage Ring": 1274,
    "Ring of Yoba": 1275,
    "Sturdy Ring": 1276,
    "Burglar's Ring": 1247,
    "Iridium Band": 1248,
    "Jukebox Ring": 1249,
    "Amethyst Ring": 1169,
    "Topaz Ring": 1281,
    "Aquamarine Ring": 1191,
    "Jade Ring": 1253,
    "Emerald Ring": 1254,
    "Ruby Ring": 1285,
    "Crabshell Ring": 1531,
    "Napalm Ring": 1562,
    "Thorns Ring": 1590,
    "Lucky Ring": 1580,
    "Hot Java Ring": 1581,
    "Protection Ring": 1612,
    "Soul Sapper Ring": 1613,
    "Phoenix Ring": 1614,
    "Combined Ring": 1601,
    "Glowstone Ring": 1609,
}

FURNITURE_TYPE_TO_NUMBER = {
    "chair": 0,
    "bench": 1,
    "couch": 2,
    "armchair": 3,
    "dresser": 4,
    "longtable": 5,
    "painting": 6,
    "lamp": 7,
    "decor": 8,
    "other": 9,
    "bookcase": 10,
    "table": 11,
    "rug": 12,
    "window": 13,
    "fireplace": 14,
    "bed": 15,
    "torch": 16,
    "sconce": 17,
}

CLOTHES_TYPE = {
    "Shirt": "SHIRT",
    "Pants": "PANTS",
}

_COLOR_RGB_RE = re.compile(r"^rgb\((\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})\)$")

def _normalize_item_id(item_id):
    if not item_id:
        return None, None
    raw = str(item_id).strip()
    match = re.match(r"^\(([^)]+)\)(.+)$", raw)
    if match:
        prefix = match.group(1)
        key = match.group(2)
        return key, PREFIX_TYPE_MAP.get(prefix)
    return raw, None

def _compute_packed_value(r, g, b, a):
    return (
        ((a & 0xFF) << 24)
        | ((b & 0xFF) << 16)
        | ((g & 0xFF) << 8)
        | (r & 0xFF)
    ) & 0xFFFFFFFF

def _set_color_element(parent, tag, r, g, b, a=255):
    color_elem = parent.find(tag)
    if color_elem is None:
        color_elem = ET.SubElement(parent, tag)
    for key, value in (("R", r), ("G", g), ("B", b), ("A", a)):
        child = color_elem.find(key)
        if child is None:
            child = ET.SubElement(color_elem, key)
        child.text = str(int(value))
    packed = color_elem.find("PackedValue")
    if packed is None:
        packed = ET.SubElement(color_elem, "PackedValue")
    packed.text = str(_compute_packed_value(r, g, b, a))

def _parse_color(value):
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("#") and len(text) in (7, 9):
            r = int(text[1:3], 16)
            g = int(text[3:5], 16)
            b = int(text[5:7], 16)
            a = int(text[7:9], 16) if len(text) == 9 else 255
            return r, g, b, a
        match = _COLOR_RGB_RE.match(text)
        if match:
            r = int(match.group(1))
            g = int(match.group(2))
            b = int(match.group(3))
            return r, g, b, 255
        parts = text.replace(",", " ").split()
        if len(parts) >= 3:
            r = int(parts[0])
            g = int(parts[1])
            b = int(parts[2])
            a = int(parts[3]) if len(parts) > 3 else 255
            return r, g, b, a
    if isinstance(value, dict):
        r = int(value.get("R", 0))
        g = int(value.get("G", 0))
        b = int(value.get("B", 0))
        a = int(value.get("A", 255))
        return r, g, b, a
    return None

def _set_vector(parent, tag, x, y):
    vec = parent.find(tag)
    if vec is None:
        vec = ET.SubElement(parent, tag)
    for key, value in (("X", x), ("Y", y)):
        child = vec.find(key)
        if child is None:
            child = ET.SubElement(vec, key)
        child.text = str(int(value))

def _set_rectangle(parent, tag, x, y, width, height, include_size_location=True):
    rect = parent.find(tag)
    if rect is None:
        rect = ET.SubElement(parent, tag)
    for key, value in (("X", x), ("Y", y), ("Width", width), ("Height", height)):
        child = rect.find(key)
        if child is None:
            child = ET.SubElement(rect, key)
        child.text = str(int(value))
    if include_size_location:
        _set_vector(rect, "Location", x, y)
        _set_vector(rect, "Size", width, height)

def _normalize_preserve_type(label, output_item_id):
    if label == "Pickles":
        return "Pickle"
    if label == "Aged Roe":
        return "AgedRoe"
    if label == "Smoked":
        return "SmokedFish"
    if label == "Dried":
        return "DriedMushroom" if output_item_id == "DriedMushrooms" else "DriedFruit"
    if label == "Wine":
        return "Wine"
    if label == "Jelly":
        return "Jelly"
    if label == "Juice":
        return "Juice"
    if label == "Roe":
        return "Roe"
    if label == "Honey":
        return "Honey"
    if label == "Bait":
        return "Bait"
    raise ValueError(f"Unknown preserve type: {label}")

_DIMENSIONS = None

def _get_dimensions():
    global _DIMENSIONS
    if _DIMENSIONS is not None:
        return _DIMENSIONS
    
    import sys
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # type: ignore
    else:
        # 开发模式下，指向项目根目录的 generated 文件夹
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
    path = os.path.join(base_dir, "generated", "dimensions.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _DIMENSIONS = {name: size for name, size in data}
    except Exception:
        _DIMENSIONS = {}
    return _DIMENSIONS

def _compute_furniture_source_rect(data, width, height):
    sheet = data.get("texture") or "furniture.png"
    sheet_size = _get_dimensions().get(sheet)
    if not sheet_size:
        return None
    sheet_w = int(sheet_size.get("width", 0))
    sheet_h = int(sheet_size.get("height", 0))
    if not sheet_w or not sheet_h:
        return None
    index = data.get("menuSpriteIndex")
    if index is None or index < 0:
        index = data.get("spriteIndex")
    if index is None:
        try:
            index = int(data.get("_key", 0))
        except (ValueError, TypeError):
            return None
    try:
        index = int(index)
    except (ValueError, TypeError):
        return None
    sheet_lower = str(sheet).lower()
    item_w = 16 if "furniture" in sheet_lower else width
    item_h = 16 if "furniture" in sheet_lower else height
    x = sheet_w - ((index * item_w) % sheet_w)
    y = sheet_h - (index * item_w // sheet_w) * item_h
    return sheet_w - x, sheet_h - y

class Item(BaseProxy):
    """
    物品代理类，封装物品的 XML 操作。
    """
    def __init__(self, element: ET.Element):
        super().__init__(element)

    @classmethod
    def from_name(cls, name: str | None, item_id: str | None = None):
        from utils.item_manager import item_manager
        info = None
        if item_id:
            key, type_hint = _normalize_item_id(item_id)
            if key:
                info = item_manager.get_item_info_by_key(key, type_hint)
                if info is None:
                    info = item_manager.get_item_info_by_key(key)
        
        if info is None and name:
            info = item_manager.get_item_info(name)
            
        if not info:
            raise ValueError(f"Item '{name or item_id}' not found in metadata")

        data = info
        data_type = data.get("_type", "Object")
        item_name = data.get("name", name or "Unknown Item")

        element = ET.Element("Item")
        item = cls(element)

        item_type_xml = TYPE_TO_ITEM_TYPE_MAP.get(data_type)
        if data_type == "Weapon" and data.get("type") == 4:
            item_type_xml = "Slingshot"
            
        tool_upgrade_level = None
        tool_menu_index = None
        tool_initial_parent = None
        tool_parent_sheet = None
        tool_is_bottomless = None

        if data_type == "Tool":
            name_without_prefix = item_name.split(" ").pop() if item_name else ""
            item_type_xml = TOOL_TYPE_MAP.get(name_without_prefix)
            if item_type_xml in ["Pickaxe", "Axe", "Hoe", "WateringCan"]:
                tool_upgrade_level = 0
                for level_name, level_value in UPGRADE_LEVELS:
                    if item_name.startswith(level_name):
                        tool_upgrade_level = level_value
                        item_name = TOOL_NAME_MAP.get(
                            name_without_prefix,
                            name_without_prefix,
                        )
                        break
                if data.get("menuSpriteIndex") is not None:
                    tool_menu_index = data.get("menuSpriteIndex")
            if item_type_xml == "FishingRod":
                tool_upgrade_level = FISHING_ROD_UPGRADE_NUMBER.get(
                    data.get("name"),
                    0,
                )
                tool_parent_sheet = 685
                tool_initial_parent = FISHING_ROD_SPRITE_INDEX.get(
                    data.get("name"),
                    0,
                )
                tool_menu_index = tool_initial_parent
            if item_type_xml == "WateringCan":
                tool_is_bottomless = False
            if not item_type_xml:
                item_type_xml = TOOL_TYPE_MAP.get(data.get("class", ""))

        item.name = item_name
        item.itemId = data.get("_key", "")
        item.stack = 1
        item.quality = 0
        item.set_bool("isRecipe", False)
        item.price = data.get("price", 0)
        item.set_bool("hasBeenInInventory", True)
        item.set_bool("isLostItem", False)
        item.set_bool("specialItem", False)
        item.set_int("SpecialVariable", 0)

        category = data.get("category")
        if category is None:
            category = TYPE_TO_CATEGORY.get(data_type)
        if category is not None:
            item.set_int("category", category)

        if data.get("spriteIndex") is not None:
            item.set_int("parentSheetIndex", data.get("spriteIndex", 0))
            item.set_int("indexInTileSheet", data.get("spriteIndex", 0))

        _set_rectangle(element, "boundingBox", 0, 0, 64, 64)
        _set_vector(element, "tileLocation", 0, 0)
        item.set_bool("canBeSetDown", True)
        item.set_bool("canBeGrabbed", True)

        if data_type == "BigCraftable":
            item.set_bool("bigCraftable", True)
            item.set_text("type", "Crafting")
        elif data_type == "Object":
            if data.get("type") is not None:
                item.set_text("type", data.get("type"))

        if tool_upgrade_level is not None:
            item.set_int("upgradeLevel", tool_upgrade_level)
        if tool_menu_index is not None:
            item.set_int("indexOfMenuItemView", tool_menu_index)
        if tool_initial_parent is not None:
            item.set_int("initialParentTileIndex", tool_initial_parent)
        if tool_parent_sheet is not None:
            item.set_int("parentSheetIndex", tool_parent_sheet)
        if tool_is_bottomless is not None:
            item.set_bool("IsBottomless", tool_is_bottomless)
            item.set_bool("isBottomless", tool_is_bottomless)

        if data_type == "Weapon":
            item.set_int("minDamage", data.get("minDamage", 0))
            item.set_int("maxDamage", data.get("maxDamage", 0))
            item.set_int("speed", data.get("speed", 0))
            item.set_int("addedPrecision", data.get("precision", 0))
            item.set_int("addedDefense", data.get("defense", 0))
            item.set_int("addedAreaOfEffect", data.get("areaOfEffect", 0))
            item.set_int("knockback", data.get("knockback", 0))
            item.set_text("critChance", data.get("critChance", 0))
            item.set_text("critMultiplier", data.get("critMultiplier", 0))

        if data_type == "Trinket":
            item.set_int("generationSeed", random.randint(0, 9999998))

        if item_type_xml:
            element.set(_XSI_TYPE, item_type_xml)

        if data_type == "Object" and data.get("type") == "Ring":
            ring_id = RINGS_UNIQUE_ID.get(item_name)
            if ring_id is not None:
                item.set_int("uniqueID", ring_id)
            element.set(_XSI_TYPE, "Ring")

        if data_type == "Hat":
            which_elem = element.find("which")
            if which_elem is None:
                which_elem = ET.SubElement(element, "which")
            which_elem.set(_XSI_NIL, "true")
            if data.get("showRealHair") is not None:
                item.set_bool("skipHairDraw", data.get("showRealHair"))
            if data.get("skipHairstyleOffset") is not None:
                item.set_bool("ignoreHairstyleOffset", data.get("skipHairstyleOffset"))

        if data_type == "Furniture":
            item.set_bool("canBeGrabbed", True)
            ftype = data.get("type")
            if ftype is not None:
                item.set_int(
                    "type",
                    FURNITURE_TYPE_TO_NUMBER.get(str(ftype).lower(), 0),
                )
            if data.get("tilesheetSize"):
                size = data.get("tilesheetSize", {})
                width = int(size.get("width", 1)) * 16
                height = int(size.get("height", 1)) * 16
                coords = _compute_furniture_source_rect(data, width, height)
                if coords:
                    x, y = coords
                    _set_rectangle(element, "sourceRect", x, y, width, height)
                    _set_rectangle(element, "defaultSourceRect", x, y, width, height)
            if data.get("boundingBoxSize"):
                size = data.get("boundingBoxSize", {})
                width = int(size.get("width", 0))
                height = int(size.get("height", 0))
                _set_rectangle(element, "boundingBox", 0, 0, width, height)
                _set_rectangle(element, "defaultBoundingBox", 0, 0, width, height)
            if str(data.get("type", "")).lower() == "lamp":
                item.set_bool("isLamp", True)

        if data_type in CLOTHES_TYPE:
            item.set_text("clothesType", CLOTHES_TYPE[data_type])
            # 如果是 Pants，确保 xsi:type 是 Clothing (虽然 TYPE_TO_ITEM_TYPE_MAP 已经定义了，但显式检查一下更稳)
            if data_type == "Pants":
                element.set(_XSI_TYPE, "Clothing")
            item.set_int("Price", data.get("price", 0))
            if "canBeDyed" in data:
                item.set_bool("dyeable", data.get("canBeDyed"))
                if data.get("canBeDyed"):
                    _set_color_element(element, "clothesColor", 255, 255, 255, 255)
            if "isPrismatic" in data:
                item.set_bool("isPrismatic", data.get("isPrismatic"))
            if "hasSleeves" in data:
                item.set_bool("hasSleeves", data.get("hasSleeves"))

        if data_type == "Boots" and "colorIndex" in data:
            item.set_int("indexInColorSheet", data.get("colorIndex", 0))
        if data_type == "Boots":
            if "defense" in data:
                item.set_int("addedDefense", data.get("defense", 0))
            if "immunity" in data:
                item.set_int("immunityBonus", data.get("immunity", 0))

        if data.get("unpreservedItemId") and data.get("preservedItemName"):
            try:
                item.set_int(
                    "preservedParentSheetIndex",
                    int(data.get("unpreservedItemId")),
                )
                item.set_text(
                    "preserve",
                    _normalize_preserve_type(
                        data.get("preservedItemName"),
                        data.get("_key"),
                    ),
                )
            except (ValueError, TypeError):
                pass

        if data.get("color"):
            color = _parse_color(data.get("color"))
            if color:
                _set_color_element(
                    element,
                    "color",
                    color[0],
                    color[1],
                    color[2],
                    color[3],
                )
                if data_type == "Object":
                    element.set(_XSI_TYPE, "ColoredObject")

        if data.get("edibility") is not None:
            item.set_int("edibility", data.get("edibility", 0))

        return item

    @property
    def name(self): return self.get_text("name")
    @name.setter
    def name(self, value): self.set_text("name", value)

    @property
    def itemId(self): return self.get_text("itemId")
    @itemId.setter
    def itemId(self, value): self.set_text("itemId", value)

    @property
    def prefixedId(self):
        """返回带前缀的内部 ID (例如 (H)30)"""
        raw_id = self.itemId
        if not raw_id:
            return ""
        
        # 如果已经带前缀了，直接返回
        if raw_id.startswith("("):
            return raw_id
            
        xsi_type = self._element.get("{http://www.w3.org/2001/XMLSchema-instance}type")
        prefix = ""
        
        if xsi_type == "Clothing":
            c_type = self.get_text("clothesType")
            if c_type == "SHIRT": prefix = "S"
            elif c_type == "PANTS": prefix = "P"
        elif xsi_type in TYPE_TO_PREFIX_MAP:
            prefix = TYPE_TO_PREFIX_MAP[xsi_type]
        elif xsi_type == "Object":
            # 如果是 BigCraftable，前缀是 BC，否则是 O
            if self.get_bool("bigCraftable"):
                prefix = "BC"
            else:
                prefix = "O"
            
        if prefix:
            return f"({prefix}){raw_id}"
        return raw_id

    @property
    def stack(self): return self.get_int("stack", 1)
    @stack.setter
    def stack(self, value): self.set_int("stack", value)

    @property
    def quality(self): return self.get_int("quality", 0)
    @quality.setter
    def quality(self, value): self.set_int("quality", value)

    # 战斗相关属性
    @property
    def minDamage(self): return self.get_int("minDamage", 0)
    @minDamage.setter
    def minDamage(self, value): self.set_int("minDamage", value)

    @property
    def maxDamage(self): return self.get_int("maxDamage", 0)
    @maxDamage.setter
    def maxDamage(self, value): self.set_int("maxDamage", value)

    @property
    def speed(self): return self.get_int("speed", 0)
    @speed.setter
    def speed(self, value): self.set_int("speed", value)

    @property
    def knockback(self): return self.get_int("knockback", 0)
    @knockback.setter
    def knockback(self, value): self.set_int("knockback", value)

    @property
    def critChance(self):
        try:
            val = self.get_text("critChance")
            return float(val) if val else 0.0
        except (ValueError, TypeError):
            return 0.0
    @critChance.setter
    def critChance(self, value): self.set_text("critChance", value)

    @property
    def critMultiplier(self):
        try:
            val = self.get_text("critMultiplier")
            return float(val) if val else 0.0
        except (ValueError, TypeError):
            return 0.0
    @critMultiplier.setter
    def critMultiplier(self, value): self.set_text("critMultiplier", value)

    @property
    def defense(self): return self.get_int("defense", 0)
    @defense.setter
    def defense(self, value): self.set_int("defense", value)

    @property
    def immunityBonus(self): return self.get_int("immunityBonus", 0)
    @immunityBonus.setter
    def immunityBonus(self, value): self.set_int("immunityBonus", value)

    # 其他属性
    @property
    def edibility(self): return self.get_int("edibility", 0)
    @edibility.setter
    def edibility(self, value): self.set_int("edibility", value)

    @property
    def price(self): return self.get_int("price", 0)
    @price.setter
    def price(self, value): self.set_int("price", value)

    @property
    def isBottomless(self): return self.get_bool("isBottomless", False)
    @isBottomless.setter
    def isBottomless(self, value): self.set_bool("isBottomless", value)

    @property
    def color(self):
        """返回物品颜色 (R, G, B, A)"""
        color_elem = self._element.find("color")
        if color_elem is not None:
            return {
                "R": int(color_elem.findtext("R", "255")),
                "G": int(color_elem.findtext("G", "255")),
                "B": int(color_elem.findtext("B", "255")),
                "A": int(color_elem.findtext("A", "255"))
            }
        return None

    @color.setter
    def color(self, value):
        """设置物品颜色，value 预期为字典 {"R": 255, "G": 255, ...}"""
        color_elem = self._element.find("color")
        if color_elem is None:
            color_elem = ET.SubElement(self._element, "color")
        
        for k, v in value.items():
            elem = color_elem.find(k)
            if elem is None:
                elem = ET.SubElement(color_elem, k)
            elem.text = str(v)

    @property
    def is_empty(self):
        # 检查是否是空物品节点 (xsi:nil="true")
        return self._element.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"
