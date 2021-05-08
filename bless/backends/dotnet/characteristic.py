from bleak.backends.dotnet.characteristic import (  # type: ignore
    BleakGATTCharacteristicDotNet,
)

from Windows.Devices.Bluetooth.GenericAttributeProfile import (  # type: ignore
    GattProtectionLevel
)

from bless.backends.characteristic import GATTAttributePermissions


class BlessGATTCharacteristicDotNet(BleakGATTCharacteristicDotNet):
    """
    DotNet implementation of the BlessGATTCharacteristic
    """

    def __init__(self, obj):
        super().__init__(obj)
        self._value: bytearray = bytearray(b"")

    @staticmethod
    def permissions_to_protection_level(
        permissions: GATTAttributePermissions, read: bool
    ) -> GattProtectionLevel:
        """
        Convert the GATTAttributePermissions into a GattProtectionLevel
        GATTAttributePermissions currently only consider Encryption or Plain

        Parameters
        ----------
        permissions : GATTAttributePermissions
            The permission flags for the characteristic
        read : bool
            If True, processes the permissions for Reading, else process for Writing

        Returns
        -------
        GattProtectionLevel
            The protection level equivalent
        """
        result: GattProtectionLevel = GattProtectionLevel.Plain
        shift_value: int = 3 if read else 4
        permission_value: int = permissions.value >> shift_value
        if permission_value & 1:
            result |= GattProtectionLevel.EncryptionRequired
        return result

    @property
    def value(self) -> bytearray:
        """Get the value of the characteristic"""
        return self._value

    @value.setter
    def value(self, val: bytearray):
        """Set the value of the characteristic"""
        self._value = val
