import json
import os
import xml.etree.ElementTree as ET
from models.base_proxy import BaseProxy

class Recipes(BaseProxy):
    """
    配方代理类。
    """
    def __init__(self, element: ET.Element, recipe_type: str):
        super().__init__(element)
        self.recipe_type = recipe_type
        self.reference_data = self._load_reference_data()

    def _load_reference_data(self):
        filename = "cookingrecipes.json" if self.recipe_type == "cookingRecipes" else "craftingrecipes.json"
        # 尝试从 generated 目录加载
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # type: ignore
        else:
            # 开发模式下，指向项目根目录的 generated 文件夹
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        path = os.path.join(base_dir, "generated", filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def get_recipes_status(self):
        """返回所有配方的解锁状态 {recipe_name: craft_count or None}"""
        status = {}
        # 初始化所有配方为 None (未解锁)
        for name in self.reference_data:
            status[name] = None
        
        # 填充已解锁的配方
        for item in self._element.findall("item"):
            name_elem = item.find("key/string")
            count_elem = item.find("value/int")
            if name_elem is not None and count_elem is not None:
                try:
                    text = count_elem.text or "0"
                    status[name_elem.text] = int(text)
                except (ValueError, TypeError):
                    status[name_elem.text] = 0
        
        return status

    def set_recipe_status(self, name, count):
        """设置配方状态。count 为 None 表示删除（未解锁）"""
        # 查找现有项
        existing_item = None
        for item in self._element.findall("item"):
            name_elem = item.find("key/string")
            if name_elem is not None and name_elem.text == name:
                existing_item = item
                break
        
        if count is None:
            if existing_item is not None:
                self._element.remove(existing_item)
        else:
            if existing_item is not None:
                count_elem = existing_item.find("value/int")
                if count_elem is not None:
                    count_elem.text = str(count)
            else:
                # 创建新项
                new_item = ET.SubElement(self._element, "item")
                key_elem = ET.SubElement(new_item, "key")
                string_elem = ET.SubElement(key_elem, "string")
                string_elem.text = name
                
                val_elem = ET.SubElement(new_item, "value")
                int_elem = ET.SubElement(val_elem, "int")
                int_elem.text = str(count)
