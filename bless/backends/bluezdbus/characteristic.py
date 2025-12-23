from uuid import UUID

from typing import Union, Optional, List, Dict, cast, TYPE_CHECKING, Literal

from bleak.backends.characteristic import (  # type: ignore
    BleakGATTCharacteristic,
)
from bleak.backends.descriptor import BleakGATTDescriptor  # type: ignore

from bless.backends.attribute import GATTAttributePermissions
from bless.backends.characteristic import (
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
)
from bless.backends.bluezdbus.dbus.characteristic import (
    Flags,
    BlueZGattCharacteristic,
)

if TYPE_CHECKING:
    from bless.backends.bluezdbus.service import BlessGATTServiceBlueZDBus
    from bless.backends.service import BlessGATTService

# GattCharacteristicsFlags mappings from Bleak v1.1.1
_GattCharacteristicsFlagsEnum = {
    1: "broadcast",
    2: "read",
    4: "write-without-response",
    8: "write",
    16: "notify",
    32: "indicate",
    64: "authenticated-signed-writes",
    128: "extended-properties",
    256: "reliable-write",
    512: "writable-auxiliaries",
}


class BlessGATTCharacteristicBlueZDBus(
    BlessGATTCharacteristic, BleakGATTCharacteristic
):
    """
    BlueZ implementation of the BlessGATTCharacteristic
    """
    gatt: "BlueZGattCharacteristic"

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
        BlessGATTCharacteristic.__init__(self, uuid, properties, permissions, value)
        self._value = value
        self._descriptors: Dict[int, BleakGATTDescriptor] = {}

    async def init(self, service: "BlessGATTService"):
        """
        Initialize the BlueZGattCharacteristic object

        Parameters
        ----------
        service : BlessGATTService
            The service to assign the characteristic to
        """
        flags: List[Flags] = [
            transform_flags_with_permissions(flag, self._permissions)
            for flag in flags_to_dbus(self._properties_flags)
        ]

        # Add to our BlueZDBus app
        bluez_service: "BlessGATTServiceBlueZDBus" = cast(
            "BlessGATTServiceBlueZDBus", service
        )
        gatt_char: BlueZGattCharacteristic = (
            await bluez_service.gatt.add_characteristic(
                self._uuid, flags, bytes(self._value)
            )
        )

        # Store the BlueZ GATT characteristic
        self.gatt = gatt_char

        # Set attributes expected by BleakGATTCharacteristic
        self.obj = gatt_char  # The backend-specific object
        self.path = gatt_char.path  # D-Bus path
        self._service_uuid = service.uuid
        self._handle = 0  # Handle will be assigned by BlueZ
        self._max_write_without_response_size = lambda: 512  # Default MTU

    @property
    def service_uuid(self) -> str:
        """The UUID of the service this characteristic belongs to"""
        return self._service_uuid

    @property
    def service_handle(self) -> int:
        """The handle of the service this characteristic belongs to"""
        return 0  # Not used in BlueZ DBus

    @property
    def handle(self) -> int:
        """The handle of this characteristic"""
        return self._handle

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
        return self._uuid

    @property
    def description(self) -> str:
        """Description of this characteristic"""
        return f"Characteristic {self._uuid}"


def transform_flags_with_permissions(
    flag: Flags, permissions: GATTAttributePermissions
) -> Flags:
    """
    Returns the encrypted variant of a flag if the corresponding permission is
    set.
    """
    if (
        flag == Flags.READ
        and GATTAttributePermissions.read_encryption_required in permissions
    ):
        return Flags.ENCRYPT_READ
    if (
        flag == Flags.WRITE
        and GATTAttributePermissions.write_encryption_required in permissions
    ):
        return Flags.ENCRYPT_WRITE

    return flag


def flags_to_dbus(flags: GATTCharacteristicProperties) -> List[Flags]:
    """
    Convert Bleak/Bless flags

    Parameters
    ----------
    flags : GATTCharacteristicProperties
        The numerical enumeration for the combined flags

    Returns
    -------
    List[Flags]
        A list fo Flags for use in BlueZDBus
    """
    result: List[Flags] = []
    flag_value: int = flags.value
    for i, int_flag in enumerate(_GattCharacteristicsFlagsEnum.keys()):
        included: bool = int_flag & flag_value > 0
        if included:
            flag_enum_val: str = _GattCharacteristicsFlagsEnum[int_flag]
            flag: Flags = next(
                iter(
                    [
                        Flags.__members__[x]
                        for x in list(Flags.__members__)
                        if Flags.__members__[x].value == flag_enum_val
                    ]
                )
            )
            result.append(flag)

    return result


_Flags = List[
    Literal[
        "broadcast",
        "read",
        "write-without-response",
        "write",
        "notify",
        "indicate",
        "authenticated-signed-writes",
        "extended-properties",
        "reliable-write",
        "writable-auxiliaries",
        "encrypt-read",
        "encrypt-write",
        # "encrypt-notify" and "encrypt-indicate" are server-only
        "encrypt-authenticated-read",
        "encrypt-authenticated-write",
        # "encrypt-authenticated-notify", "encrypt-authenticated-indicate",
        # "secure-read", "secure-write", "secure-notify", "secure-indicate"
        # are server-only
        "authorize",
    ]
]
