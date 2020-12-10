import bleak.backends.bluezdbus.defs as defs

from enum import Enum

from typing import List

from txdbus.objects import DBusObject, DBusProperty
from txdbus.interface import DBusInterface, Method, Property



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
            Property("Flags", "as")
            )

    dbusInterfaces: List[DBusInterface] = [iface]

    uuid: DBusProperty = DBusProperty("UUID")
    service: DBusProperty = DBusProperty("Service")
    flags: DBusProperty = DBusProperty("Flags")
    value: DBusProperty = DBusProperty("Value")

    def __init__(
            self,
            uuid: str,
            flags: List[Flags],
            index: int,
            service: 'BlueZGattService',  # noqa: F821
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
        self.path: str = service.path + "/char" + str(index)
        self.uuid: str = uuid
        self.flags: List[str] = [x.value for x in flags]
        self.service: str = service.path  # noqa: F821

        self.value: bytes = b''
        self.descriptors: List['BlueZGattDescriptor'] = []  # noqa: F821

        super(BlueZGattCharacteristic, self).__init__(self.path)
