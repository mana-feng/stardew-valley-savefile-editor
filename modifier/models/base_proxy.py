import xml.etree.ElementTree as ET

class BaseProxy:
    """
    基础代理类。
    封装 XML 元素的操作，使其更像 Python 对象。
    """
    def __init__(self, element: ET.Element):
        self._element = element

    def get_text(self, tag, default: str | None = ""):
        try:
            elem = self._element.find(tag)
            if elem is not None and elem.text is not None:
                return elem.text
        except Exception:
            pass
        return default

    def set_text(self, tag, value):
        elem = self._element.find(tag)
        if elem is not None:
            elem.text = str(value) if value is not None else ""
        else:
            # 如果不存在则创建
            if "/" in tag and not tag.startswith(".") and "//" not in tag and "[" not in tag and "@" not in tag:
                parts = [p for p in tag.split("/") if p]
                parent = self._element
                for part in parts[:-1]:
                    child = parent.find(part)
                    if child is None:
                        child = ET.SubElement(parent, part)
                    parent = child
                new_elem = ET.SubElement(parent, parts[-1])
            else:
                new_elem = ET.SubElement(self._element, tag)
            new_elem.text = str(value) if value is not None else ""

    def get_int(self, tag, default=0):
        try:
            val = self.get_text(tag)
            if val is None or val == "":
                return default
            return int(val)
        except (ValueError, TypeError):
            return default

    def safe_int(self, value, default=0):
        try:
            if value is None or value == "":
                return default
            return int(value)
        except (ValueError, TypeError):
            return default

    def set_int(self, tag, value):
        try:
            if value is None or value == "":
                val = 0
            else:
                val = int(value)
            self.set_text(tag, val)
        except (ValueError, TypeError):
            self.set_text(tag, 0)

    def get_bool(self, tag, default=False):
        val = self.get_text(tag, default=None)
        if val is None or val == "":
            return default
        # 兼容处理 XML 序列化中可能出现的干扰
        val = val.lower().strip()
        if "true" in val: return True
        if "false" in val: return False
        return default

    def set_bool(self, tag, value):
        self.set_text(tag, "true" if value else "false")

    @property
    def raw(self):
        return self._element
