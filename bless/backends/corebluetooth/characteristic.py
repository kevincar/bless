from enum import Flag
from typing import Union, Optional
from uuid import UUID

from CoreBluetooth import (
        CBMutableCharacteristic,
        CBUUID
        )  # type: ignore

from bleak.backends.corebluetooth.characteristic import (  # type: ignore
    BleakGATTCharacteristicCoreBluetooth,
)

from bleak.backends.characteristic import BleakGATTCharacteristic  # type: ignore

from bless.backends.characteristic import GattCharacteristicsFlags


class CBAttributePermissions(Flag):
    readable = 0x1
    writeable = 0x2
    read_encryption_required = 0x4
    write_encryption_required = 0x8


class BlessGATTCharacteristicCoreBluetooth(BleakGATTCharacteristicCoreBluetooth):
    """
    CoreBluetooth implementation of the BlessGATTCharacteristic
    """

    @classmethod
    def new(
            cls,
            uuid: Union[str, UUID],
            properties: GattCharacteristicsFlags,
            value: Optional[bytearray],
            permissions: int
            ) -> BleakGATTCharacteristic:
        """
        Create a new characteristic in place

        Parameters
        ----------
        uuid : Union[str, UUID]
            A string representation or a UUID for the unique identifier of the
            characteristic to create
        properties : GattCharacteristicsFlags
            The characteristic that define the properties for the characteristic
        value : Optional[bytearray]
            The value of the characteristic
        permissions : int
            An integer value that defines the permissions for the characteristic

        Returns
        -------
        BlessGATTCharacteristic
            The new characteristic
        """
        uuid = str(uuid)
        cb_uuid: CBUUID = CBUUID.alloc().initWithString_(uuid)
        cb_characteristic: CBMutableCharacteristic = (
            CBMutableCharacteristic.alloc().initWithType_properties_value_permissions_(
                cb_uuid, properties, value, permissions
            )
        )
        bless_characteristic: BlessGATTCharacteristicCoreBluetooth = (
            BlessGATTCharacteristicCoreBluetooth(obj=cb_characteristic)
        )
        return bless_characteristic

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
