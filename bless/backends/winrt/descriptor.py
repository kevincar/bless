import sys
from bless.backends.characteristic import BlessGATTCharacteristic
from bless.backends.descriptor import BlessGATTDescriptor
from bless.backends.attribute import GATTAttributePermissions
from bless.backends.descriptor import GATTDescriptorProperties
from bless.backends.winrt.characteristic import BlessGATTCharacteristicWinRT
from bleak import BleakGATTDescriptor

from uuid import UUID
from typing import Union, Optional

if sys.version_info >= (3, 12):
    from winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattLocalDescriptor,
        GattLocalDescriptorResult,
        GattLocalDescriptorParameters,
    )
else:
    from bleak_winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattLocalDescriptor,
        GattLocalDescriptorResult,
        GattLocalDescriptorParameters,
    )


class BlessGATTDescriptorWinRT(BlessGATTDescriptor, BleakGATTDescriptor):
    """
    WinRT implementation of a GATT Descriptor
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
        self.value = value if value is not None else bytearray(b'\x00')

    async def init(self, characteristic: BlessGATTCharacteristic):
        desc_parameters: GattLocalDescriptorParameters = GattLocalDescriptorParameters()
        desc_parameters.read_protection_level = (
            BlessGATTCharacteristicWinRT.permissions_to_protection_level(
                self._permissions, True
            )
        )
        desc_parameters.write_protection_level = (
            BlessGATTCharacteristicWinRT.permissions_to_protection_level(
                self._permissions, True
            )
        )
        descriptor_result: GattLocalDescriptorResult = (
            await characteristic.obj.create_descriptor_async(
                UUID(self._uuid), desc_parameters
            )
        )
        gatt_desc: Optional[GattLocalDescriptor] = descriptor_result.descriptor
        if gatt_desc is None:
            raise RuntimeError("Failed to create GATT descriptor")
        self._gatt_descriptor = gatt_desc
        self.obj = gatt_desc
        self._characteristic_uuid = characteristic.uuid
        self._handle = 0

    @property
    def value(self) -> bytearray:
        """Get the value of the descriptor"""
        return bytearray(self._value)

    @value.setter
    def value(self, val: bytearray):
        """Set the value of the descriptor"""
        self._value = val
