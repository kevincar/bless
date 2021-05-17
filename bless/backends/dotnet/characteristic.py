from uuid import UUID
from typing import Union, Optional

from bleak.backends.dotnet.characteristic import (  # type: ignore
    BleakGATTCharacteristicDotNet,
)
from bleak.backends.dotnet.utils import (  # type: ignore
    wrap_IAsyncOperation,
)

from System import Guid  # type: ignore
from Windows.Foundation import IAsyncOperation  # type: ignore
from Windows.Devices.Bluetooth.GenericAttributeProfile import (  # type: ignore
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


class BlessGATTCharacteristicDotNet(
    BlessGATTCharacteristic, BleakGATTCharacteristicDotNet
):
    """
    DotNet implementation of the BlessGATTCharacteristic
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
        Initialize the DotNet GattLocalCharacteristic object

        Parameters
        ----------
        service : BlessGATTServiceDotNet
            The service to assign the characteristic to
        """
        charguid: Guid = Guid.Parse(self._uuid)

        char_parameters: GattLocalCharacteristicParameters = (
            GattLocalCharacteristicParameters()
        )
        char_parameters.CharacteristicProperties = self._properties.value
        char_parameters.ReadProtectionLevel = (
            BlessGATTCharacteristicDotNet.permissions_to_protection_level(
                self._permissions, True
            )
        )
        char_parameters.WriteProtectionLevel = (
            BlessGATTCharacteristicDotNet.permissions_to_protection_level(
                self._permissions, False
            )
        )

        characteristic_result: GattLocalCharacteristicResult = (
            await wrap_IAsyncOperation(
                IAsyncOperation[GattLocalCharacteristicResult](
                    service.obj.CreateCharacteristicAsync(charguid, char_parameters)
                ),
                return_type=GattLocalCharacteristicResult,
            )
        )

        gatt_char: GattLocalCharacteristic = characteristic_result.Characteristic
        super(BlessGATTCharacteristic, self).__init__(obj=gatt_char)

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
