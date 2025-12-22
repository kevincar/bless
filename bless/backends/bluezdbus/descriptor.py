from uuid import UUID
from typing import Union, Optional, List, Dict, cast, TYPE_CHECKING, Literal

from bleak.backends.bluezdbus.defs import GattDescriptor1

from bless.backends.attribute import GATTAttributePermissions
from bless.backends.descriptor import (
    BlessGATTDescriptor,
    GATTDescriptorProperties,
)
from bless.backends.bluezdbus.dbus.descriptor import (
    DescriptorFlags,
    BlueZGattDescriptor,
)

if TYPE_CHECKING:
    from bless.backends.bluezdbus.characteristic import BlessGATTCharacteristicBlueZDBus
    from bless.backends.characteristic import BlessGATTCharacteristic


_GATTDescriptorsFlagsEnum = {
    0x0001: "read",
    0x0002: "write",
    # "encrypt-read"
    # "encrypt-write"
    # "encrypt-authenticated-read"
    # "encrypt-authenticated-write"
    # "secure-read" #(Server only)
    # "secure-write" #(Server only)
    # "authorize"
}


class BlessGATTDescriptorBlueZDBus(BlessGATTDescriptor):
    """
    BlueZ implementation of the BlessGATTDescriptor
    """
    gatt: "BlueZGattDescriptor"

    def __init__(
        self,
        uuid: Union[str, UUID],
        properties: GATTDescriptorProperties,
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
        properties : GATTDescriptorProperties
            The properties that define the characteristics behavior
        permissions : GATTAttributePermissions
            Permissions that define the protection levels of the properties
        value : Optional[bytearray]
            The binary value of the characteristic
        """
        value = value if value is not None else bytearray(b"")
        super().__init__(uuid, properties, permissions, value)
        self.value = value

    async def init(self, characteristic: "BlessGATTCharacteristic"):
        """
        Initialize the BlueZGattDescriptor object

        Parameters
        ----------
        characteristic : BlessGATTCharacteristic
            The characteristic to assign the descriptor to
        """
        flags: List[DescriptorFlags] = [
            transform_flags_with_permissions(flag, self._permissions)
            for flag in flags_to_dbus(self._properties)
        ]

        # Add to our BlueZDBus app
        bluez_characteristic: "BlessGATTCharacteristicBlueZDBus" = cast(
            "BlessGATTCharacteristicBlueZDBus", characteristic
        )
        gatt_desc: BlueZGattDescriptor = (
            await bluez_characteristic.gatt.add_descriptor(
                self._uuid, flags, bytes(self.value)
            )
        )
        self.gatt: BlueZGattDescriptor = gatt_desc
        dict_obj: Dict = await gatt_desc.get_obj()
        obj: GattDescriptor1 = GattDescriptor1(
            UUID=dict_obj["UUID"],
            Characteristic=characteristic.uuid,
            Value=bytes(self.value),
            Flags=cast(_Flags, flags),
        )

        # Add a Bleak Descriptor properties
        super(BlessGATTDescriptor, self).__init__(
            obj, 0, self._uuid, characteristic
        )

    @property
    def value(self) -> bytearray:
        """Get the value of the characteristic"""
        return bytearray(self._value)

    @value.setter
    def value(self, val: bytearray):
        """Set the value of the characteristic"""
        self._value = val

    @property
    def uuid(self) -> str:
        """The uuid of this characteristic"""
        return self.obj.get("UUID").value


def transform_flags_with_permissions(
    flag: DescriptorFlags, permissions: GATTAttributePermissions
) -> DescriptorFlags:
    """
    Returns the encrypted variant of a flag if the corresponding permission is
    set.

    Parameters
    ----------
    flag : GATTDescriptorProperties
        The numerical enumeration of a single flag

    permissions: GATTAttributePermissions
        The permissions for the characteristic

    Returns
    -------
    List[DescriptorFlags]
        A Flags enum value for use in BlueZDBus that reflects encryption
        requirements.
    """
    if (
        flag == DescriptorFlags.READ
        and GATTAttributePermissions.read_encryption_required in permissions
    ):
        return DescriptorFlags.ENCRYPT_READ
    if (
        flag == DescriptorFlags.WRITE
        and GATTAttributePermissions.write_encryption_required in permissions
    ):
        return DescriptorFlags.ENCRYPT_WRITE

    return flag


def flags_to_dbus(flags: GATTDescriptorProperties) -> List[DescriptorFlags]:
    """
    Convert Bleak/Bless flags

    Parameters
    ----------
    flags : GATTDescriptorProperties
        The numerical enumeration for the combined flags

    Returns
    -------
    List[DescriptorFlags]
        A list fo Flags for use in BlueZDBus
    """
    result: List[DescriptorFlags] = []
    flag_value: int = flags.value
    for i, int_flag in enumerate(_GATTDescriptorsFlagsEnum.keys()):
        included: bool = int_flag & flag_value > 0
        if included:
            flag_enum_val: str = _GATTDescriptorsFlagsEnum[int_flag]
            flag: DescriptorFlags = next(
                iter(
                    [
                        DescriptorFlags.__members__[x]
                        for x in list(DescriptorFlags.__members__)
                        if DescriptorFlags.__members__[x].value == flag_enum_val
                    ]
                )
            )
            result.append(flag)

    return result


_Flags = List[
    Literal[
        "read",
        "write",
        "encrypt-read",
        "encrypt-write",
        "encrypt-authenticated-read",
        "encrypt-authenticated-write",
        # "secure-read" and "secure-write" are server-only and not available in Bleak
        "authorize",
    ]
]
