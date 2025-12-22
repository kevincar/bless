from CoreBluetooth import CBUUID, CBMutableDescriptor  # type: ignore

from bleak.backends.descriptor import (  # type: ignore
    BleakGATTDescriptor,
)

from bless.backends.descriptor import BlessGATTDescriptor
from bless.backends.attribute import GATTAttributePermissions
from bless.backends.descriptor import GATTDescriptorProperties
from bless.backends.characteristic import BlessGATTCharacteristic

from uuid import UUID
from typing import Union, Optional


class BlessGATTDescriptorCoreBluetooth(BlessGATTDescriptor, BleakGATTDescriptor):
    """
    CoreBluetooth implementation of a GATT Descriptor
    """

    def __init__(
        self,
        uuid: Union[str, UUID],
        properties: GATTDescriptorProperties,
        permissions: GATTAttributePermissions,
        value: Optional[bytearray],
    ):
        """
        Instantiates a new GATT Descriptor but is not yet assigned to any
        characteristic or application

        Parameters
        ----------
        uuid : Union[str, UUID]
            The string representation of the universal unique identifier for
            the descriptor or the actual UUID object
        properties : GATTDescriptorProperties
            The properties that define the descriptors behavior
        permissions : GATTAttributePermissions
            Permissions that define the protection levels of the properties
        value : Optional[bytearray]
            The binary value of the descriptor
        """
        super().__init__(uuid, properties, permissions, value)
        self.value = value if value is not None else bytearray()

    async def init(self, characteristic: BlessGATTCharacteristic):
        cb_uuid: CBUUID = CBUUID.alloc().initWithString_(self._uuid)
        cb_descriptor: CBMutableDescriptor = (
            CBMutableDescriptor.alloc().initWithType_value_(
                cb_uuid, self._initial_value
            )
        )

        # Store the CoreBluetooth descriptor
        self._cb_descriptor = cb_descriptor
        self.obj = cb_descriptor
        self._handle = 0
        characteristic.add_descriptor(self)

    @property
    def value(self) -> bytearray:
        """Get the value of the descriptor"""
        return self._value

    @value.setter
    def value(self, val: bytearray):
        """Set the value of the characteristic"""
        self._value = val

    @property
    def uuid(self) -> str:
        """The uuid of this characteristic"""
        return self.obj.get("UUID").value
