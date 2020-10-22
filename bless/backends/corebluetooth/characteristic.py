from enum import Flag

from bleak.backends.corebluetooth.characteristic import (
        BleakGATTCharacteristicCoreBluetooth
        )

from CoreBluetooth import CBMutableCharacteristic


class CBAttributePermissions(Flag):
    readable = 0x1
    writeable = 0x2
    read_encryption_required = 0x4
    write_encryption_required = 0x8


class BlessGATTCharacteristicCoreBluetooth(
        BleakGATTCharacteristicCoreBluetooth
        ):
    """
    CoreBluetooth implementation of the BlessGATTCharacteristic
    """

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
