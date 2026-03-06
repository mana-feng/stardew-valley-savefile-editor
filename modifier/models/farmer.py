# Represent the main player record and the editable fields exposed by the editor.
from models.base_proxy import BaseProxy

from models.item import Item

from models.inventory import Inventory, is_nil_sentinel

import xml.etree.ElementTree as ET


class RecipeCollectionProxy:

    def __init__(self, owner, tag_name):

        self.owner = owner

        self.tag_name = tag_name

    def _get_elem(self, create=False):

        recipes_elem = self.owner._element.find(self.tag_name)

        if recipes_elem is None and create:

            recipes_elem = ET.SubElement(self.owner._element, self.tag_name)

        return recipes_elem

    def get_recipes_status(self):

        recipes_elem = self._get_elem(create=False)

        recipes = {}

        if recipes_elem is None:

            return recipes

        for item in recipes_elem.findall("item"):

            recipe_name = item.findtext("key/string")

            if not recipe_name:

                continue

            crafted_text = item.findtext("value/int")

            try:

                recipes[recipe_name] = int(crafted_text) if crafted_text not in (None, "") else 0

            except (TypeError, ValueError):

                recipes[recipe_name] = 0

        return recipes

    def set_recipe_status(self, recipe_name, crafted_count):

        recipes_elem = self._get_elem(create=True)

        existing_item = None

        for item in recipes_elem.findall("item"):

            if item.findtext("key/string") == recipe_name:

                existing_item = item

                break

        if crafted_count is None:

            if existing_item is not None:

                recipes_elem.remove(existing_item)

            return

        try:

            crafted_value = int(crafted_count)

        except (TypeError, ValueError):

            crafted_value = 0

        if existing_item is None:

            existing_item = ET.SubElement(recipes_elem, "item")

            key_elem = ET.SubElement(existing_item, "key")

            ET.SubElement(key_elem, "string").text = recipe_name

            value_elem = ET.SubElement(existing_item, "value")

            ET.SubElement(value_elem, "int")

        value_int = existing_item.find("value/int")

        if value_int is None:

            value_elem = existing_item.find("value")

            if value_elem is None:

                value_elem = ET.SubElement(existing_item, "value")

            value_int = ET.SubElement(value_elem, "int")

        value_int.text = str(crafted_value)

