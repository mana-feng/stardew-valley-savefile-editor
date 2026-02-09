from models.base_proxy import BaseProxy
import xml.etree.ElementTree as ET

class Pet(BaseProxy):
    """
    宠物模型类。
    """
    def __init__(self, element: ET.Element):
        super().__init__(element)

    @property
    def name(self): return self.get_text("name")
    @name.setter
    def name(self, value): self.set_text("name", value)

    @property
    def petType(self): return self.get_text("petType")
    @petType.setter
    def petType(self, value): self.set_text("petType", value)

    @property
    def whichBreed(self): return self.get_int("whichBreed")
    @whichBreed.setter
    def whichBreed(self, value): self.set_int("whichBreed", value)

    @property
    def friendshipTowardFarmer(self): return self.get_int("friendshipTowardFarmer")
    @friendshipTowardFarmer.setter
    def friendshipTowardFarmer(self, value): self.set_int("friendshipTowardFarmer", value)

    @property
    def timesPet(self): return self.get_int("timesPet")
    @timesPet.setter
    def timesPet(self, value): self.set_int("timesPet", value)

    @property
    def isSleepingOnFarmerBed(self): return self.get_bool("isSleepingOnFarmerBed")
    @isSleepingOnFarmerBed.setter
    def isSleepingOnFarmerBed(self, value): self.set_bool("isSleepingOnFarmerBed", value)

    @property
    def grantedFriendshipForPet(self): return self.get_bool("grantedFriendshipForPet")
    @grantedFriendshipForPet.setter
    def grantedFriendshipForPet(self, value): self.set_bool("grantedFriendshipForPet", value)
