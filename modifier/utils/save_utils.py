import os
import re
import xml.etree.ElementTree as ET
from models.base_proxy import BaseProxy

# 注册 XML 命名空间，防止保存时丢失
ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
ET.register_namespace('xsd', 'http://www.w3.org/2001/XMLSchema')
from models.farmer import Farmer
from models.pet import Pet
from models.chest import Chest

_INVALID_AMP_PATTERN = re.compile(r"&(?!(?:#\d+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9._-]*);)")
_STATS_STEPS_TAG_PATTERN = re.compile(r"<stats/stepsTaken(?:\s+[^>]*)?>([^<]*)</stats/stepsTaken>")
_STATS_STEPS_SELF_PATTERN = re.compile(r"<stats/stepsTaken(?:\s+[^>]*)?\s*/>")

def _strip_invalid_xml_chars(text):
    if not text:
        return text, 0
    removed = 0
    out = []
    for ch in text:
        code = ord(ch)
        if (
            code == 0x9
            or code == 0xA
            or code == 0xD
            or 0x20 <= code <= 0xD7FF
            or 0xE000 <= code <= 0xFFFD
            or 0x10000 <= code <= 0x10FFFF
        ):
            out.append(ch)
        else:
            removed += 1
    return "".join(out), removed

def _sanitize_xml_text(text):
    cleaned, removed = _strip_invalid_xml_chars(text)
    cleaned, amp_fixed = _INVALID_AMP_PATTERN.subn("&amp;", cleaned)
    return cleaned, removed, amp_fixed

def _remove_invalid_steps_taken_tags(text):
    values = [m.group(1) for m in _STATS_STEPS_TAG_PATTERN.finditer(text)]
    cleaned, tag_count = _STATS_STEPS_TAG_PATTERN.subn("", text)
    cleaned, self_count = _STATS_STEPS_SELF_PATTERN.subn("", cleaned)
    value = None
    for v in values:
        v = v.strip()
        if v != "":
            value = v
    return cleaned, value, tag_count + self_count

def _apply_steps_taken_to_player(root, value):
    if value is None:
        return False
    value = value.strip()
    if value == "":
        return False
    try:
        int_value = int(float(value))
    except (ValueError, TypeError):
        return False
    player = root.find("player")
    if player is None:
        return False
    stats = player.find("stats")
    if stats is None:
        stats = ET.SubElement(player, "stats")
    steps_elem = stats.find("stepsTaken")
    if steps_elem is None:
        steps_elem = ET.SubElement(stats, "stepsTaken")
    nil_attr = "{http://www.w3.org/2001/XMLSchema-instance}nil"
    if nil_attr in steps_elem.attrib:
        del steps_elem.attrib[nil_attr]
    steps_elem.text = str(int_value)
    return True

def _parse_xml_file(path):
    try:
        return ET.parse(path)
    except ET.ParseError:
        with open(path, "rb") as f:
            raw = f.read()
        text = raw.decode("utf-8-sig", errors="replace")
        sanitized, removed, amp_fixed = _sanitize_xml_text(text)
        sanitized, steps_value, steps_removed = _remove_invalid_steps_taken_tags(sanitized)
        try:
            root = ET.fromstring(sanitized)
        except ET.ParseError as exc:
            print(f"XML parse failed after sanitization for {path}: {exc}")
            raise
        if steps_removed:
            steps_applied = _apply_steps_taken_to_player(root, steps_value)
            action = "moved to player stats" if steps_applied else "removed"
            print(f"Warning: fixed {steps_removed} invalid stats/stepsTaken tag(s) in {path} ({action}).")
        if removed or amp_fixed:
            print(
                f"Warning: sanitized XML in {path} (removed {removed} invalid chars, "
                f"fixed {amp_fixed} stray '&')."
            )
        return ET.ElementTree(root)

def find_save_files(save_dir, info_file_name="SaveGameInfo"):
    """查找存档文件和信息文件"""
    if not save_dir or not os.path.exists(save_dir):
        return None, None
        
    folder_name = os.path.basename(os.path.abspath(save_dir))
    potential_main = os.path.join(save_dir, folder_name)
    
    if os.path.exists(potential_main) and os.path.isfile(potential_main):
        return potential_main, os.path.join(save_dir, info_file_name)
        
    if os.path.exists(os.path.join(save_dir, info_file_name)):
        files = [f for f in os.listdir(save_dir) if os.path.isfile(os.path.join(save_dir, f)) 
                 and f != info_file_name and not f.endswith((".py", ".bak", "_old", ".txt"))]
        if files: 
            return os.path.join(save_dir, files[0]), os.path.join(save_dir, info_file_name)
            
    return None, None

def list_save_folders(parent_dir):
    """列出目录下所有的有效存档文件夹"""
    if not parent_dir or not os.path.exists(parent_dir):
        return []
        
    save_folders = []
    try:
        for item in os.listdir(parent_dir):
            item_path = os.path.join(parent_dir, item)
            if os.path.isdir(item_path):
                main_file, info_file = find_save_files(item_path)
                if main_file:
                    save_folders.append({
                        "name": item,
                        "path": item_path,
                        "main_file": main_file,
                        "info_file": info_file
                    })
    except Exception:
        pass
    return save_folders

