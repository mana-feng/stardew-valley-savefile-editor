from models.base_proxy import BaseProxy
import xml.etree.ElementTree as ET

class FarmAnimal(BaseProxy):
    """
    农场动物代理类。
    """
    def __init__(self, element: ET.Element):
        super().__init__(element)
        # element 预期是一个 <item>，包含 <key><long>...</long></key> 和 <value><FarmAnimal>...</FarmAnimal></value>
        self.animal_elem = self._element.find("value/FarmAnimal")

    @property
    def name(self):
        if self.animal_elem is not None:
            return self.animal_elem.findtext("name", "")
        return ""

    @name.setter
    def name(self, value):
        if self.animal_elem is not None:
            name_elem = self.animal_elem.find("name")
            if name_elem is not None: name_elem.text = value
            display_elem = self.animal_elem.find("displayName")
            if display_elem is not None: display_elem.text = value

    @property
    def type(self):
        if self.animal_elem is not None:
            return self.animal_elem.findtext("type", "Unknown")
        return "Unknown"

    @type.setter
    def type(self, value):
        if self.animal_elem is not None:
            elem = self.animal_elem.find("type")
            if elem is not None: elem.text = value

    @property
    def gender(self):
        if self.animal_elem is not None:
            return self.animal_elem.findtext("Gender", "Female")
        return "Female"

    @gender.setter
    def gender(self, value):
        if self.animal_elem is not None:
            gender_elem = self.animal_elem.find("Gender")
            if gender_elem is not None: gender_elem.text = value

    @property
    def daysOwned(self):
        if self.animal_elem is not None:
            return self.safe_int(self.animal_elem.findtext("daysOwned", "0"))
        return 0

    @daysOwned.setter
    def daysOwned(self, value):
        if self.animal_elem is not None:
            days_elem = self.animal_elem.find("daysOwned")
            if days_elem is not None: days_elem.text = str(value)
            age_elem = self.animal_elem.find("age")
            if age_elem is not None: age_elem.text = str(value)

    @property
    def age(self):
        if self.animal_elem is not None:
            return self.safe_int(self.animal_elem.findtext("age", "0"))
        return 0

    @age.setter
    def age(self, value):
        if self.animal_elem is not None:
            age_elem = self.animal_elem.find("age")
            if age_elem is not None: age_elem.text = str(value)

    @property
    def friendship(self):
        if self.animal_elem is not None:
            return self.safe_int(self.animal_elem.findtext("friendshipTowardFarmer", "0"))
        return 0

    @friendship.setter
    def friendship(self, value):
        if self.animal_elem is not None:
            elem = self.animal_elem.find("friendshipTowardFarmer")
            if elem is not None: elem.text = str(value)

    @property
    def happiness(self):
        if self.animal_elem is not None:
            return self.safe_int(self.animal_elem.findtext("happiness", "0"))
        return 0

    @happiness.setter
    def happiness(self, value):
        if self.animal_elem is not None:
            happy_elem = self.animal_elem.find("happiness")
            if happy_elem is not None: happy_elem.text = str(value)

    @property
    def fullness(self):
        if self.animal_elem is not None:
            return int(self.animal_elem.findtext("fullness", "0"))
        return 0

    @fullness.setter
    def fullness(self, value):
        if self.animal_elem is not None:
            elem = self.animal_elem.find("fullness")
            if elem is not None: elem.text = str(value)

    @property
    def allowReproduction(self):
        if self.animal_elem is not None:
            return self.animal_elem.findtext("allowReproduction", "true").lower() == "true"
        return True

    @allowReproduction.setter
    def allowReproduction(self, value):
        if self.animal_elem is not None:
            elem = self.animal_elem.find("allowReproduction")
            if elem is not None: elem.text = "true" if value else "false"

    @property
    def hasEatenAnimalCracker(self):
        if self.animal_elem is not None:
            return self.animal_elem.findtext("hasEatenAnimalCracker", "false").lower() == "true"
        return False

    @hasEatenAnimalCracker.setter
    def hasEatenAnimalCracker(self, value):
        if self.animal_elem is not None:
            elem = self.animal_elem.find("hasEatenAnimalCracker")
            if elem is not None: elem.text = "true" if value else "false"

    @property
    def wasPet(self):
        if self.animal_elem is not None:
            return self.animal_elem.findtext("wasPet", "false").lower() == "true"
        return False

    @wasPet.setter
    def wasPet(self, value):
        if self.animal_elem is not None:
            elem = self.animal_elem.find("wasPet")
            if elem is not None: elem.text = "true" if value else "false"

    @property
    def buildingTypeILiveIn(self):
        if self.animal_elem is not None:
            return self.animal_elem.findtext("buildingTypeILiveIn", "")
        return ""

    @buildingTypeILiveIn.setter
    def buildingTypeILiveIn(self, value):
        if self.animal_elem is not None:
            elem = self.animal_elem.find("buildingTypeILiveIn")
            if elem is not None: elem.text = value

    @property
    def ownerID(self):
        if self.animal_elem is not None:
            return self.animal_elem.findtext("ownerID", "0")
        return "0"

    @ownerID.setter
    def ownerID(self, value):
        if self.animal_elem is not None:
            owner_elem = self.animal_elem.find("ownerID")
            if owner_elem is not None: owner_elem.text = str(value)

    @property
    def isEating(self):
        if self.animal_elem is not None:
            return self.animal_elem.findtext("isEating", "false").lower() == "true"
        return False

    @isEating.setter
    def isEating(self, value):
        if self.animal_elem is not None:
            elem = self.animal_elem.find("isEating")
            if elem is not None: elem.text = "true" if value else "false"

    @property
    def wasAutoPet(self):
        if self.animal_elem is not None:
            return self.animal_elem.findtext("wasAutoPet", "false").lower() == "true"
        return False

    @wasAutoPet.setter
    def wasAutoPet(self, value):
        if self.animal_elem is not None:
            elem = self.animal_elem.find("wasAutoPet")
            if elem is not None: elem.text = "true" if value else "false"
