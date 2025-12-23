from enum import Enum

import bleak.backends.bluezdbus.defs as defs  # type: ignore

from typing import List, TYPE_CHECKING, Any, Dict

from dbus_next.service import ServiceInterface, method, dbus_property  # type: ignore
from dbus_next.constants import PropertyAccess  # type: ignore
from dbus_next.signature import Variant  # type: ignore

from .descriptor import BlueZGattDescriptor, DescriptorFlags  # type: ignore

if TYPE_CHECKING:
    from bless.backends.bluezdbus.dbus.service import (  # type: ignore # noqa: F401
        BlueZGattService
    )


class Flags(Enum):
    BROADCAST = "broadcast"
    READ = "read"
    WRITE_WITHOUT_RESPONSE = "write-without-response"
    WRITE = "write"
    NOTIFY = "notify"
    INDICATE = "indicate"
    AUTHENTICATED_SIGNED_WRITES = "authenticated-signed-writes"
    RELIABLE_WRITE = "reliable-write"
    WRITABLE_AUXILIARIES = "writable-auxiliaries"
    ENCRYPT_READ = "encrypt-read"
    ENCRYPT_WRITE = "encrypt-write"
    ENCRYPT_AUTHENTICATED_READ = "encrypt-authenticated-read"
    ENCRYPT_AUTHENTICATED_WRITE = "encrypt-authenticated-write"


class BlueZGattCharacteristic(ServiceInterface):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """

    interface_name: str = defs.GATT_CHARACTERISTIC_INTERFACE

    def __init__(
        self,
        uuid: str,
        flags: List[Flags],
        index: int,
        service: "BlueZGattService",  # noqa: F821
    ):
        """
        Create a BlueZ Gatt Characteristic

        Parameters
        ----------
        uuid : str
            The unique identifier for the characteristic
        flags : List[Flags]
            A list of strings that represent the properties of the
            characteristic
        index : int
            The index number for this characteristic in the service
        service : BlueZService
            The Gatt Service that owns this characteristic
        """
        self.path: str = service.path + "/char" + f"{index:04d}"
        self._uuid: str = uuid
        self._flags: List[str] = [x.value for x in flags]
        self._service_path: str = service.path  # noqa: F821
        self._service: "BlueZGattService" = service  # noqa: F821

        self._value: bytes = b""
        self._notifying: bool = (
            "notify" in self._flags
            or "indicate" in self._flags
        )
        self.descriptors: List["BlueZGattDescriptor"] = []  # noqa: F821

        super(BlueZGattCharacteristic, self).__init__(self.interface_name)

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":  # type: ignore # noqa: F821 N802
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Service(self) -> "o":  # type: ignore # noqa: F821 N802
        return self._service_path

    @dbus_property()
    def Value(self) -> "ay":  # type: ignore # noqa: F821 N802
        return self._value

    @Value.setter  # type: ignore
    def Value(self, value: "ay"):  # type: ignore # noqa: F821 N802
        self._value = value
        self.emit_properties_changed(
            changed_properties={"Value": self._value}
        )

    @dbus_property(access=PropertyAccess.READ)
    def Notifying(self) -> "b":  # type: ignore # noqa: F821 N802
        return self._notifying

    @dbus_property(access=PropertyAccess.READ)  # noqa: F722
    def Flags(self) -> "as":  # type: ignore # noqa: F821 F722 N802
        return self._flags

    @method()  # noqa: F722
    def ReadValue(self, options: "a{sv}") -> "ay":  # type: ignore # noqa: F722 F821 N802 E501
        """
        Read the value of the characteristic.
        This is to be fully implemented at the application level

        Parameters
        ----------
        options : Dict
            A list of options

        Returns
        -------
        bytes
            The bytes that is the value of the characteristic
        """
        f = self._service.app.Read
        if f is None:
            raise NotImplementedError()
        return f(self)

    @method()  # noqa: F722
    def WriteValue(self, value: "ay", options: "a{sv}"):  # type: ignore # noqa
        """
        Write a value to the characteristic
        This is to be fully implemented at the application level

        Parameters
        ----------
        value : bytes
            The value to set
        options : Dict
            Some options for you to select from
        """
        f = self._service.app.Write
        if f is None:
            raise NotImplementedError()
        f(self, value)

    @method()
    def StartNotify(self):  # noqa: N802
        """
        Begin a subscription to the characteristic
        """
        f = self._service.app.StartNotify
        if f is None:
            raise NotImplementedError()
        f(None)
        self._service.app.subscribed_characteristics.append(self._uuid)

    @method()
    def StopNotify(self):  # noqa: N802
        """
        Stop a subscription to the characteristic
        """
        f = self._service.app.StopNotify
        if f is None:
            raise NotImplementedError()
        f(None)
        self._service.app.subscribed_characteristics.remove(self._uuid)

    async def add_descriptor(
        self, uuid: str, flags: List[DescriptorFlags], value: Any
    ) -> BlueZGattDescriptor:
        """
        Adds a BlueZGattDescriptor to the characteristic.

        Parameters
        ----------
        uuid : str
            The string representation of the UUID for the descriptor
        flags : List[DescriptorFlags],
            A list of flags to apply to the descriptor
        value : Any
            The descriptor's value
        """
        index: int = len(self.descriptors) + 1
        descriptor: BlueZGattDescriptor = BlueZGattDescriptor(
            uuid, flags, index, self
        )
        descriptor._value = value  # type: ignore
        self.descriptors.append(descriptor)
        await self._service.app._register_object(descriptor)
        return descriptor

    async def get_obj(self) -> Dict:
        """
        Obtain the underlying dictionary within the BlueZ API that describes
        the characteristic

        Returns
        -------
        Dict
            The dictionary that describes the characteristic
        """
        return {
            "UUID": Variant('s', self._uuid)
        }
