from enum import Enum

import bleak.backends.bluezdbus.defs as defs  # type: ignore

from typing import List, Dict, TYPE_CHECKING

from txdbus.objects import (  # type: ignore
        DBusObject,
        DBusProperty,
        dbusMethod,
        RemoteDBusObject
        )
from txdbus.interface import DBusInterface, Method, Property  # type: ignore

if TYPE_CHECKING:
    from bless.backends.bluezdbus.dbus.service import (  # type: ignore
        BlueZGattService,
        BlueZGattDescriptor,
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


class BlueZGattCharacteristic(DBusObject):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """

    interface_name: str = defs.GATT_CHARACTERISTIC_INTERFACE

    iface: DBusInterface = DBusInterface(
        interface_name,
        Method("ReadValue", arguments="a{sv}", returns="ay"),
        Method("WriteValue", arguments="aya{sv}"),
        Method("StartNotify"),
        Method("StopNotify"),
        Property("UUID", "s"),
        Property("Service", "o"),
        Property("Value", "ay"),
        Property("Notifying", "b"),
        Property("Flags", "as"),
    )

    dbusInterfaces: List[DBusInterface] = [iface]

    uuid: DBusProperty = DBusProperty("UUID")
    service: DBusProperty = DBusProperty("Service")
    flags: DBusProperty = DBusProperty("Flags")
    value: DBusProperty = DBusProperty("Value")
    notifying: DBusProperty = DBusProperty("Notifying")

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
        self.uuid: str = uuid
        self.flags: List[str] = [x.value for x in flags]
        self.service: str = service.path  # noqa: F821
        self._service: "BlueZGattService" = service  # noqa: F821

        self.value: bytes = b""
        self.notifying: bool = False
        self.descriptors: List["BlueZGattDescriptor"] = []  # noqa: F821

        super(BlueZGattCharacteristic, self).__init__(self.path)

    @dbusMethod(interface_name, "ReadValue")
    def ReadValue(self, options: Dict) -> bytearray:  # noqa: N802
        """
        Read the value of the characteristic.
        This is to be fully implemented at the application level

        Parameters
        ----------
        options : Dict
            A list of options

        Returns
        -------
        bytearray
            The bytearray that is the value of the characteristic
        """
        f = self._service.app.Read
        if f is None:
            raise NotImplementedError()
        return f(self)

    @dbusMethod(interface_name, "WriteValue")
    def WriteValue(self, value: bytearray, options: Dict):  # noqa: N802
        """
        Write a value to the characteristic
        This is to be fully implemented at the application level

        Parameters
        ----------
        value : bytearray
            The value to set
        options : Dict
            Some options for you to select from
        """
        f = self._service.app.Write
        if f is None:
            raise NotImplementedError()
        f(self, value)

    @dbusMethod(interface_name, "StartNotify")
    def StartNotify(self):  # noqa: N802
        """
        Begin a subscription to the characteristic
        """
        f = self._service.app.StartNotify
        if f is None:
            raise NotImplementedError()
        f(None)
        self._service.app.subscribed_characteristics.append(self.uuid)

    @dbusMethod(interface_name, "StopNotify")
    def StopNotify(self):  # noqa: N802
        """
        Stop a subscription to the characteristic
        """
        f = self._service.app.StopNotify
        if f is None:
            raise NotImplementedError()
        f(None)
        self._service.app.subscribed_characteristics.remove(self.uuid)

    async def get_obj(self) -> Dict:
        """
        Obtain the underlying dictionary within the BlueZ API that describes
        the characteristic

        Returns
        -------
        Dict
            The dictionary that describes the characteristic
        """
        dbus_obj: RemoteDBusObject = await self._service.app.bus.getRemoteObject(
            self._service.app.destination, self.path
        ).asFuture(self._service.app.loop)
        dict_obj: Dict = await dbus_obj.callRemote(
            "GetAll",
            defs.GATT_CHARACTERISTIC_INTERFACE,
            interface=defs.PROPERTIES_INTERFACE,
        ).asFuture(self._service.app.loop)
        return dict_obj
