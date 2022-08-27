from uuid import UUID
from typing import Union

from CoreBluetooth import CBMutableService, CBUUID  # type: ignore

from bleak.backends.corebluetooth.utils import cb_uuid_to_str  # type: ignore
from bleak.backends.corebluetooth.service import (  # type: ignore
    BleakGATTServiceCoreBluetooth
)

from bless.backends.service import BlessGATTService
from bless.backends.server import BaseBlessServer


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
        self.__handle = 0

    async def init(self, server: "BaseBlessServer"):
        """
        Initailize the CoreBluetooth Service object
        """
        service_uuid: CBUUID = CBUUID.alloc().initWithString_(self._uuid)
        cb_service: CBMutableService = CBMutableService.alloc().initWithType_primary_(
            service_uuid, True
        )

        # super(BlessGATTService, self).__init__(obj=cb_service)
        setattr(self, "_BleakGATTServiceCoreBluetooth__characteristics", [])
        self.obj = cb_service

    @property
    def handle(self) -> int:
        """The integer handle of this service"""
        return self.__handle

    @property
    def uuid(self) -> str:
        """UUID for this service."""
        return cb_uuid_to_str(self.obj.UUID())
