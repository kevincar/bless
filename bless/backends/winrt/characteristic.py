import sys
from uuid import UUID
from typing import Union, Optional, Dict

from bleak.backends.characteristic import (  # type: ignore
    BleakGATTCharacteristic,
)
from bleak.backends.descriptor import BleakGATTDescriptor  # type: ignore

if sys.version_info >= (3, 12):
    from winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattProtectionLevel,
        GattLocalCharacteristicParameters,
        GattLocalCharacteristic,
        GattLocalCharacteristicResult,
        GattCharacteristicProperties,
    )
else:
    from bleak_winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattProtectionLevel,
        GattLocalCharacteristicParameters,
        GattLocalCharacteristic,
        GattLocalCharacteristicResult,
        GattCharacteristicProperties,
    )

from bless.backends.service import BlessGATTService

from bless.backends.attribute import (
    GATTAttributePermissions,
)

from bless.backends.characteristic import (
    BlessGATTCharacteristic as BaseBlessGATTCharacteristic,
    GATTCharacteristicProperties,
)


class BlessGATTCharacteristicWinRT(
    BaseBlessGATTCharacteristic, BleakGATTCharacteristic
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
        BaseBlessGATTCharacteristic.__init__(self, uuid, properties, permissions, value)
        self._value = value
        self._descriptors: Dict[int, BleakGATTDescriptor] = {}
        self._gatt_characteristic: Optional[GattLocalCharacteristic] = None

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
        char_parameters.characteristic_properties = GattCharacteristicProperties(
            self._properties_flags.value
        )
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

        gatt_char: Optional[GattLocalCharacteristic] = (
            characteristic_result.characteristic
        )

        # Store the WinRT characteristic
        self._gatt_characteristic = gatt_char
        self.obj = gatt_char
        self._service_uuid = service.uuid
        self._handle = 0
        self._max_write_without_response_size = lambda: 128

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
            result |= GattProtectionLevel.ENCRYPTION_REQURIED  # type: ignore
        return result

    @property
    def value(self) -> bytearray:
        """Get the value of the characteristic"""
        return self._value

    @value.setter
    def value(self, val: bytearray):
        """Set the value of the characteristic"""
        self._value = val
