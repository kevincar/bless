import abc

from enum import Flag

from bleak.backends.characteristic import BleakGATTCharacteristic


class GattCharacteristicsFlags(Flag):
    broadcast = 0x0001
    read = 0x0002
    write_without_response = 0x0004
    write = 0x0008
    notify = 0x0010
    indicate = 0x0020
    authenticated_signed_writes = 0x0040
    extended_properties = 0x0080
    reliable_write = 0x0100
    writable_auxiliaries = 0x0200


class GATTAttributePermissions(Flag):
    readable = 0x1
    writeable = 0x2
    read_encryption_required = 0x4
    write_encryption_required = 0x8


class BlessGATTCharacteristic(BleakGATTCharacteristic):
    """
    Extension of the BleakGATTCharacteristic to allow for writeable values
    """

    @property  # type: ignore
    @abc.abstractmethod
    def value(self) -> bytearray:
        """Value of this characteristic"""
        raise NotImplementedError()

    @value.setter  # type: ignore
    @abc.abstractmethod
    def value(self, val: bytearray):
        """Set the value of this characteristic"""
        raise NotImplementedError
