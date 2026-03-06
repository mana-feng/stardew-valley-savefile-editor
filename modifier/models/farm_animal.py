# Model farm animal records and derived helpers used by the editor UI.
from models.base_proxy import BaseProxy

import xml.etree.ElementTree as ET

# Define the farm animal type used by this module.
# It reads or mutates the XML-backed save model used by the editor.
class FarmAnimal(BaseProxy):

    def __init__(self, element: ET.Element):

        super().__init__(element)

        self.animal_elem = self._element.find("value/FarmAnimal")

    # Return the animal's name.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def name(self):

        if self.animal_elem is not None:

            return self.animal_elem.findtext("name", "")

        return ""

    # Update the animal's name.
    # It reads or mutates the XML-backed save model used by the editor.
    @name.setter

    def name(self, value):

        if self.animal_elem is not None:

            name_elem = self.animal_elem.find("name")

            if name_elem is not None: name_elem.text = value

            display_elem = self.animal_elem.find("displayName")

            if display_elem is not None: display_elem.text = value

    # Return the animal's type.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def type(self):

        if self.animal_elem is not None:

            return self.animal_elem.findtext("type", "Unknown")

        return "Unknown"

    # Update the animal's type.
    # It reads or mutates the XML-backed save model used by the editor.
    @type.setter

    def type(self, value):

        if self.animal_elem is not None:

            elem = self.animal_elem.find("type")

            if elem is not None: elem.text = value

    # Return the animal's gender.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def gender(self):

        if self.animal_elem is not None:

            return self.animal_elem.findtext("Gender", "Female")

        return "Female"

    # Update the animal's gender.
    # It reads or mutates the XML-backed save model used by the editor.
    @gender.setter

    def gender(self, value):

        if self.animal_elem is not None:

            gender_elem = self.animal_elem.find("Gender")

            if gender_elem is not None: gender_elem.text = value

    # Return the animal's days owned.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def daysOwned(self):

        if self.animal_elem is not None:

            return self.safe_int(self.animal_elem.findtext("daysOwned", "0"))

        return 0

    # Update the animal's days owned.
    # It reads or mutates the XML-backed save model used by the editor.
    @daysOwned.setter

    def daysOwned(self, value):

        if self.animal_elem is not None:

            days_elem = self.animal_elem.find("daysOwned")

            if days_elem is not None: days_elem.text = str(value)

            age_elem = self.animal_elem.find("age")

            if age_elem is not None: age_elem.text = str(value)

    # Return the animal's age.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def age(self):

        if self.animal_elem is not None:

            return self.safe_int(self.animal_elem.findtext("age", "0"))

        return 0

    # Update the animal's age.
    # It reads or mutates the XML-backed save model used by the editor.
    @age.setter

    def age(self, value):

        if self.animal_elem is not None:

            age_elem = self.animal_elem.find("age")

            if age_elem is not None: age_elem.text = str(value)

    # Return the animal's friendship.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def friendship(self):

        if self.animal_elem is not None:

            return self.safe_int(self.animal_elem.findtext("friendshipTowardFarmer", "0"))

        return 0

    # Update the animal's friendship.
    # It reads or mutates the XML-backed save model used by the editor.
    @friendship.setter

    def friendship(self, value):

        if self.animal_elem is not None:

            elem = self.animal_elem.find("friendshipTowardFarmer")

            if elem is not None: elem.text = str(value)

    # Return the animal's happiness.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def happiness(self):

        if self.animal_elem is not None:

            return self.safe_int(self.animal_elem.findtext("happiness", "0"))

        return 0

    # Update the animal's happiness.
    # It reads or mutates the XML-backed save model used by the editor.
    @happiness.setter

    def happiness(self, value):

        if self.animal_elem is not None:

            happy_elem = self.animal_elem.find("happiness")

            if happy_elem is not None: happy_elem.text = str(value)

    # Return the animal's fullness.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def fullness(self):

        if self.animal_elem is not None:

            return int(self.animal_elem.findtext("fullness", "0"))

        return 0

    # Update the animal's fullness.
    # It reads or mutates the XML-backed save model used by the editor.
    @fullness.setter

    def fullness(self, value):

        if self.animal_elem is not None:

            elem = self.animal_elem.find("fullness")

            if elem is not None: elem.text = str(value)

    # Return the animal's allow reproduction.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def allowReproduction(self):

        if self.animal_elem is not None:

            return self.animal_elem.findtext("allowReproduction", "true").lower() == "true"

        return True

    # Update the animal's allow reproduction.
    # It reads or mutates the XML-backed save model used by the editor.
    @allowReproduction.setter

    def allowReproduction(self, value):

        if self.animal_elem is not None:

            elem = self.animal_elem.find("allowReproduction")

            if elem is not None: elem.text = "true" if value else "false"

    # Return the animal's has eaten animal cracker.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def hasEatenAnimalCracker(self):

        if self.animal_elem is not None:

            return self.animal_elem.findtext("hasEatenAnimalCracker", "false").lower() == "true"

        return False

    # Update the animal's has eaten animal cracker.
    # It reads or mutates the XML-backed save model used by the editor.
    @hasEatenAnimalCracker.setter

    def hasEatenAnimalCracker(self, value):

        if self.animal_elem is not None:

            elem = self.animal_elem.find("hasEatenAnimalCracker")

            if elem is not None: elem.text = "true" if value else "false"

    # Return the animal's was pet.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def wasPet(self):

        if self.animal_elem is not None:

            return self.animal_elem.findtext("wasPet", "false").lower() == "true"

        return False

    # Update the animal's was pet.
    # It reads or mutates the XML-backed save model used by the editor.
    @wasPet.setter

    def wasPet(self, value):

        if self.animal_elem is not None:

            elem = self.animal_elem.find("wasPet")

            if elem is not None: elem.text = "true" if value else "false"

    # Return the animal's building type i live in.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def buildingTypeILiveIn(self):

        if self.animal_elem is not None:

            return self.animal_elem.findtext("buildingTypeILiveIn", "")

        return ""

    # Update the animal's building type i live in.
    # It reads or mutates the XML-backed save model used by the editor.
    @buildingTypeILiveIn.setter

    def buildingTypeILiveIn(self, value):

        if self.animal_elem is not None:

            elem = self.animal_elem.find("buildingTypeILiveIn")

            if elem is not None: elem.text = value

    # Return the animal's owner ID.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def ownerID(self):

        if self.animal_elem is not None:

            return self.animal_elem.findtext("ownerID", "0")

        return "0"

    # Update the animal's owner ID.
    # It reads or mutates the XML-backed save model used by the editor.
    @ownerID.setter

    def ownerID(self, value):

        if self.animal_elem is not None:

            owner_elem = self.animal_elem.find("ownerID")

            if owner_elem is not None: owner_elem.text = str(value)

    # Return the animal's is eating.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def isEating(self):

        if self.animal_elem is not None:

            return self.animal_elem.findtext("isEating", "false").lower() == "true"

        return False

    # Update the animal's is eating.
    # It reads or mutates the XML-backed save model used by the editor.
    @isEating.setter

    def isEating(self, value):

        if self.animal_elem is not None:

            elem = self.animal_elem.find("isEating")

            if elem is not None: elem.text = "true" if value else "false"

    # Return the animal's was auto pet.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def wasAutoPet(self):

        if self.animal_elem is not None:

            return self.animal_elem.findtext("wasAutoPet", "false").lower() == "true"

        return False

    # Update the animal's was auto pet.
    # It reads or mutates the XML-backed save model used by the editor.
    @wasAutoPet.setter

    def wasAutoPet(self, value):

        if self.animal_elem is not None:

            elem = self.animal_elem.find("wasAutoPet")

            if elem is not None: elem.text = "true" if value else "false"
