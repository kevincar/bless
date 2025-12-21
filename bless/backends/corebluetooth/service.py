from uuid import UUID
from typing import Union, List, Dict

from CoreBluetooth import CBMutableService, CBUUID  # type: ignore

from bleak.backends.characteristic import BleakGATTCharacteristic  # type: ignore
from bleak.backends.service import BleakGATTService  # type: ignore

from bless.backends.service import BlessGATTService as BaseBlessGATTService
from bless.backends.server import BaseBlessServer


class BlessGATTServiceCoreBluetooth(BaseBlessGATTService, BleakGATTService):
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
        BaseBlessGATTService.__init__(self, uuid)
        self.__handle = 0
        self.__characteristics: List[BleakGATTCharacteristic] = []
        self._characteristics: Dict[int, BleakGATTCharacteristic] = (
            {}
        )  # For Bleak compatibility
        self._cb_service = None

    async def init(self, server: "BaseBlessServer"):
        """
        Initailize the CoreBluetooth Service object
        """
        service_uuid: CBUUID = CBUUID.alloc().initWithString_(self._uuid)
        cb_service: CBMutableService = CBMutableService.alloc().initWithType_primary_(
            service_uuid, True
        )

        # Store the CoreBluetooth service
        self._cb_service = cb_service
        self.obj = cb_service
        self._handle = 0

    @property
    def handle(self) -> int:
        """The integer handle of this service"""
        return self.__handle

    @property
    def uuid(self) -> str:
        """UUID for this service."""
        if self._cb_service is not None:
            return self._cb_service.UUID().UUIDString().lower()
        return self._uuid

    @property
    def description(self) -> str:
        """Description of this service"""
        return f"Service {self.uuid}"

    @property
    def characteristics(self) -> List[BleakGATTCharacteristic]:
        """List of characteristics for this service"""
        return self.__characteristics

    def add_characteristic(self, characteristic: BleakGATTCharacteristic):
        """Add a characteristic to this service"""
        self.__characteristics.append(characteristic)
        # Also add to the dict for Bleak compatibility
        handle = len(self._characteristics)
        self._characteristics[handle] = characteristic

    def get_characteristic(self, uuid: Union[str, UUID]):
        """Get a characteristic by UUID"""
        uuid_str = str(uuid) if isinstance(uuid, UUID) else uuid
        for char in self.__characteristics:
            if char.uuid == uuid_str:
                return char
        return None
