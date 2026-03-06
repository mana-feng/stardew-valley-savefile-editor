# Provide shared XML proxy helpers for save-model classes that wrap element trees.
import xml.etree.ElementTree as ET

# Wrap XML elements with higher-level accessors used by the save editor.
# It reads or mutates the XML-backed save model used by the editor.
class BaseProxy:

    def __init__(self, element: ET.Element):

        self._element = element

    # Return the text.
    # It reads or mutates the XML-backed save model used by the editor.
    def get_text(self, tag, default: str | None = ""):

        try:

            elem = self._element.find(tag)

            if elem is not None and elem.text is not None:

                return elem.text

        except Exception:

            pass

        return default

    # Set the text.
    # It reads or mutates the XML-backed save model used by the editor.
    def set_text(self, tag, value):

        elem = self._element.find(tag)

        if elem is not None:

            elem.text = str(value) if value is not None else ""

        else:

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

    # Return the int.
    # It reads or mutates the XML-backed save model used by the editor.
    def get_int(self, tag, default=0):

        try:

            val = self.get_text(tag)

            if val is None or val == "":

                return default

            return int(val)

        except (ValueError, TypeError):

            return default

    # Safely convert the provided value to an integer.
    # It reads or mutates the XML-backed save model used by the editor.
    def safe_int(self, value, default=0):

        try:

            if value is None or value == "":

                return default

            return int(value)

        except (ValueError, TypeError):

            return default

    # Set the int.
    # It reads or mutates the XML-backed save model used by the editor.
    def set_int(self, tag, value):

        try:

            if value is None or value == "":

                val = 0

            else:

                val = int(value)

            self.set_text(tag, val)

        except (ValueError, TypeError):

            self.set_text(tag, 0)

    # Return the bool.
    # It reads or mutates the XML-backed save model used by the editor.
    def get_bool(self, tag, default=False):

        val = self.get_text(tag, default=None)

        if val is None or val == "":

            return default

        val = val.lower().strip()

        if "true" in val: return True

        if "false" in val: return False

        return default

    # Set the bool.
    # It reads or mutates the XML-backed save model used by the editor.
    def set_bool(self, tag, value):

        self.set_text(tag, "true" if value else "false")

    # Return the proxy's raw.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def raw(self):

        return self._element
