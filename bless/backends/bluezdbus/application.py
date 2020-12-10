import asyncio

import bleak.backends.bluezdbus.defs as defs

from typing import List, Any

from txdbus import client
from txdbus.objects import DBusObject, RemoteDBusObject

from bless.backends.bluezdbus.advertisement import (
        Type,
        BlueZLEAdvertisement
        )
from bless.backends.bluezdbus.service import BlueZGattService
from bless.backends.bluezdbus.characteristic import (
        Flags,
        BlueZGattCharacteristic
        )


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
        self.loop: asyncio.AbstractEventLoop = loop

        self.base_path: str = "/org/bluez/" + name
        self.advertisements: List[BlueZLEAdvertisement] = []
        self.services: List[BlueZGattService] = []

        super(BlueZGattApplication, self).__init__(self.path)

    async def add_service(self, uuid: str):  # noqa: F821
        """
        Add a service to the application
        The first service to be added will be the primary service

        Parameters
        ----------
        uuid : str
            The string representation of the uuid for the service to create
        """

        index: int = len(self.services) + 1
        primary: bool = index == 1
        service: BlueZGattService = BlueZGattService(
                uuid, primary, index, self
                )
        self.services.append(service)
        self.bus.exportObject(service)
        await self.bus.requestBusName(self.destination).asFuture(self.loop)

    async def add_characteristic(
            self,
            service_uuid: str,
            uuid: str,
            value: Any,
            flags: List[Flags]
            ):
        """
        Add a characteristic to the service


        Parameters
        ----------
        service_uuid: str
            The string representation of the UUID for the service that this
            characteristic belongs to
        uuid : str
            The string representation of the UUID for the characteristic
        value : Any
            The value of the characteristic,
        flags: List[Flags]
            A list of flags to apply to the characteristic
        """
        service: BlueZGattService = next(iter([
            x
            for x in self.services
            if x.uuid == service_uuid
            ]))
        index: int = len(service.characteristics) + 1
        characteristic: BlueZGattCharacteristic = BlueZGattCharacteristic(
                uuid, flags, index, service
                )
        characteristic.value = value

        service.characteristics.append(characteristic)
        self.bus.exportObject(characteristic)
        await self.bus.requestBusName(self.destination).asFuture(self.loop)

    async def register(self, adapter: RemoteDBusObject):
        """
        Register the application with BlueZDBus

        Parameters
        ----------
        adapter : DBusObject
            The adapter to register the application with
        """
        await adapter.callRemote(
                "RegisterApplication",
                self.path,
                {},
                interface=defs.GATT_MANAGER_INTERFACE
                ).asFuture(self.loop)

    async def start_advertising(self, adapter: RemoteDBusObject):
        """
        Start Advertising the application
        """
        advertisement: BlueZLEAdvertisement = BlueZLEAdvertisement(
                Type.PERIPHERAL, len(self.advertisements)+1, self
                )
        self.advertisements.append(advertisement)

        for service in self.services:
            advertisement.service_uuids.append(service.uuid)

        self.bus.exportObject(advertisement)
        await self.bus.requestBusName(self.destination).asFuture(self.loop)

        await adapter.callRemote(
                "RegisterAdvertisement",
                advertisement.path,
                {}
                ).asFuture(self.loop)

    async def is_advertising(self, adapter: RemoteDBusObject):
        """
        Check if the adapter is advertising
        """
        objects: Dict = await adapter.callRemote(
                "GetManagedObjects",
                interface=defs.OBJECT_MANAGER_INTERFACE
                ).asFuture(self.loop)
        print(objects)
    async def stop_advertising(self, adapter: RemoteDBusObject):
        """
        Stop Advertising
        """
        advertisement: BlueZLEAdvertisement = self.advertisements.pop()
        await adapter.callRemote(
                "UnregisterAdvertisement",
                advertisement.path
                ).asFuture(self.loop)