class SaveProxy(BaseProxy):
    """
    存档代理。
    """
    def __init__(self, main_path, info_path=None):
        self.main_path = main_path
        self.info_path = info_path
        self.tree = _parse_xml_file(main_path)
        root = self.tree.getroot()
        if root is None:
            raise ValueError(f"Failed to get root element from {main_path}")
        super().__init__(root)
        
        # 查找主玩家
        player_elem = self.root.find("player")
        self.player = Farmer(player_elem) if player_elem is not None else None
        
        # 查找联机玩家
        self.farmhands = []
        farmhands_elem = self.root.find("farmhands")
        if farmhands_elem is not None:
            for f_elem in farmhands_elem.findall("Farmer"):
                self.farmhands.append(Farmer(f_elem))

    @property
    def root(self):
        return self._element

    @property
    def year(self): return self.get_int("year")
    @year.setter
    def year(self, value): self.set_int("year", value)

    @property
    def currentSeason(self): return self.get_text("currentSeason")
    @currentSeason.setter
    def currentSeason(self, value): self.set_text("currentSeason", value)

    @property
    def dayOfMonth(self): return self.get_int("dayOfMonth")
    @dayOfMonth.setter
    def dayOfMonth(self, value): self.set_int("dayOfMonth", value)

    @property
    def isRaining(self): return self.get_bool("isRaining")
    @isRaining.setter
    def isRaining(self, value): self.set_bool("isRaining", value)

    @property
    def isDebrisWeather(self): 
        # isDebrisWeather 可能在某些旧版本或特定情况下不存在，增加默认值处理
        return self.get_bool("isDebrisWeather", False)
    @isDebrisWeather.setter
    def isDebrisWeather(self, value): self.set_bool("isDebrisWeather", value)

    @property
    def isLightning(self): return self.get_bool("isLightning")
    @isLightning.setter
    def isLightning(self, value): self.set_bool("isLightning", value)

    @property
    def isSnowing(self): return self.get_bool("isSnowing")
    @isSnowing.setter
    def isSnowing(self, value): self.set_bool("isSnowing", value)

    @property
    def isGreenRain(self): return self.get_bool("isGreenRain", False)
    @isGreenRain.setter
    def isGreenRain(self, value): self.set_bool("isGreenRain", value)

    @property
    def canCheat(self): return self.get_bool("canCheat", False)
    @canCheat.setter
    def canCheat(self, value): self.set_bool("canCheat", value)

    @property
    def spouse(self): return self.get_text("spouse")
    @spouse.setter
    def spouse(self, value): self.set_text("spouse", value)

    @property
    def playerChoiceFruitCave(self): return self.get_text("playerChoiceFruitCave", "0")
    @playerChoiceFruitCave.setter
    def playerChoiceFruitCave(self, value): self.set_text("playerChoiceFruitCave", value)

    @property
    def dailyLuck(self): return self.get_text("dailyLuck")
    @dailyLuck.setter
    def dailyLuck(self, value): self.set_text("dailyLuck", value)

    @property
    def goldenWalnuts(self): return self.get_int("goldenWalnuts", 0)
    @goldenWalnuts.setter
    def goldenWalnuts(self, value): self.set_int("goldenWalnuts", value)

    @property
    def stepsTaken(self):
        if self.player:
            return self.player.get_int("stats/stepsTaken")
        return self.get_int("stats/stepsTaken")
    @stepsTaken.setter
    def stepsTaken(self, value):
        if self.player:
            self.player.set_int("stats/stepsTaken", value)
        else:
            self.set_int("stats/stepsTaken", value)

    def get_all_pets(self):
        """获取存档中所有的宠物"""
        pets = []
        try:
            locations_elem = self.root.find("locations")
            if locations_elem is not None:
                for loc in locations_elem.findall("GameLocation"):
                    name_elem = loc.find("name")
                    loc_name = name_elem.text if name_elem is not None and name_elem.text is not None else "Unknown"
                    chars = loc.find("characters")
                    if chars is not None:
                        for char in chars:
                            # 增加防御性检查
                            if char is not None and char.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "Pet":
                                pets.append({
                                    "model": Pet(char),
                                    "location": loc_name
                                })
        except Exception as e:
            print(f"获取宠物列表时出错: {e}")
        return pets

    def get_all_chests(self):
        """获取存档中所有的箱子"""
        chests = []
        try:
            locations_elem = self.root.find("locations")
            if locations_elem is not None:
                for loc in locations_elem.findall("GameLocation"):
                    name_elem = loc.find("name")
                    loc_name = name_elem.text if name_elem is not None and name_elem.text is not None else "Unknown"
                    objs = loc.find("objects")
                    if objs is not None:
                        for item in objs.findall("item"):
                            obj = item.find("value/Object")
                            if obj is not None and obj.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "Chest":
                                chests.append({
                                    "model": Chest(obj),
                                    "location": loc_name
                                })
        except Exception as e:
            print(f"获取箱子列表时出错: {e}")
        return chests

    def get_all_animals(self):
        """获取存档中所有的农场动物"""
        from models.farm_animal import FarmAnimal
        animals = []
        try:
            locations_elem = self.root.find("locations")
            if locations_elem is not None:
                for loc in locations_elem.findall("GameLocation"):
                    name_elem = loc.find("name")
                    loc_name = name_elem.text if name_elem is not None and name_elem.text is not None else "Unknown"
                    
                    # 农场动物通常在 GameLocation 的 animals 列表中
                    animals_elem = loc.find("animals")
                    if animals_elem is not None:
                        for item in animals_elem.findall("item"):
                            animals.append({
                                "model": FarmAnimal(item),
                                "location": loc_name
                            })
        except Exception as e:
            print(f"获取动物列表时出错: {e}")
        return animals

    def save(self):
        """保存修改到文件"""
        # 彻底清理根节点可能存在的重复命名空间属性
        root = self.tree.getroot()
        if root is None:
            return
        
        # 移除所有已存在的 xmlns 属性，由我们统一控制
        to_remove = [k for k in root.attrib if k.startswith("xmlns:")]
        for k in to_remove:
            del root.attrib[k]

        # 重新设置必要的命名空间
        # xsd 必须手动设置，因为它不常出现在前缀中
        root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
        # xsi 不需要手动设置，因为 ET.register_namespace 会处理它
        
        # 遍历所有节点，确保没有 None 文本导致解析错误
        for elem in self.tree.iter():
            if elem.text is None and len(elem) == 0:
                elem.text = ""

        # 使用 utf-8-sig 以包含 BOM，并强制使用双引号声明
        # 序列化实现
        import io
        output = io.BytesIO()
        self.tree.write(output, encoding="utf-8", xml_declaration=False)
        xml_str = output.getvalue().decode("utf-8")
        
        # 1. 统一缩进逻辑：将 /> 替换为  /> (带空格)
        # 2. 将 &apos; 替换为 '
        xml_str = xml_str.replace("/>", " />").replace("&apos;", "'")
        
        with open(self.main_path, "wb") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>'.encode("utf-8-sig"))
            f.write(xml_str.encode("utf-8"))
        
        if self.info_path and os.path.exists(self.info_path):
            # 同步 SaveGameInfo
            try:
                info_tree = _parse_xml_file(self.info_path)
                info_root = info_tree.getroot()
                if info_root is None:
                    return
                
                # 同样清理 Info 的命名空间
                for k in list(info_root.attrib):
                    if k.startswith("xmlns:"):
                        del info_root.attrib[k]
                info_root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
                
                # 同步数据
                info_proxy = BaseProxy(info_root)
                info_proxy.set_text("year", self.year)
                info_proxy.set_text("currentSeason", self.currentSeason)
                info_proxy.set_text("dayOfMonth", self.dayOfMonth)
                
                if self.player:
                    sync_player_xml(info_root, self.player.raw)
                
                # 同样对 Info 应用格式化逻辑
                info_output = io.BytesIO()
                info_tree.write(info_output, encoding="utf-8", xml_declaration=False)
                info_xml_str = info_output.getvalue().decode("utf-8")
                info_xml_str = info_xml_str.replace("/>", " />").replace("&apos;", "'")
                
                with open(self.info_path, "wb") as f:
                    f.write('<?xml version="1.0" encoding="utf-8"?>'.encode("utf-8-sig"))
                    f.write(info_xml_str.encode("utf-8"))
            except Exception as e:
                print(f"同步 SaveGameInfo 时出错: {e}")

