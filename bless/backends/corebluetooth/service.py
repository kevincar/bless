from bleak.backends.corebluetooth.utils import cb_uuid_to_str
from typing import List

from CoreBluetooth import CBMutableService

from bless.backends.corebluetooth.characteristic import (
    BlessGATTCharacteristicCoreBluetooth,
)
from bleak.backends.service import BleakGATTService


class BlessGATTServiceCoreBluetooth(BleakGATTService):
    """
    GATT Characteristic implementation for the CoreBluetooth backend
    """

    def __init__(self, obj: CBMutableService):
        super().__init__(obj)
        self.__characteristics: List[BlessGATTCharacteristicCoreBluetooth] = []
        self.__handle = 0

    @property
    def handle(self) -> int:
        """The integer handle of this service"""
        return self.__handle

    @property
    def uuid(self) -> str:
        """UUID for this service."""
        return cb_uuid_to_str(self.obj.UUID())

    @property
    def characteristics(self) -> List[BlessGATTCharacteristicCoreBluetooth]:
        """List of characteristics for this service"""
        return self.__characteristics

    def add_characteristic(self, characteristic: BlessGATTCharacteristicCoreBluetooth):
        """
        Should not be used by end user, but rather by `bleak` itself.
        """
        self.__characteristics.append(characteristic)
