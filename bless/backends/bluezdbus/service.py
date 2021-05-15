from typing import List, Dict

from bleak.backends.bluezdbus.service import BleakGATTServiceBlueZDBus
from bless.backends.bluezdbus.characteristic import BlessGATTCharacteristicBlueZDBus
from bless.backends.bluezdbus.dbus.service import BlueZGattService


class BlessGATTServiceBlueZDBus(BleakGATTServiceBlueZDBus):
    """"
    GATT service implementation for the BlueZ backend
    """

    def __init__(self, obj: Dict, path: str, gatt: BlueZGattService):
        super().__init__(obj, path)
        self.__characteristics: List[BlessGATTCharacteristicBlueZDBus] = []
        self.__path = path
        self.__handle = 0
        self.gatt = gatt

    @property
    def handle(self) -> int:
        """The integer handle of the service"""
        return self.__handle

    @property
    def uuid(self) -> str:
        """UUID for this service"""
        return self.obj["UUID"]

    @property
    def characteristics(self) -> List[BlessGATTCharacteristicBlueZDBus]:
        """List of characteristics for this service"""
        return self.__characteristics

    def add_characteristic(self, characteristic: BlessGATTCharacteristicBlueZDBus):
        """
        Should not be used by end user, but rather by `bleak` itself.
        """
        self.__characteristics.append(characteristic)

    @property
    def path(self):
        return self.__path
