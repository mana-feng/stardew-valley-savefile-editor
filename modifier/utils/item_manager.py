import json
import os

class ItemManager:
    _instance = None
    _data = {}
    _data_by_key = {}
    _data_by_key_any = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ItemManager, cls).__new__(cls)
            cls._instance._load_data()
        return cls._instance

    def _load_data(self):
        # 尝试加载 generated/iteminfo.json
        # 路径相对于项目根目录
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # type: ignore
            json_path = os.path.join(base_dir, "generated", "iteminfo.json")
        else:
            # 开发模式下，指向项目根目录的 generated 文件夹
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            json_path = os.path.join(base_dir, "generated", "iteminfo.json")
        self._data = {}
        self._data_by_key = {}
        self._data_by_key_any = {}
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    # raw_data 是一个 [[name, info], ...] 的列表
                    for name, info in raw_data:
                        self._data[name] = info
                        key = str(info.get("_key", ""))
                        item_type = info.get("_type")
                        if key and item_type:
                            self._data_by_key[(key, item_type)] = info
                            self._data_by_key_any.setdefault(key, []).append(info)
            except Exception as e:
                print(f"Error loading iteminfo.json: {e}")
        else:
            print(f"iteminfo.json not found at {json_path}")

    def get_item_info(self, name):
        return self._data.get(name)

    def get_item_info_by_key(self, key, item_type=None):
        if key is None:
            return None
        key = str(key)
        if item_type:
            return self._data_by_key.get((key, item_type))
        infos = self._data_by_key_any.get(key, [])
        if len(infos) == 1:
            return infos[0]
        return None

    def get_all_names(self):
        return list(self._data.keys())

item_manager = ItemManager()