def sync_player_xml(target_elem, source_elem):
    """
    同步玩家数据到另一个 XML 元素（通常用于 SaveGameInfo）。
    使用 Farmer 模型来简化逻辑。
    """
    s_player = Farmer(source_elem)
    t_player = Farmer(target_elem)
    
    # 同步基础属性
    t_player.name = s_player.name
    t_player.money = s_player.money
    t_player.maxHealth = s_player.maxHealth
    t_player.maxStamina = s_player.maxStamina
    t_player.gender = s_player.gender
    t_player.houseUpgradeLevel = s_player.houseUpgradeLevel
    t_player.totalMoneyEarned = s_player.totalMoneyEarned
    
    # 同步经验
    for i, exp in enumerate(s_player.experiencePoints):
        t_player.set_experience(i, exp)
    
    # 同步职业
    t_player.set_professions(s_player.get_professions())
    
    # 同步好感度 (这部分保持原始 XML 操作，因为好感度结构较复杂)
    s_friend = source_elem.find("friendshipData")
    t_friend = target_elem.find("friendshipData")
    if s_friend is not None and t_friend is not None:
        for s_item in s_friend.findall("item"):
            s_key = s_item.find("key/string")
            s_val = s_item.find("value/Friendship/Points")
            if s_key is not None and s_val is not None:
                for t_item in t_friend.findall("item"):
                    t_key = t_item.find("key/string")
                    t_val = t_item.find("value/Friendship/Points")
                    if t_key is not None and t_key.text == s_key.text and t_val is not None:
                        t_val.text = s_val.text
                        break
