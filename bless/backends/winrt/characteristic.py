import sys
from uuid import UUID
from typing import Union, Optional

from bleak.backends.winrt.characteristic import (  # type: ignore
    BleakGATTCharacteristicWinRT,
)

if sys.version_info >= (3, 12):
    from winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattProtectionLevel,
        GattLocalCharacteristicParameters,
        GattLocalCharacteristic,
        GattLocalCharacteristicResult,
    )
else:
    from bleak_winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattProtectionLevel,
        GattLocalCharacteristicParameters,
        GattLocalCharacteristic,
        GattLocalCharacteristicResult,
    )

from bless.backends.service import BlessGATTService

from bless.backends.characteristic import (
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)


class BlessGATTCharacteristicWinRT(
    BlessGATTCharacteristic, BleakGATTCharacteristicWinRT
):
    """
    WinRT implementation of the BlessGATTCharacteristic
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
        value = value if value is not None else bytearray(b"")
        super().__init__(uuid, properties, permissions, value)
        self.value = value

    async def init(self, service: BlessGATTService):
        """
        Initialize the WinRT GattLocalCharacteristic object

        Parameters
        ----------
        service : BlessGATTServiceWinRT
            The service to assign the characteristic to
        """
        char_parameters: GattLocalCharacteristicParameters = (
            GattLocalCharacteristicParameters()
        )
        char_parameters.characteristic_properties = self._properties.value
        char_parameters.read_protection_level = (
            BlessGATTCharacteristicWinRT.permissions_to_protection_level(
                self._permissions, True
            )
        )
        char_parameters.write_protection_level = (
            BlessGATTCharacteristicWinRT.permissions_to_protection_level(
                self._permissions, False
            )
        )

        characteristic_result: GattLocalCharacteristicResult = (
            await service.obj.create_characteristic_async(
                UUID(self._uuid), char_parameters
            )
        )

        gatt_char: GattLocalCharacteristic = characteristic_result.characteristic
        super(BlessGATTCharacteristic, self).__init__(
            obj=gatt_char, max_write_without_response_size=128
        )

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
        result: GattProtectionLevel = GattProtectionLevel.PLAIN
        shift_value: int = 3 if read else 4
        permission_value: int = permissions.value >> shift_value
        if permission_value & 1:
            result |= GattProtectionLevel.ENCRYPTION_REQURIED
        return result

    @property
    def value(self) -> bytearray:
        """Get the value of the characteristic"""
        return self._value

    @value.setter
    def value(self, val: bytearray):
        """Set the value of the characteristic"""
        self._value = val
