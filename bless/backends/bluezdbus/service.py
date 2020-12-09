from __future__ import annotations

import asyncio

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

    interface_name: str = "org.bluez.GattService1"

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
            destination: str,
            bus: client,
            loop: asyncio.AbstractEventLoop
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
        destination : str
            A string representation of the destination interface this object
            should belong to
        bus : client
            An active client connection to DBus
        loop : asyncio.AbstractEventLoop
            The asyncio loop the service should run on
        """
        self.path: str = app.path + "/service" + str(index)
        self.bus: client = bus
        self.destination: str = destination
        self.uuid: str = uuid
        self.primary: bool = primary
        self.loop: asyncio.AbstractEventLoop = loop

        self.characteristics: List[BlueZGattCharacteristic] = []
