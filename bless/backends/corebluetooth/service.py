from uuid import UUID
from typing import List, Union

from CoreBluetooth import CBMutableService, CBUUID  # type: ignore

from bleak.backends.corebluetooth.utils import cb_uuid_to_str  # type: ignore
from bless.backends.corebluetooth.characteristic import (
    BlessGATTCharacteristicCoreBluetooth,
)
from bleak.backends.corebluetooth.service import (  # type: ignore
        BleakGATTServiceCoreBluetooth
        )

from bless.backends.service import BlessGATTService


class BlessGATTServiceCoreBluetooth(BlessGATTService, BleakGATTServiceCoreBluetooth):
    """
    GATT Characteristic implementation for the CoreBluetooth backend
    """

    def __init__(self, uuid: Union[str, UUID]):
        """
        New Bless Service for macOS

        Parameters
        ----------
        uuid: Union[str, UUID]
            The uuid to assign to the service
        """
        super(BlessGATTServiceCoreBluetooth, self).__init__(uuid)
        self.__characteristics: List[BlessGATTCharacteristicCoreBluetooth] = []
        self.__handle = 0

    async def init(self):
        """
        Initailize the CoreBluetooth Service object
        """
        service_uuid: CBUUID = CBUUID.alloc().initWithString_(self._uuid)
        cb_service: CBMutableService = CBMutableService.alloc().initWithType_primary_(
            service_uuid, True
        )

        # Cannot call this because of handle issue
        # super(BlessGATTService, self).__init__(obj=cb_service)
        self.obj = cb_service

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
