from models.base_proxy import BaseProxy
from models.item import Item
from models.recipes import Recipes
from models.inventory import Inventory, is_nil_sentinel
import xml.etree.ElementTree as ET

class Farmer(BaseProxy):
    """
    玩家模型类。
    """
    def __init__(self, element: ET.Element):
        super().__init__(element)
        self._migrate_legacy_wallet_flags()
        self._inventory = Inventory(element)

    @property
    def inventory(self):
        """返回玩家背包代理对象"""
        return self._inventory

    @property
    def items(self):
        """返回玩家背包中的物品列表 (兼容旧代码)"""
        return self._inventory.all_items

    @property
    def name(self): return self.get_text("name")
    @name.setter
    def name(self, value): self.set_text("name", value)

    @property
    def money(self): return self.get_int("money")
    @money.setter
    def money(self, value): 
        # 限制金钱上限为 99999999
        try:
            val = int(value)
            if val > 99999999:
                val = 99999999
            self.set_int("money", val)
        except (ValueError, TypeError):
            self.set_int("money", value)

    @property
    def maxHealth(self): return self.get_int("maxHealth")
    @maxHealth.setter
    def maxHealth(self, value): self.set_int("maxHealth", value)

    @property
    def maxStamina(self): return self.get_int("maxStamina")
    @maxStamina.setter
    def maxStamina(self, value): self.set_int("maxStamina", value)

    @property
    def gender(self): 
        val = self.get_text("gender", None)
        if val is None or val == "":
            val = self.get_text("Gender", "0")
        
        # 兼容 "Male"/"Female" 和 "0"/"1"
        if val in ["0", "Male"]:
            return "0"
        return "1"

    @property
    def Gender(self):
        val = self.get_text("Gender", None)
        if val is None or val == "":
            val = self.get_text("gender", "Male")
        
        if val in ["0", "Male"]:
            return "Male"
        return "Female"

    @gender.setter
    def gender(self, value): 
        # value 预期为 "0" 或 "1"
        str_val = str(value)
        self.set_text("gender", str_val)
        
        # 同步 Gender 字段
        gender_str = "Male" if str_val == "0" else "Female"
        self.set_text("Gender", gender_str)
        
        # 同步 isMale 字段
        is_male = "true" if str_val == "0" else "false"
        self.set_text("isMale", is_male)

    @property
    def maxItems(self): return self.get_int("maxItems", 36)
    @maxItems.setter
    def maxItems(self, value): self.set_int("maxItems", value)

    @property
    def farmName(self): return self.get_text("farmName")
    @farmName.setter
    def farmName(self, value): self.set_text("farmName", value)

    @property
    def health(self): return self.get_int("health")
    @health.setter
    def health(self, value): self.set_int("health", value)

    @property
    def stamina(self): return self.get_int("stamina")
    @stamina.setter
    def stamina(self, value): self.set_int("stamina", value)

    @property
    def clubCoins(self): return self.get_int("clubCoins")
    @clubCoins.setter
    def clubCoins(self, value): self.set_int("clubCoins", value)

    @property
    def qiGems(self): return self.get_int("qiGems")
    @qiGems.setter
    def qiGems(self, value): self.set_int("qiGems", value)

    @property
    def masteryExp(self): return self.get_int("masteryExp")
    @masteryExp.setter
    def masteryExp(self, value): self.set_int("masteryExp", value)

    @property
    def catPerson(self): return self.get_bool("catPerson")
    @catPerson.setter
    def catPerson(self, value): 
        self.set_bool("catPerson", value)
        # 同步 isCat 字段（如果存在）
        self.set_bool("isCat", value)

    @property
    def petType(self): return self.get_text("petType")
    @petType.setter
    def petType(self, value): self.set_text("petType", value)

    @property
    def totalMoneyEarned(self): return self.get_int("totalMoneyEarned")
    @totalMoneyEarned.setter
    def totalMoneyEarned(self, value): self.set_int("totalMoneyEarned", value)

    @property
    def deepestMineLevel(self): return self.get_int("deepestMineLevel")
    @deepestMineLevel.setter
    def deepestMineLevel(self, value): self.set_int("deepestMineLevel", value)

    @property
    def trashCanLevel(self): return self.get_int("trashCanLevel")
    @trashCanLevel.setter
    def trashCanLevel(self, value): self.set_int("trashCanLevel", value)

    @property
    def luckLevel(self): return self.get_int("luckLevel")
    @luckLevel.setter
    def luckLevel(self, value): self.set_int("luckLevel", value)

    @property
    def houseUpgradeLevel(self): return self.get_int("houseUpgradeLevel")
    @houseUpgradeLevel.setter
    def houseUpgradeLevel(self, value): 
        # 限制房屋等级上限为 3 (1.6版本支持)
        try:
            val = int(value)
            if val > 3:
                val = 3
            self.set_int("houseUpgradeLevel", val)
        except (ValueError, TypeError):
            self.set_int("houseUpgradeLevel", value)

    @property
    def magneticRadius(self): return self.get_int("magneticRadius")
    @magneticRadius.setter
    def magneticRadius(self, value): self.set_int("magneticRadius", value)

    @property
    def resilience(self): return self.get_int("resilience")
    @resilience.setter
    def resilience(self, value): self.set_int("resilience", value)

    @property
    def immunity(self): return self.get_int("immunity")
    @immunity.setter
    def immunity(self, value): self.set_int("immunity", value)

    @property
    def farmingLevel(self): return self.get_int("farmingLevel")
    @farmingLevel.setter
    def farmingLevel(self, value): self.set_int("farmingLevel", value)

    @property
    def miningLevel(self): return self.get_int("miningLevel")
    @miningLevel.setter
    def miningLevel(self, value): self.set_int("miningLevel", value)

    @property
    def foragingLevel(self): return self.get_int("foragingLevel")
    @foragingLevel.setter
    def foragingLevel(self, value): self.set_int("foragingLevel", value)

    @property
    def fishingLevel(self): return self.get_int("fishingLevel")
    @fishingLevel.setter
    def fishingLevel(self, value): self.set_int("fishingLevel", value)

    @property
    def combatLevel(self): return self.get_int("combatLevel")
    @combatLevel.setter
    def combatLevel(self, value): self.set_int("combatLevel", value)

    @property
    def favoriteThing(self): return self.get_text("favoriteThing")
    @favoriteThing.setter
    def favoriteThing(self, value): self.set_text("favoriteThing", value)

    @property
    def attack(self): return self.get_int("attack")
    @attack.setter
    def attack(self, value): self.set_int("attack", value)

    @property
    def hair(self): return self.get_int("hair")
    @hair.setter
    def hair(self, value): self.set_int("hair", value)

    @property
    def hairstyle(self):
        # 兼容 1.6 的发型逻辑
        val = self.get_int("hair")
        if val >= 100:
            return val - 100 + 56
        return val

    @hairstyle.setter
    def hairstyle(self, value):
        try:
            val = int(value)
        except (ValueError, TypeError):
            val = 0
            
        if val >= 56:
            self.set_int("hair", val + 100 - 56)
        else:
            self.set_int("hair", val)

    @property
    def shirt(self): return self.get_int("shirt")
    @shirt.setter
    def shirt(self, value): self.set_int("shirt", value)

    @property
    def skin(self): return self.get_int("skin")
    @skin.setter
    def skin(self, value): self.set_int("skin", value)

    @property
    def accessory(self): return self.get_int("accessory")
    @accessory.setter
    def accessory(self, value): self.set_int("accessory", value)

    @property
    def uniqueID(self): return self.get_text("UniqueMultiplayerID")

    def get_color(self, tag):
        """获取颜色属性 (R, G, B, A)"""
        color_elem = self._element.find(tag)
        if color_elem is not None:
            r = int(color_elem.findtext("R", "0"))
            g = int(color_elem.findtext("G", "0"))
            b = int(color_elem.findtext("B", "0"))
            a = int(color_elem.findtext("A", "255"))
            return (r, g, b, a)
        return (0, 0, 0, 255)

    def set_color(self, tag, r, g, b, a=255):
        """设置颜色属性并计算 PackedValue"""
        color_elem = self._element.find(tag)
        if color_elem is None:
            color_elem = ET.SubElement(self._element, tag)
        
        for name, val in [("R", r), ("G", g), ("B", b), ("A", a)]:
            elem = color_elem.find(name)
            if elem is None:
                elem = ET.SubElement(color_elem, name)
            elem.text = str(val)
        
        # 计算 PackedValue: (((A & 0xff) << 24) | ((B & 0xff) << 16) | ((G & 0xff) << 8) | (R & 0xff)) >>> 0
        packed = (((a & 0xFF) << 24) | ((b & 0xFF) << 16) | ((g & 0xFF) << 8) | (r & 0xFF)) & 0xFFFFFFFF
        packed_elem = color_elem.find("PackedValue")
        if packed_elem is None:
            packed_elem = ET.SubElement(color_elem, "PackedValue")
        packed_elem.text = str(packed)

    @property
    def hairColor(self): return self.get_color("hairstyleColor")
    @hairColor.setter
    def hairColor(self, rgba): self.set_color("hairstyleColor", *rgba)

    @property
    def eyeColor(self): return self.get_color("newEyeColor")
    @eyeColor.setter
    def eyeColor(self, rgba): self.set_color("newEyeColor", *rgba)

    @property
    def hat(self):
        elem = self._element.find("hat")
        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None
    @hat.setter
    def hat(self, value): self._set_equipment("hat", value)

    @property
    def shirtItem(self):
        elem = self._element.find("shirtItem")
        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None
    @shirtItem.setter
    def shirtItem(self, value): self._set_equipment("shirtItem", value)

    @property
    def pantsItem(self):
        elem = self._element.find("pantsItem")
        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None
    @pantsItem.setter
    def pantsItem(self, value): self._set_equipment("pantsItem", value)

    @property
    def boots(self):
        elem = self._element.find("boots")
        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None
    @boots.setter
    def boots(self, value): self._set_equipment("boots", value)

    @property
    def leftRing(self):
        elem = self._element.find("leftRing")
        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None
    @leftRing.setter
    def leftRing(self, value): self._set_equipment("leftRing", value)

    @property
    def rightRing(self):
        elem = self._element.find("rightRing")
        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None
    @rightRing.setter
    def rightRing(self, value): self._set_equipment("rightRing", value)

    @property
    def trinketItem(self):
        elem = self._element.find("trinketItem")
        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None
    @trinketItem.setter
    def trinketItem(self, value): self._set_equipment("trinketItem", value)

    def _set_equipment(self, tag, value):
        """内部方法：通过替换元素设置装备位物品"""
        if value is None or (isinstance(value, str) and (value == "" or value.lower() == "none")):
            # 设置为 nil
            elem = self._element.find(tag)
            if elem is not None:
                for child in list(elem): elem.remove(child)
                elem.set("{http://www.w3.org/2001/XMLSchema-instance}nil", "true")
            return

        # 创建新物品
        if isinstance(value, Item):
            new_item = value
        else:
            # 根据 ID 创建新物品，确保 xsi:type 等属性正确
            new_item = Item.from_name(None, item_id=str(value))
        
        # 使用 Inventory.set_item 的逻辑来确保元素被正确替换且 tag 正确
        self._inventory.set_item(tag, new_item)

    # --- 邮件与特殊标志 ---
    def has_mail(self, mail_id):
        """检查是否收到特定邮件"""
        mail_elem = self._element.find("mailReceived")
        if mail_elem is not None:
            for s in mail_elem.findall("string"):
                if s.text == mail_id:
                    return True
        return False

    def add_mail(self, mail_id):
        """添加收到邮件的标志"""
        if self.has_mail(mail_id):
            return
        mail_elem = self._element.find("mailReceived")
        if mail_elem is None:
            mail_elem = ET.SubElement(self._element, "mailReceived")
        new_mail = ET.SubElement(mail_elem, "string")
        new_mail.text = mail_id

    def remove_mail(self, mail_id):
        """移除收到邮件的标志"""
        mail_elem = self._element.find("mailReceived")
        if mail_elem is not None:
            for s in mail_elem.findall("string"):
                if s.text == mail_id:
                    mail_elem.remove(s)

    def has_achievement(self, achievement_id):
        """检查是否获得特定成就"""
        ach_elem = self._element.find("achievements")
        if ach_elem is not None:
            for i in ach_elem.findall("int"):
                if i.text == str(achievement_id):
                    return True
        return False

    def add_achievement(self, achievement_id):
        """添加成就"""
        if self.has_achievement(achievement_id):
            return
        ach_elem = self._element.find("achievements")
        if ach_elem is None:
            ach_elem = ET.SubElement(self._element, "achievements")
        new_ach = ET.SubElement(ach_elem, "int")
        new_ach.text = str(achievement_id)

    def remove_achievement(self, achievement_id):
        """移除成就"""
        ach_elem = self._element.find("achievements")
        if ach_elem is not None:
            for i in ach_elem.findall("int"):
                if i.text == str(achievement_id):
                    ach_elem.remove(i)

    # --- 社交相关 ---
    @property
    def friendshipData(self):
        """返回好感度数据列表"""
        data = []
        fd_elem = self._element.find("friendshipData")
        if fd_elem is not None:
            for item in fd_elem.findall("item"):
                name_elem = item.find("key/string")
                if name_elem is None or name_elem.text is None:
                    continue
                name = name_elem.text
                f_elem = item.find("value/Friendship")
                if f_elem is None:
                    continue
                
                points_elem = f_elem.find("Points")
                points = int(points_elem.text) if points_elem is not None and points_elem.text else 0
                
                data.append({
                    "name": name,
                    "points": points,
                    "element": f_elem # 保存引用以便更新
                })
        return data

    def update_friendship(self, name, points):
        """更新指定 NPC 的好感度"""
        fd_elem = self._element.find("friendshipData")
        if fd_elem is None:
            fd_elem = ET.SubElement(self._element, "friendshipData")
        
        for item in fd_elem.findall("item"):
            name_elem = item.find("key/string")
            if name_elem is not None and name_elem.text == name:
                f_elem = item.find("value/Friendship")
                if f_elem is not None:
                    points_elem = f_elem.find("Points")
                    if points_elem is None:
                        points_elem = ET.SubElement(f_elem, "Points")
                    points_elem.text = str(points)
                    return
        
        # 如果没找到，创建一个新的
        item = ET.SubElement(fd_elem, "item")
        key = ET.SubElement(item, "key")
        ET.SubElement(key, "string").text = name
        value = ET.SubElement(item, "value")
        friendship = ET.SubElement(value, "Friendship")
        ET.SubElement(friendship, "Points").text = str(points)
        ET.SubElement(friendship, "GiftsThisWeek").text = "0"
        ET.SubElement(friendship, "GiftsToday").text = "0"
        ET.SubElement(friendship, "TalkedToToday").text = "false"
        ET.SubElement(friendship, "ProposalRejected").text = "false"
        ET.SubElement(friendship, "Status").text = "Friendly"
        ET.SubElement(friendship, "Proposer").text = "0"
        ET.SubElement(friendship, "RoommateMarriage").text = "false"

    # --- 技能相关 ---
    XP_FOR_LEVEL = [0, 100, 380, 770, 1300, 2150, 3300, 4800, 6900, 10000, 15000]

    def xp_to_level(self, xp):
        level = 0
        for i, req in enumerate(self.XP_FOR_LEVEL):
            if xp < req:
                break
            level = i
        return level

    @property
    def experiencePoints(self):
        """返回经验值列表 [耕种, 采矿, 采集, 钓鱼, 战斗, ...]"""
        xp_elem = self._element.find("experiencePoints")
        if xp_elem is not None:
            return [int(i.text) if i.text is not None else 0 for i in xp_elem.findall("int")]
        return [0, 0, 0, 0, 0, 0]

    def set_experience(self, skill_index, xp):
        """设置特定技能的经验值，并同步等级字段"""
        # 限制经验值上限为 15000
        try:
            val = int(xp)
            if val > 15000:
                val = 15000
        except (ValueError, TypeError):
            val = xp

        xp_elem = self._element.find("experiencePoints")
        if xp_elem is None:
            xp_elem = ET.SubElement(self._element, "experiencePoints")
        
        ints = xp_elem.findall("int")
        while len(ints) <= skill_index:
            new_int = ET.SubElement(xp_elem, "int")
            new_int.text = "0"
            ints.append(new_int)
        
        ints[skill_index].text = str(val)
        
        # 同步等级字段 (farmingLevel, miningLevel, foragingLevel, fishingLevel, combatLevel, luckLevel)
        level = self.xp_to_level(val)
        skill_names = ["farmingLevel", "miningLevel", "foragingLevel", "fishingLevel", "combatLevel", "luckLevel"]
        if 0 <= skill_index < len(skill_names):
            self.set_int(skill_names[skill_index], level)

    @property
    def professions_list(self):
        return self.get_professions()
    
    @professions_list.setter
    def professions_list(self, value):
        self.set_professions(value)

    @property
    def cookingRecipes(self):
        elem = self._element.find("cookingRecipes")
        if elem is None:
            elem = ET.SubElement(self._element, "cookingRecipes")
        return Recipes(elem, "cookingRecipes")

    @property
    def craftingRecipes(self):
        elem = self._element.find("craftingRecipes")
        if elem is None:
            elem = ET.SubElement(self._element, "craftingRecipes")
        return Recipes(elem, "craftingRecipes")

    def add_item(self, name, item_id=None, stack=1, quality=0):
        """添加物品到玩家背包"""
        items_elem = self._element.find("items")
        if items_elem is None:
            items_elem = ET.SubElement(self._element, "items")

        nil_qname = "{http://www.w3.org/2001/XMLSchema-instance}nil"
        items = items_elem.findall("Item")
        if len(items) < self.maxItems:
            for _ in range(self.maxItems - len(items)):
                nil_elem = ET.SubElement(items_elem, "Item")
                nil_elem.set(nil_qname, "true")
            items = items_elem.findall("Item")

        item = Item.from_name(name, item_id=item_id)
        item.stack = stack
        item.quality = quality

        target_index = None
        for idx, elem in enumerate(items):
            if is_nil_sentinel(elem) or elem.findtext("name", "").startswith("Secret Note"):
                target_index = idx
                break

        if target_index is None:
            max_items = self.maxItems
            if max_items < 36:
                new_max = min(36, ((max_items // 12) + 1) * 12)
                self.maxItems = new_max
                for _ in range(new_max - len(items)):
                    nil_elem = ET.SubElement(items_elem, "Item")
                    nil_elem.set(nil_qname, "true")
                items = items_elem.findall("Item")
                target_index = max_items
            else:
                items_elem.append(item.raw)
                return item

        self._inventory.set_item(target_index, item)
        return item

    def remove_item(self, item_model):
        """从玩家背包移除物品"""
        items_elem = self._element.find("items")
        if items_elem is None:
            return
        items = items_elem.findall("Item")
        for idx, elem in enumerate(items):
            if elem is item_model.raw:
                self._inventory.set_item(idx, None)
                return

    def get_professions(self):
        prof_elem = self._element.find("professions")
        if prof_elem is not None:
            return [int(i.text) if i.text is not None else 0 for i in prof_elem.findall("int")]
        return []

    def set_professions(self, profession_ids):
        prof_elem = self._element.find("professions")
        if prof_elem is not None:
            for child in list(prof_elem):
                prof_elem.remove(child)
            for pid in profession_ids:
                new_int = ET.SubElement(prof_elem, "int")
                new_int.text = str(pid)

    def _migrate_legacy_wallet_flags(self):
        # 迁移旧版钱包标志到 mailReceived
        wallet_flags = {
            "canUnderstandDwarves": "HasDwarvishTranslationGuide",
            "hasRustyKey": "HasRustyKey",
            "hasClubCard": "HasClubCard",
            "hasSpecialCharm": "HasSpecialCharm",
            "hasSkullKey": "HasSkullKey",
            "hasMagnifyingGlass": "HasMagnifyingGlass",
            "hasDarkTalisman": "HasDarkTalisman",
            "hasMagicInk": "HasMagicInk",
            "HasTownKey": "HasTownKey",
            "hasUnlockedSkullDoor": "HasUnlockedSkullDoor",
        }
        
        mail_received = self._element.find("mailReceived")
        if mail_received is None:
            mail_received = ET.SubElement(self._element, "mailReceived")
        
        # 简化处理：确保 mailReceived 结构正确
        received_list = [s.text for s in mail_received.findall("string")]

        for field, flag in wallet_flags.items():
            field_elem = self._element.find(field)
            if field_elem is not None:
                # 如果字段存在且为 true (或非空)
                if field_elem.text and field_elem.text.lower() == "true":
                    if flag not in received_list:
                        new_s = ET.SubElement(mail_received, "string")
                        new_s.text = flag
                        received_list.append(flag)
                # 迁移后删除旧字段以保持 1.6 风格
                self._element.remove(field_elem)
