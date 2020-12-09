from __future__ import annotations

from typing import List

from txdbus.objects import DBusObject, DBusProperty
from txdbus.interface import DBusInterface, Method, Property


class BlueZGattCharacteristic(DBusObject):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """

    interface_name: str = "org.bluez.GattCharacteristic1"

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
            flags: List[str],
            index: int,
            service: 'BlueZGattService',  # noqa: F821
            ):
        """
        Create a BlueZ Gatt Characteristic

        Parameters
        ----------
        uuid : str
            The unique identifier for the characteristic
        flags : List[str]
            A list of strings that represent the properties of the
            characteristic
        index : int
            The index number for this characteristic in the service
        service : BlueZService
            The Gatt Service that owns this characteristic
        """
        self.path: str = service.path + "/char" + str(index)
        self.uuid: str = uuid
        self.flags: List[str] = flags
        self.service: 'BlueZGattService' = service  # noqa: F821

        self.value: bytes = b''
        self.descriptors: List['BlueZGattDescriptor'] = []  # noqa: F821

        super(BlueZGattCharacteristic, self).__init__(self.path)
