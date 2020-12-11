import asyncio

import bleak.backends.bluezdbus.defs as defs

from typing import List

from txdbus import client
from txdbus.objects import DBusObject, DBusProperty
from txdbus.interface import DBusInterface, Property

from bless.backends.bluezdbus.characteristic import (
        BlueZGattCharacteristic
        )


class BlueZGattService(DBusObject):
    """
    org.bluez.GattService1 interface implementation
    """

    interface_name: str = defs.GATT_SERVICE_INTERFACE

    iface: DBusInterface = DBusInterface(
            interface_name,
            Property("UUID", "s"),
            Property("Primary", "b"),
            )

    dbusInterfaces: List[DBusInterface] = [iface]

    uuid: DBusProperty = DBusProperty("UUID")
    primary: DBusProperty = DBusProperty("Primary")

    def __init__(
            self,
            uuid: str,
            primary: bool,
            index: int,
            app: 'BlueZGattApplication',  # noqa: F821
            ):
        """
        Initialize the DBusObject

        Parameters
        ----------
        uuid : str
            A string representation of the unique identifier
        primary : bool
            Whether the service is the primary service for the application it
            belongs to
        index : int
            The index of the service amongst the other service of the
            application
        app : BlueZApp
            A BlueZApp object that owns this service
        """
        self.path: str = app.base_path + "/service" + str(index)
        self.bus: client = app.bus
        self.destination: str = app.destination
        self.uuid: str = uuid
        self.primary: bool = primary
        self.loop: asyncio.AbstractEventLoop = app.loop
        self.app: 'BlueZGattApplication' = app  # noqa: F821

        self.characteristics: List[BlueZGattCharacteristic] = []
        super(BlueZGattService, self).__init__(self.path)
