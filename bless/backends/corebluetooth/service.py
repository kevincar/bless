from typing import List, Union
from uuid import UUID
from bleak.backends.corebluetooth.utils import cb_uuid_to_str  # type: ignore

from CoreBluetooth import (  # type: ignore
        CBMutableService,
        CBUUID
        )

from bless.backends.corebluetooth.characteristic import (
    BlessGATTCharacteristicCoreBluetooth,
)

from bleak.backends.service import BleakGATTService  # type: ignore


class BlessGATTServiceCoreBluetooth(BleakGATTService):
    """
    GATT Characteristic implementation for the CoreBluetooth backend
    """

    def __init__(self, obj: CBMutableService):
        super().__init__(obj)
        self.__characteristics: List[BlessGATTCharacteristicCoreBluetooth] = []
        self.__handle = 0

    @classmethod
    def new(cls, uuid: Union[str, UUID]) -> BleakGATTService:
        """
        Create a new service in place

        Parameters
        ----------
        uuid : Union[str | UUID]
            A string representation or a UUID for the unique identifier of the
            service to create

        Returns
        -------
        BlessGATTService
            The new service
        """
        uuid = str(uuid)
        service_uuid: CBUUID = CBUUID.alloc().initWithString_(uuid)
        cb_service: CBMutableService = CBMutableService.alloc().initWithType_primary_(
            service_uuid, True
        )

        bless_service: BlessGATTServiceCoreBluetooth = BlessGATTServiceCoreBluetooth(
            obj=cb_service
        )

        return bless_service

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
