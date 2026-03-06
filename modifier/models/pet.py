# Model pet records and the editable save fields associated with player pets.
from models.base_proxy import BaseProxy

import xml.etree.ElementTree as ET

# Define the pet type used by this module.
# It reads or mutates the XML-backed save model used by the editor.
class Pet(BaseProxy):

    def __init__(self, element: ET.Element):

        super().__init__(element)

    # Return the pet's name.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def name(self): return self.get_text("name")

    # Update the pet's name.
    # It reads or mutates the XML-backed save model used by the editor.
    @name.setter

    def name(self, value): self.set_text("name", value)

    # Return the pet's pet type.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def petType(self): return self.get_text("petType")

    # Update the pet's pet type.
    # It reads or mutates the XML-backed save model used by the editor.
    @petType.setter

    def petType(self, value): self.set_text("petType", value)

    # Return the pet's which breed.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def whichBreed(self): return self.get_int("whichBreed")

    # Update the pet's which breed.
    # It reads or mutates the XML-backed save model used by the editor.
    @whichBreed.setter

    def whichBreed(self, value): self.set_int("whichBreed", value)

    # Return the pet's friendship toward farmer.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def friendshipTowardFarmer(self): return self.get_int("friendshipTowardFarmer")

    # Update the pet's friendship toward farmer.
    # It reads or mutates the XML-backed save model used by the editor.
    @friendshipTowardFarmer.setter

    def friendshipTowardFarmer(self, value): self.set_int("friendshipTowardFarmer", value)

    # Return the pet's times pet.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def timesPet(self): return self.get_int("timesPet")

    # Update the pet's times pet.
    # It reads or mutates the XML-backed save model used by the editor.
    @timesPet.setter

    def timesPet(self, value): self.set_int("timesPet", value)

    # Return the pet's is sleeping on farmer bed.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def isSleepingOnFarmerBed(self): return self.get_bool("isSleepingOnFarmerBed")

    # Update the pet's is sleeping on farmer bed.
    # It reads or mutates the XML-backed save model used by the editor.
    @isSleepingOnFarmerBed.setter

    def isSleepingOnFarmerBed(self, value): self.set_bool("isSleepingOnFarmerBed", value)

    # Return the pet's granted friendship for pet.
    # It reads or mutates the XML-backed save model used by the editor.
    @property

    def grantedFriendshipForPet(self): return self.get_bool("grantedFriendshipForPet")

    # Update the pet's granted friendship for pet.
    # It reads or mutates the XML-backed save model used by the editor.
    @grantedFriendshipForPet.setter

    def grantedFriendshipForPet(self, value): self.set_bool("grantedFriendshipForPet", value)
