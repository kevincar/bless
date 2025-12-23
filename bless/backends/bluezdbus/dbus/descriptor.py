from enum import Enum

import bleak.backends.bluezdbus.defs as defs  # type: ignore

from typing import List, Dict, TYPE_CHECKING

from dbus_next.service import (  # type: ignore
    ServiceInterface,
    method,
    dbus_property,
)
from dbus_next.constants import PropertyAccess  # type: ignore
from dbus_next.signature import Variant  # type: ignore

if TYPE_CHECKING:
    from bless.backends.bluezdbus.dbus.characteristic import (
        BlueZGattCharacteristic,
    )


class DescriptorFlags(Enum):
    READ = "read"
    WRITE = "write"
    ENCRYPT_READ = "encrypt-read"
    ENCRYPT_WRITE = "encrypt-write"
    ENCRYPT_AUTHENTICATED_READ = "encrypt-authenticated-read"
    ENCRYPT_AUTHENTICATED_WRITE = "encrypt-authenticated-write"
    AUTHORIZE = "authorize"


class BlueZGattDescriptor(ServiceInterface):
    """
    org.bluez.GattDescriptor1 interface implementation
    """

    interface_name: str = defs.GATT_DESCRIPTOR_INTERFACE

    def __init__(
        self,
        uuid: str,
        flags: List[DescriptorFlags],
        index: int,
        characteristic: "BlueZGattCharacteristic",  # noqa: F821
    ):
        """
        Create a BlueZ Gatt Descriptor

        Parameters
        ----------
        uuid : str
            The unique identifier for the descriptor
        flags : List[DescriptorFlags]
            A list of strings that represent the properties of the
            descriptor
        index : int
            The index number for this descriptor in the descriptors
        characteristic : BlueZService
            The Gatt Characteristic that owns this descriptor
        """
        self.path: str = characteristic.path + "/desc" + f"{index:04d}"
        self._uuid: str = uuid
        self._flags: List[str] = [x.value for x in flags]
        self._characteristic_path: str = characteristic.path  # noqa: F821
        self._characteristic: "BlueZGattCharacteristic" = characteristic  # noqa: F821

        self._value: bytes = b""

        super(BlueZGattDescriptor, self).__init__(self.interface_name)

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":  # type: ignore # noqa: F821 N802
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Characteristic(self) -> "o":  # type: ignore # noqa: F821 N802
        return self._characteristic_path

    @dbus_property()
    def Value(self) -> "ay":  # type: ignore # noqa: F821 N802
        return self._value

    @Value.setter  # type: ignore
    def Value(self, value: "ay"):  # type: ignore # noqa: F821 N802
        self._value = value
        self.emit_properties_changed(
            changed_properties={"Value": self._value}
        )

    @dbus_property(access=PropertyAccess.READ)  # noqa: F722
    def Flags(self) -> "as":  # type: ignore # noqa: F821 F722 N802
        return self._flags

    @method()  # noqa: F722
    def ReadValue(self, options: "a{sv}") -> "ay":  # type: ignore # noqa: F722 F821 N802 E501
        """
        Read the value of the descriptor.
        This is to be fully implemented at the application level

        Parameters
        ----------
        options : Dict
            A list of options

        Returns
        -------
        bytes
            The bytes that is the value of the descriptor
        """
        return self._value

    @method()  # noqa: F722
    def WriteValue(self, value: "ay", options: "a{sv}"):  # type: ignore # noqa
        """
        Write a value to the descriptor
        This is to be fully implemented at the application level

        Parameters
        ----------
        value : bytes
            The value to set
        options : Dict
            Some options for you to select from
        """
        self._value = value

    async def get_obj(self) -> Dict:
        """
        Obtain the underlying dictionary within the BlueZ API that describes
        the descriptor

        Returns
        -------
        Dict
            The dictionary that describes the descriptor
        """
        return {
            "UUID": Variant('s', self._uuid)
        }
