from enum import Flag

from bleak.backends.dotnet.characteristic import (
        BleakGATTCharacteristicDotNet
        )
<<<<<<< HEAD
        
=======

>>>>>>> dae35b78106faae3f3ad9eb31747bb6f8de5568d

class CBAttributePermissions(Flag):
    readable = 0x1
    writeable = 0x2
    read_encryption_required = 0x4
    write_encryption_required = 0x8


class BlessGATTCharacteristicDotNet(
        BleakGATTCharacteristicDotNet
        ):
    """
    DotNet implementation of the BlessGATTCharacteristic
    """

    def __init__(self):
        super().__init__()
        self._value: bytearray = bytearray(b'')

    @property
    def value(self) -> bytearray:
        """Get the value of the characteristic"""
        return self._value

    @value.setter
    def value(self, val: bytearray):
        """Set the value of the characteristic"""
        self._value = val
