from __future__ import annotations

import asyncio

from typing import List

from txdbus import client
from txdbus.objects import DBusObject


class BlueZGattApplication(DBusObject):
    """
    org.bluez.GattApplication1 interface implementation
    """

    def __init__(
            self,
            name: str,
            destination: str,
            bus: client,
            loop: asyncio.AbstractEventLoop
            ):
        """
        Initialize a new GattApplication1

        Parameters
        ----------
        name : str
            The name of the Bluetooth Low Energy Application
        destination : str
            The destination interface to add the application to
        bus : client
            The txdbus connection
        loop : asyncio.AbstractEventLoop
            The loop to use
        """
        self.path: str = "/"
        self.name: str = name
        self.destination: str = destination
        self.bus: client = bus
        self.loop: asyncio.AbstractEventLoop

        self.base_path: str = "/org/bluez/" + name
        self.services: List['BlueZGattService'] = []  # noqa: F821

        super(BlueZGattApplication, self).__init__(self.path)

    async def add_service(self, service: "BlueZGattService"):  # noqa: F821
        """
        Add a service to the application

        Parameters
        ----------
        service : BlueZGattService
            The Service to add to the application. Characteristics must have
            already by added
        """

        self.services.append(service)
        self.bus.exportObject(service)
        await self.bus.requestBusName(self.destination).asFuture(self.loop)
