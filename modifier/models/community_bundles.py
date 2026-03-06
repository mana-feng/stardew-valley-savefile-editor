# Represent community bundle state and reward progress stored in save files.
from models.base_proxy import BaseProxy

import xml.etree.ElementTree as ET

# Safely convert the provided value to an integer.
# It reads or mutates the XML-backed save model used by the editor.
def safe_int(value, default=0):

    try:

        if value is None: return default

        return int(str(value).strip())

    except (ValueError, TypeError):

        return default

# Define the bundle type used by this module.
# It reads or mutates the XML-backed save model used by the editor.
class Bundle(BaseProxy):

    def __init__(self, element, data_key, data_value, submitted_booleans):

        super().__init__(element)

        self.data_key = data_key

        self.data_value = data_value

        self.submitted_booleans = submitted_booleans

        parts = data_key.split("/")

        self.room_name = parts[0]

        self.sprite_index = safe_int(parts[1]) if len(parts) > 1 else 0

        v_parts = data_value.split("/")

        self.name = v_parts[0]

        self.reward = v_parts[1] if len(v_parts) > 1 else ""

        self.requirements_raw = v_parts[2] if len(v_parts) > 2 else ""

        self.color = safe_int(v_parts[3]) if len(v_parts) > 3 else 0

        self.required_count = safe_int(v_parts[4]) if len(v_parts) > 4 else 0

        self.requirements = []

        req_tokens = self.requirements_raw.split()

        for i in range(0, len(req_tokens), 3):

            if i + 2 < len(req_tokens):

                self.requirements.append({

                    "id": req_tokens[i],

                    "quantity": safe_int(req_tokens[i+1]),

                    "quality": safe_int(req_tokens[i+2])

                })

    # Return the bundle's completed.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def completed(self):

        needed = self.required_count if self.required_count > 0 else len(self.requirements)

        submitted_count = sum(1 for b in self.submitted_booleans if b)

        return submitted_count >= needed

    # Set the submitted.
    # It reads or mutates the XML-backed save model used by the editor.
    def set_submitted(self, index, value):

        if 0 <= index < len(self.submitted_booleans):

            self.submitted_booleans[index] = value

            bool_elems = self._element.find("value/ArrayOfBoolean")

            if bool_elems is not None:

                bools = bool_elems.findall("boolean")

                if index < len(bools):

                    bools[index].text = "true" if value else "false"

    # Mark every bundle in the dialog as complete.
    # It reads or mutates the XML-backed save model used by the editor.
    def complete_all(self):

        for i in range(len(self.submitted_booleans)):

            self.set_submitted(i, True)

# Define the community bundles type used by this module.
# It reads or mutates the XML-backed save model used by the editor.
class CommunityBundles:

    def __init__(self, save_proxy):

        self.save_proxy = save_proxy

        self.bundles = []

        self._load_bundles()

    # Load the bundles.
    # It reads or mutates the XML-backed save model used by the editor.
    def _load_bundles(self):

        cc_elem = None

        for loc in self.save_proxy._element.find("locations").findall("GameLocation"):

            if loc.findtext("name") == "CommunityCenter":

                cc_elem = loc

                break

        if cc_elem is None:

            return

        bundle_data_map = {}

        bundle_data_elem = self.save_proxy._element.find("bundleData")

        if bundle_data_elem is not None:

            for item in bundle_data_elem.findall("item"):

                key = item.find("key/string").text

                value = item.find("value/string").text

                bundle_data_map[key] = value

        bundles_elem = cc_elem.find("bundles")

        if bundles_elem is not None:

            for item in bundles_elem.findall("item"):

                sprite_index_text = item.findtext("key/int")

                sprite_index = safe_int(sprite_index_text)

                booleans = [b.text == "true" for b in item.find("value/ArrayOfBoolean").findall("boolean")]

                matching_key = None

                matching_value = None

                for k, v in bundle_data_map.items():

                    k_parts = k.split("/")

                    if len(k_parts) > 1 and safe_int(k_parts[1]) == sprite_index:

                        matching_key = k

                        matching_value = v

                        break

                if matching_key:

                    self.bundles.append(Bundle(item, matching_key, matching_value, booleans))

    # Return the bundles by room.
    # It reads or mutates the XML-backed save model used by the editor.
    def get_bundles_by_room(self):

        rooms = {}

        for b in self.bundles:

            if b.room_name not in rooms:

                rooms[b.room_name] = []

            rooms[b.room_name].append(b)

        return rooms