# Define the farmer type used by this module.
# It reads or mutates the XML-backed save model used by the editor.
class Farmer(BaseProxy):

    def __init__(self, element: ET.Element):

        super().__init__(element)

        self._migrate_legacy_wallet_flags()

        self._inventory = Inventory(element)

        self._cooking_recipes = RecipeCollectionProxy(self, "cookingRecipes")

        self._crafting_recipes = RecipeCollectionProxy(self, "craftingRecipes")

    # Return the player's inventory.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def inventory(self):

        return self._inventory

    # Return the player's items.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def items(self):

        return self._inventory.all_items

    @property

    def cookingRecipes(self):

        return self._cooking_recipes

    @property

    def craftingRecipes(self):

        return self._crafting_recipes

    # Return the player's name.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def name(self): return self.get_text("name")

    # Update the player's name.
    # It reads or mutates the XML-backed save model used by the editor.
    @name.setter

    def name(self, value): self.set_text("name", value)

    # Return the player's money.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def money(self): return self.get_int("money")

    # Update the player's money.
    # It reads or mutates the XML-backed save model used by the editor.
    @money.setter

    def money(self, value):

        try:

            val = int(value)

            if val > 99999999:

                val = 99999999

            self.set_int("money", val)

        except (ValueError, TypeError):

            self.set_int("money", value)

    # Return the player's max health.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def maxHealth(self): return self.get_int("maxHealth")

    # Update the player's max health.
    # It reads or mutates the XML-backed save model used by the editor.
    @maxHealth.setter

    def maxHealth(self, value): self.set_int("maxHealth", value)

    # Return the player's max stamina.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def maxStamina(self): return self.get_int("maxStamina")

    # Update the player's max stamina.
    # It reads or mutates the XML-backed save model used by the editor.
    @maxStamina.setter

    def maxStamina(self, value): self.set_int("maxStamina", value)

    # Return the player's gender.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def gender(self):

        val = self.get_text("gender", None)

        if val is None or val == "":

            val = self.get_text("Gender", "0")

        if val in ["0", "Male"]:

            return "0"

        return "1"

    # Return the player's gender.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def Gender(self):

        val = self.get_text("Gender", None)

        if val is None or val == "":

            val = self.get_text("gender", "Male")

        if val in ["0", "Male"]:

            return "Male"

        return "Female"

    # Update the player's gender.
    # It reads or mutates the XML-backed save model used by the editor.
    @gender.setter

    def gender(self, value):

        str_val = str(value)

        self.set_text("gender", str_val)

        gender_str = "Male" if str_val == "0" else "Female"

        self.set_text("Gender", gender_str)

        is_male = "true" if str_val == "0" else "false"

        self.set_text("isMale", is_male)

    # Return the player's max items.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def maxItems(self): return self.get_int("maxItems", 36)

    # Update the player's max items.
    # It reads or mutates the XML-backed save model used by the editor.
    @maxItems.setter

    def maxItems(self, value): self.set_int("maxItems", value)

    # Return the player's farm name.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def farmName(self): return self.get_text("farmName")

    # Update the player's farm name.
    # It reads or mutates the XML-backed save model used by the editor.
    @farmName.setter

    def farmName(self, value): self.set_text("farmName", value)

    # Return the player's health.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def health(self): return self.get_int("health")

    # Update the player's health.
    # It reads or mutates the XML-backed save model used by the editor.
    @health.setter

    def health(self, value): self.set_int("health", value)

    # Return the player's stamina.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def stamina(self): return self.get_int("stamina")

    # Update the player's stamina.
    # It reads or mutates the XML-backed save model used by the editor.
    @stamina.setter

    def stamina(self, value): self.set_int("stamina", value)

    # Return the player's club coins.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def clubCoins(self): return self.get_int("clubCoins")

    # Update the player's club coins.
    # It reads or mutates the XML-backed save model used by the editor.
    @clubCoins.setter

    def clubCoins(self, value): self.set_int("clubCoins", value)

    # Return the player's qi gems.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def qiGems(self): return self.get_int("qiGems")

    # Update the player's qi gems.
    # It reads or mutates the XML-backed save model used by the editor.
    @qiGems.setter

    def qiGems(self, value): self.set_int("qiGems", value)

    # Return the player's mastery exp.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def masteryExp(self): return self.get_int("masteryExp")

    # Update the player's mastery exp.
    # It reads or mutates the XML-backed save model used by the editor.
    @masteryExp.setter

    def masteryExp(self, value): self.set_int("masteryExp", value)

    # Return the player's cat person.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def catPerson(self): return self.get_bool("catPerson")

    # Update the player's cat person.
    # It reads or mutates the XML-backed save model used by the editor.
    @catPerson.setter

    def catPerson(self, value):

        self.set_bool("catPerson", value)

        self.set_bool("isCat", value)

    # Return the player's pet type.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def petType(self): return self.get_text("petType")

    # Update the player's pet type.
    # It reads or mutates the XML-backed save model used by the editor.
    @petType.setter

    def petType(self, value): self.set_text("petType", value)

    # Return the player's which pet breed.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def whichPetBreed(self): return self.get_int("whichPetBreed")

    # Update the player's which pet breed.
    # It reads or mutates the XML-backed save model used by the editor.
    @whichPetBreed.setter

    def whichPetBreed(self, value): self.set_int("whichPetBreed", value)

    # Return the player's total money earned.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def totalMoneyEarned(self): return self.get_int("totalMoneyEarned")

    # Update the player's total money earned.
    # It reads or mutates the XML-backed save model used by the editor.
    @totalMoneyEarned.setter

    def totalMoneyEarned(self, value): self.set_int("totalMoneyEarned", value)

    # Return the player's deepest mine level.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def deepestMineLevel(self): return self.get_int("deepestMineLevel")

    # Update the player's deepest mine level.
    # It reads or mutates the XML-backed save model used by the editor.
    @deepestMineLevel.setter

    def deepestMineLevel(self, value): self.set_int("deepestMineLevel", value)

    # Return the player's times reached mine bottom.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def timesReachedMineBottom(self): return self.get_int("timesReachedMineBottom")

    # Update the player's times reached mine bottom.
    # It reads or mutates the XML-backed save model used by the editor.
    @timesReachedMineBottom.setter

    def timesReachedMineBottom(self, value): self.set_int("timesReachedMineBottom", value)

    # Return the player's trash can level.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def trashCanLevel(self): return self.get_int("trashCanLevel")

    # Update the player's trash can level.
    # It reads or mutates the XML-backed save model used by the editor.
    @trashCanLevel.setter

    def trashCanLevel(self, value): self.set_int("trashCanLevel", value)

    # Return the player's luck level.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def luckLevel(self): return self.get_int("luckLevel")

    # Update the player's luck level.
    # It reads or mutates the XML-backed save model used by the editor.
    @luckLevel.setter

    def luckLevel(self, value): self.set_int("luckLevel", value)

    # Return the player's house upgrade level.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def houseUpgradeLevel(self): return self.get_int("houseUpgradeLevel")

    # Update the player's house upgrade level.
    # It reads or mutates the XML-backed save model used by the editor.
    @houseUpgradeLevel.setter

    def houseUpgradeLevel(self, value):

        try:

            val = int(value)

            if val > 3:

                val = 3

            self.set_int("houseUpgradeLevel", val)

        except (ValueError, TypeError):

            self.set_int("houseUpgradeLevel", value)

    # Return the player's days until house upgrade.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def daysUntilHouseUpgrade(self): return self.get_int("daysUntilHouseUpgrade")

    # Update the player's days until house upgrade.
    # It reads or mutates the XML-backed save model used by the editor.
    @daysUntilHouseUpgrade.setter

    def daysUntilHouseUpgrade(self, value): self.set_int("daysUntilHouseUpgrade", value)

    # Return the player's magnetic radius.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def magneticRadius(self): return self.get_int("magneticRadius")

    # Update the player's magnetic radius.
    # It reads or mutates the XML-backed save model used by the editor.
    @magneticRadius.setter

    def magneticRadius(self, value): self.set_int("magneticRadius", value)

    # Return the player's resilience.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def resilience(self): return self.get_int("resilience")

    # Update the player's resilience.
    # It reads or mutates the XML-backed save model used by the editor.
    @resilience.setter

    def resilience(self, value): self.set_int("resilience", value)

    # Return the player's immunity.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def immunity(self): return self.get_int("immunity")

    # Update the player's immunity.
    # It reads or mutates the XML-backed save model used by the editor.
    @immunity.setter

    def immunity(self, value): self.set_int("immunity", value)

    # Return the player's farming level.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def farmingLevel(self): return self.get_int("farmingLevel")

    # Update the player's farming level.
    # It reads or mutates the XML-backed save model used by the editor.
    @farmingLevel.setter

    def farmingLevel(self, value): self.set_int("farmingLevel", value)

    # Return the player's mining level.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def miningLevel(self): return self.get_int("miningLevel")

    # Update the player's mining level.
    # It reads or mutates the XML-backed save model used by the editor.
    @miningLevel.setter

    def miningLevel(self, value): self.set_int("miningLevel", value)

    # Return the player's foraging level.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def foragingLevel(self): return self.get_int("foragingLevel")

    # Update the player's foraging level.
    # It reads or mutates the XML-backed save model used by the editor.
    @foragingLevel.setter

    def foragingLevel(self, value): self.set_int("foragingLevel", value)

    # Return the player's fishing level.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def fishingLevel(self): return self.get_int("fishingLevel")

    # Update the player's fishing level.
    # It reads or mutates the XML-backed save model used by the editor.
    @fishingLevel.setter

    def fishingLevel(self, value): self.set_int("fishingLevel", value)

    # Return the player's combat level.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def combatLevel(self): return self.get_int("combatLevel")

    # Update the player's combat level.
    # It reads or mutates the XML-backed save model used by the editor.
    @combatLevel.setter

    def combatLevel(self, value): self.set_int("combatLevel", value)

    # Return the player's favorite thing.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def favoriteThing(self): return self.get_text("favoriteThing")

    # Update the player's favorite thing.
    # It reads or mutates the XML-backed save model used by the editor.
    @favoriteThing.setter

    def favoriteThing(self, value): self.set_text("favoriteThing", value)

    # Return the player's attack.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def attack(self): return self.get_int("attack")

    # Update the player's attack.
    # It reads or mutates the XML-backed save model used by the editor.
    @attack.setter

    def attack(self, value): self.set_int("attack", value)

    # Return the player's hair.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def hair(self): return self.get_int("hair")

    # Update the player's hair.
    # It reads or mutates the XML-backed save model used by the editor.
    @hair.setter

    def hair(self, value): self.set_int("hair", value)

    # Return the player's hairstyle.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def hairstyle(self):

        val = self.get_int("hair")

        if val >= 100:

            return val - 100 + 56

        return val

    # Update the player's hairstyle.
    # It reads or mutates the XML-backed save model used by the editor.
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

    # Return the player's shirt.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def shirt(self): return self.get_int("shirt")

    # Update the player's shirt.
    # It reads or mutates the XML-backed save model used by the editor.
    @shirt.setter

    def shirt(self, value): self.set_int("shirt", value)

    # Return the player's skin.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def skin(self): return self.get_int("skin")

    # Update the player's skin.
    # It reads or mutates the XML-backed save model used by the editor.
    @skin.setter

    def skin(self, value): self.set_int("skin", value)

    # Return the player's accessory.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def accessory(self): return self.get_int("accessory")

    # Update the player's accessory.
    # It reads or mutates the XML-backed save model used by the editor.
    @accessory.setter

    def accessory(self, value): self.set_int("accessory", value)

    # Return the player's shoes.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def shoes(self): return self.get_int("shoes")

    # Update the player's shoes.
    # It reads or mutates the XML-backed save model used by the editor.
    @shoes.setter

    def shoes(self, value): self.set_int("shoes", value)

    # Return the player's facial hair.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def facialHair(self): return self.get_int("facialHair")

    # Update the player's facial hair.
    # It reads or mutates the XML-backed save model used by the editor.
    @facialHair.setter

    def facialHair(self, value): self.set_int("facialHair", value)

    # Return the player's pants.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def pants(self): return self.get_int("pants")

    # Update the player's pants.
    # It reads or mutates the XML-backed save model used by the editor.
    @pants.setter

    def pants(self, value): self.set_int("pants", value)

    # Return the player's unique ID.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def uniqueID(self): return self.get_text("UniqueMultiplayerID")

    # Return the color.
    # It reads or mutates the XML-backed save model used by the editor.
    def get_color(self, tag):

        color_elem = self._element.find(tag)

        if color_elem is not None:

            r = int(color_elem.findtext("R", "0"))

            g = int(color_elem.findtext("G", "0"))

            b = int(color_elem.findtext("B", "0"))

            a = int(color_elem.findtext("A", "255"))

            return (r, g, b, a)

        return (0, 0, 0, 255)

    # Set the color.
    # It reads or mutates the XML-backed save model used by the editor.
    def set_color(self, tag, r, g, b, a=255):

        color_elem = self._element.find(tag)

        if color_elem is None:

            color_elem = ET.SubElement(self._element, tag)

        for name, val in [("R", r), ("G", g), ("B", b), ("A", a)]:

            elem = color_elem.find(name)

            if elem is None:

                elem = ET.SubElement(color_elem, name)

            elem.text = str(val)

        packed = (((a & 0xFF) << 24) | ((b & 0xFF) << 16) | ((g & 0xFF) << 8) | (r & 0xFF)) & 0xFFFFFFFF

        packed_elem = color_elem.find("PackedValue")

        if packed_elem is None:

            packed_elem = ET.SubElement(color_elem, "PackedValue")

        packed_elem.text = str(packed)

    # Return the player's hair color.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def hairColor(self): return self.get_color("hairstyleColor")

    # Update the player's hair color.
    # It reads or mutates the XML-backed save model used by the editor.
    @hairColor.setter

    def hairColor(self, rgba): self.set_color("hairstyleColor", *rgba)

    # Return the player's eye color.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def eyeColor(self): return self.get_color("newEyeColor")

    # Update the player's eye color.
    # It reads or mutates the XML-backed save model used by the editor.
    @eyeColor.setter

    def eyeColor(self, rgba): self.set_color("newEyeColor", *rgba)

    # Return the player's pants color.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def pantsColor(self): return self.get_color("pantsColor")

    # Update the player's pants color.
    # It reads or mutates the XML-backed save model used by the editor.
    @pantsColor.setter

    def pantsColor(self, rgba): self.set_color("pantsColor", *rgba)

    # Return the player's hat.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def hat(self):

        elem = self._element.find("hat")

        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None

    # Update the player's hat.
    # It reads or mutates the XML-backed save model used by the editor.
    @hat.setter

    def hat(self, value): self._set_equipment("hat", value)

    # Return the player's shirt item.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def shirtItem(self):

        elem = self._element.find("shirtItem")

        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None

    # Update the player's shirt item.
    # It reads or mutates the XML-backed save model used by the editor.
    @shirtItem.setter

    def shirtItem(self, value): self._set_equipment("shirtItem", value)

    # Return the player's pants item.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def pantsItem(self):

        elem = self._element.find("pantsItem")

        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None

    # Update the player's pants item.
    # It reads or mutates the XML-backed save model used by the editor.
    @pantsItem.setter

    def pantsItem(self, value): self._set_equipment("pantsItem", value)

    # Return the player's boots.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def boots(self):

        elem = self._element.find("boots")

        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None

    # Update the player's boots.
    # It reads or mutates the XML-backed save model used by the editor.
    @boots.setter

    def boots(self, value): self._set_equipment("boots", value)

    # Return the player's left ring.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def leftRing(self):

        elem = self._element.find("leftRing")

        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None

    # Update the player's left ring.
    # It reads or mutates the XML-backed save model used by the editor.
    @leftRing.setter

    def leftRing(self, value): self._set_equipment("leftRing", value)

    # Return the player's right ring.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def rightRing(self):

        elem = self._element.find("rightRing")

        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None

    # Update the player's right ring.
    # It reads or mutates the XML-backed save model used by the editor.
    @rightRing.setter

    def rightRing(self, value): self._set_equipment("rightRing", value)

    # Return the player's trinket item.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def trinketItem(self):

        elem = self._element.find("trinketItem")

        return Item(elem) if elem is not None and elem.get("{http://www.w3.org/2001/XMLSchema-instance}nil") != "true" else None

    # Update the player's trinket item.
    # It reads or mutates the XML-backed save model used by the editor.
    @trinketItem.setter

    def trinketItem(self, value): self._set_equipment("trinketItem", value)

    # Set the equipment.
    # It reads or mutates the XML-backed save model used by the editor.
    def _set_equipment(self, tag, value):

        if value is None or (isinstance(value, str) and (value == "" or value.lower() == "none")):

            elem = self._element.find(tag)

            if elem is not None:

                for child in list(elem): elem.remove(child)

                elem.set("{http://www.w3.org/2001/XMLSchema-instance}nil", "true")

            return

        if isinstance(value, Item):

            new_item = value

        else:

            new_item = Item.from_name(None, item_id=str(value))

        self._inventory.set_item(tag, new_item)

    # Return whether the mail value is available.
    # It reads or mutates the XML-backed save model used by the editor.
    def has_mail(self, mail_id):

        mail_elem = self._element.find("mailReceived")

        if mail_elem is not None:

            for s in mail_elem.findall("string"):

                if s.text == mail_id:

                    return True

        return False

    # Add a mail flag to the player record.
    # It reads or mutates the XML-backed save model used by the editor.
    def add_mail(self, mail_id):

        if self.has_mail(mail_id):

            return

        mail_elem = self._element.find("mailReceived")

        if mail_elem is None:

            mail_elem = ET.SubElement(self._element, "mailReceived")

        new_mail = ET.SubElement(mail_elem, "string")

        new_mail.text = mail_id

    # Remove the mail.
    # It reads or mutates the XML-backed save model used by the editor.
    def remove_mail(self, mail_id):

        mail_elem = self._element.find("mailReceived")

        if mail_elem is not None:

            for s in mail_elem.findall("string"):

                if s.text == mail_id:

                    mail_elem.remove(s)

    # Return whether the achievement value is available.
    # It reads or mutates the XML-backed save model used by the editor.
    def has_achievement(self, achievement_id):

        ach_elem = self._element.find("achievements")

        if ach_elem is not None:

            for i in ach_elem.findall("int"):

                if i.text == str(achievement_id):

                    return True

        return False

    # Add an achievement to the player record.
    # It reads or mutates the XML-backed save model used by the editor.
    def add_achievement(self, achievement_id):

        if self.has_achievement(achievement_id):

            return

        ach_elem = self._element.find("achievements")

        if ach_elem is None:

            ach_elem = ET.SubElement(self._element, "achievements")

        new_ach = ET.SubElement(ach_elem, "int")

        new_ach.text = str(achievement_id)

    # Remove the achievement.
    # It reads or mutates the XML-backed save model used by the editor.
    def remove_achievement(self, achievement_id):

        ach_elem = self._element.find("achievements")

        if ach_elem is not None:

            for i in ach_elem.findall("int"):

                if i.text == str(achievement_id):

                    ach_elem.remove(i)

    # Return the player's friendship data.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def friendshipData(self):

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

                    "element": f_elem

                })

        return data

    # Update the friendship.
    # It reads or mutates the XML-backed save model used by the editor.
    def update_friendship(self, name, points):

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

    XP_FOR_LEVEL = [0, 100, 380, 770, 1300, 2150, 3300, 4800, 6900, 10000, 15000]

    # Convert a skill XP value into the corresponding level.
    # It reads or mutates the XML-backed save model used by the editor.
    def xp_to_level(self, xp):

        level = 0

        for i, req in enumerate(self.XP_FOR_LEVEL):

            if xp < req:

                break

            level = i

        return level

    # Return the player's experience points.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def experiencePoints(self):

        xp_elem = self._element.find("experiencePoints")

        if xp_elem is not None:

            return [int(i.text) if i.text is not None else 0 for i in xp_elem.findall("int")]

        return [0, 0, 0, 0, 0, 0]

    # Set the experience.
    # It reads or mutates the XML-backed save model used by the editor.
    def set_experience(self, skill_index, xp):

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

        level = self.xp_to_level(val)

        skill_names = ["farmingLevel", "miningLevel", "foragingLevel", "fishingLevel", "combatLevel", "luckLevel"]

        if 0 <= skill_index < len(skill_names):

            self.set_int(skill_names[skill_index], level)

    # Return the player's professions list.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def professions_list(self):

        return self.get_professions()

    # Update the player's professions list.
    # It reads or mutates the XML-backed save model used by the editor.
    @professions_list.setter

    def professions_list(self, value):

        self.set_professions(value)

    # Add an item to the current collection.
    # It reads or mutates the XML-backed save model used by the editor.
    def add_item(self, name, item_id=None, stack=1, quality=0):

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

    # Remove the item.
    # It reads or mutates the XML-backed save model used by the editor.
    def remove_item(self, item_model):

        items_elem = self._element.find("items")

        if items_elem is None:

            return

        items = items_elem.findall("Item")

        for idx, elem in enumerate(items):

            if elem is item_model.raw:

                self._inventory.set_item(idx, None)

                return

    # Return the professions.
    # It reads or mutates the XML-backed save model used by the editor.
    def get_professions(self):

        prof_elem = self._element.find("professions")

        if prof_elem is not None:

            return [int(i.text) if i.text is not None else 0 for i in prof_elem.findall("int")]

        return []

    # Set the professions.
    # It reads or mutates the XML-backed save model used by the editor.
    def set_professions(self, profession_ids):

        prof_elem = self._element.find("professions")

        if prof_elem is not None:

            for child in list(prof_elem):

                prof_elem.remove(child)

            for pid in profession_ids:

                new_int = ET.SubElement(prof_elem, "int")

                new_int.text = str(pid)

    # Migrate legacy wallet flags into the current save representation.
    # It reads or mutates the XML-backed save model used by the editor.
    def _migrate_legacy_wallet_flags(self):

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

        received_list = [s.text for s in mail_received.findall("string")]

        for field, flag in wallet_flags.items():

            field_elem = self._element.find(field)

            if field_elem is not None:

                if field_elem.text and field_elem.text.lower() == "true":

                    if flag not in received_list:

                        new_s = ET.SubElement(mail_received, "string")

                        new_s.text = flag

                        received_list.append(flag)

                self._element.remove(field_elem)
