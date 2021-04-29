from typing import List

from Windows.Devices.Bluetooth.GenericAttributeProfile import GattLocalCharacteristic

from bleak.backends.service import BleakGATTService

from bless.backends.dotnet.characteristic import BlessGATTCharacteristicDotNet


class BlessGATTServiceDotNet(BleakGATTService):
    """
    GATT Characteristic implementation for the DotNet backend
    """

    def __init__(self, obj: GattLocalCharacteristic):
        super().__init__(obj)
        self.__characteristics: List[BlessGATTCharacteristicDotNet] = []
        self.__handle = 0

    @property
    def handle(self) -> int:
        """The integer handle of the service"""
        return self.__handle

    @property
    def uuid(self) -> str:
        """UUID for this service"""
        return self.obj.Uuid.ToString()

    @property
    def characteristics(self) -> List[BlessGATTCharacteristicDotNet]:
        """List of characteristics for this service"""
        return self.__characteristics

    def add_characteristic(self, characteristic: BlessGATTCharacteristicDotNet):
        """
        Should not be used by end user, but rather by `bleak` itself.
        """
        self.__characteristics.append(characteristic)
