from enum import Flag
from uuid import UUID
from typing import Union, Optional

from CoreBluetooth import (  # type: ignore
        CBUUID,
        CBMutableCharacteristic
        )

from bleak.backends.corebluetooth.characteristic import (  # type: ignore
    BleakGATTCharacteristicCoreBluetooth,
)

from bless.backends.characteristic import (
        GATTCharacteristicProperties,
        GATTAttributePermissions,
        BlessGATTCharacteristic
        )


class CBAttributePermissions(Flag):
    readable = 0x1
    writeable = 0x2
    read_encryption_required = 0x4
    write_encryption_required = 0x8


class BlessGATTCharacteristicCoreBluetooth(
    BlessGATTCharacteristic, BleakGATTCharacteristicCoreBluetooth
):
    """
    CoreBluetooth implementation of the BlessGATTCharacteristic
    """

    def __init__(
        self,
        uuid: Union[str, UUID],
        properties: GATTCharacteristicProperties,
        permissions: GATTAttributePermissions,
        value: Optional[bytearray]
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
        super(BlessGATTCharacteristicCoreBluetooth, self).__init__(
            uuid, properties, permissions, value
        )

    async def init(self):
        """
        Initializes the backend-specific characteristic object and stores it in
        self.obj
        """
        properties_value: int = self._properties.value
        permissions_value: int = self._permissions.value

        cb_uuid: CBUUID = CBUUID.alloc().initWithString_(self._uuid)
        cb_characteristic: CBMutableCharacteristic = (
            CBMutableCharacteristic.alloc().initWithType_properties_value_permissions_(
                cb_uuid, properties_value, self._initial_value, permissions_value
            )
        )
        super(BlessGATTCharacteristic, self).__init__(obj=cb_characteristic)

    @property
    def value(self) -> bytearray:
        """Get the value of the characteristic"""
        cb_char: CBMutableCharacteristic = self.obj
        return cb_char.value()

    @value.setter
    def value(self, val: bytearray):
        """Set the value of the characteristic"""
        cb_char: CBMutableCharacteristic = self.obj
        cb_char.setValue_(val)
