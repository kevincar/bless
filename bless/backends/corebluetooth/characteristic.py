from enum import Flag
from uuid import UUID
from typing import Union, Optional, Dict

from CoreBluetooth import CBUUID, CBMutableCharacteristic  # type: ignore

from bleak.backends.characteristic import (  # type: ignore
    BleakGATTCharacteristic,
)
from bleak.backends.descriptor import BleakGATTDescriptor  # type: ignore

from bless.backends.service import BlessGATTService

from bless.backends.characteristic import (
    GATTCharacteristicProperties,
    GATTAttributePermissions,
    BlessGATTCharacteristic as BaseBlessGATTCharacteristic,
)


class CBAttributePermissions(Flag):
    readable = 0x1
    writeable = 0x2
    read_encryption_required = 0x4
    write_encryption_required = 0x8


class BlessGATTCharacteristicCoreBluetooth(
    BaseBlessGATTCharacteristic, BleakGATTCharacteristic
):
    """
    CoreBluetooth implementation of the BlessGATTCharacteristic
    """

    def __init__(
        self,
        uuid: Union[str, UUID],
        properties: GATTCharacteristicProperties,
        permissions: GATTAttributePermissions,
        value: Optional[bytearray],
    ):
        """
        Instantiates a new GATT Characteristic but is not yet assigned to any
        service or application

        Parameters
        ----------
        uuid : Union[str, UUID]
            The string representation of the universal unique identifier for
            the characteristic or the actual UUID object
        properties : GATTCharacteristicProperties
            The properties that define the characteristics behavior
        permissions : GATTAttributePermissions
            Permissions that define the protection levels of the properties
        value : Optional[bytearray]
            The binary value of the characteristic
        """
        BaseBlessGATTCharacteristic.__init__(self, uuid, properties, permissions, value)
        self._descriptors: Dict[int, BleakGATTDescriptor] = {}
        self._cb_characteristic: Optional[CBMutableCharacteristic] = None

    async def init(self, service: BlessGATTService):
        """
        Initializes the backend-specific characteristic object and stores it in
        self.obj
        """
        properties_value: int = self._properties_flags.value
        permissions_value: int = self._permissions.value

        cb_uuid: CBUUID = CBUUID.alloc().initWithString_(self._uuid)
        cb_characteristic: (
            CBMutableCharacteristic
        ) = CBMutableCharacteristic.alloc().initWithType_properties_value_permissions_(
            cb_uuid, properties_value, self._initial_value, permissions_value
        )

        # Store the CoreBluetooth characteristic
        self._cb_characteristic = cb_characteristic
        self.obj = cb_characteristic
        self._service_uuid = service.uuid
        self._handle = 0
        self._max_write_without_response_size = lambda: 512

    @property
    def service_uuid(self) -> str:
        """The UUID of the service this characteristic belongs to"""
        return self._service_uuid

    @property
    def service_handle(self) -> int:
        """The handle of the service this characteristic belongs to"""
        return 0

    @property
    def handle(self) -> int:
        """The handle of this characteristic"""
        return self._handle

    @property
    def uuid(self) -> str:
        """The uuid of this characteristic"""
        return self._uuid

    @property
    def description(self) -> str:
        """Description of this characteristic"""
        return f"Characteristic {self._uuid}"

    @property
    def value(self) -> bytearray:
        """Get the value of the characteristic"""
        if self._cb_characteristic is not None:
            cb_char: CBMutableCharacteristic = self._cb_characteristic
            return bytearray(cb_char.value()) if cb_char.value() else bytearray()
        return bytearray()

    @value.setter
    def value(self, val: bytearray):
        """Set the value of the characteristic"""
        if self._cb_characteristic is not None:
            cb_char: CBMutableCharacteristic = self._cb_characteristic
            cb_char.setValue_(val)
