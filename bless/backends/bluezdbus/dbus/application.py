import asyncio

import bleak.backends.bluezdbus.defs as defs  # type: ignore

from typing import List, Any, Callable, Optional, Union

from txdbus import client  # type: ignore
from txdbus.objects import DBusObject, RemoteDBusObject  # type: ignore

from bless.backends.bluezdbus.dbus.advertisement import (  # type: ignore
    Type,
    BlueZLEAdvertisement,
)
from bless.backends.bluezdbus.dbus.service import BlueZGattService  # type: ignore
from bless.backends.bluezdbus.dbus.characteristic import (  # type: ignore
    Flags,
    BlueZGattCharacteristic,
)


class BlueZGattApplication(DBusObject):
    """
    org.bluez.GattApplication1 interface implementation
    """

    def __init__(
        self, name: str, destination: str, bus: client, loop: asyncio.AbstractEventLoop
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

        self.base_path: str = "/org/bluez/" + self.name
        self.advertisements: List[BlueZLEAdvertisement] = []
        self.services: List[BlueZGattService] = []

        self.Read: Optional[Callable[[BlueZGattCharacteristic], bytearray]] = None
        self.Write: Optional[
            Callable[[BlueZGattCharacteristic, bytearray], None]
        ] = None
        self.StartNotify: Optional[Callable[[None], None]] = None
        self.StopNotify: Optional[Callable[[None], None]] = None

        self.subscribed_characteristics: List[str] = []

        super(BlueZGattApplication, self).__init__(self.path)

    async def add_service(self, uuid: str) -> BlueZGattService:  # noqa: F821
        """
        Add a service to the application
        The first service to be added will be the primary service

        Parameters
        ----------
        uuid : str
            The string representation of the uuid for the service to create

        Returns
        -------
        BlueZGattService
            Returns and instance of the service object
        """

        index: int = len(self.services) + 1
        primary: bool = index == 1
        service: BlueZGattService = BlueZGattService(uuid, primary, index, self)
        self.services.append(service)
        self.bus.exportObject(service)
        await self.bus.requestBusName(self.destination).asFuture(self.loop)
        return service

    async def add_characteristic(
        self, service_uuid: str, uuid: str, value: Any, flags: List[Flags]
    ) -> BlueZGattCharacteristic:
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

        Returns
        -------
        BlueZGattCharacteristic
            The characteristic object
        """
        service: BlueZGattService = next(
            iter([x for x in self.services if x.uuid == service_uuid])
        )
        return await service.add_characteristic(uuid, flags, value)

    async def register(self, adapter: RemoteDBusObject):
        """
        Register the application with BlueZDBus

        Parameters
        ----------
        adapter : DBusObject
            The adapter to register the application with
        """
        await adapter.callRemote(
            "RegisterApplication", self.path, {}, interface=defs.GATT_MANAGER_INTERFACE
        ).asFuture(self.loop)

    async def unregister(self, adapter: RemoteDBusObject):
        """
        Unregister the application with BlueZDBus

        Parameters
        ----------
        adapter : RemoteDBusObject
            The adapter on which the current application is registered
        """
        await adapter.callRemote(
            "UnregisterApplication", self.path, interface=defs.GATT_MANAGER_INTERFACE
        ).asFuture(self.loop)

    async def start_advertising(self, adapter: RemoteDBusObject):
        """
        Start Advertising the application

        Parameters
        ----------
        adapter : RemoteDBusObject
            The adapter object to start advertising on
        """
        advertisement: BlueZLEAdvertisement = BlueZLEAdvertisement(
            Type.PERIPHERAL, len(self.advertisements) + 1, self
        )
        self.advertisements.append(advertisement)

        for service in self.services:
            advertisement.service_uuids.append(service.uuid)

        self.bus.exportObject(advertisement)
        await self.bus.requestBusName(self.destination).asFuture(self.loop)

        await adapter.callRemote(
            "RegisterAdvertisement", advertisement.path, {}
        ).asFuture(self.loop)

    async def is_advertising(self, adapter: RemoteDBusObject) -> bool:
        """
        Check if the adapter is advertising

        Parameters
        ----------
        adapter : RemoteDBusObject
            The adapter object to check for advertising

        Returns
        -------
        bool
            Whether the adapter is advertising anything
        """
        instances: int = await adapter.callRemote(
            "Get",
            "org.bluez.LEAdvertisingManager1",
            "ActiveInstances",
            interface=defs.PROPERTIES_INTERFACE,
        ).asFuture(self.loop)
        return instances > 0

    async def stop_advertising(self, adapter: RemoteDBusObject):
        """
        Stop Advertising

        Parameters
        ----------
        adapter : RemoteDBusObject
            The adapter object to stop advertising
        """
        advertisement: BlueZLEAdvertisement = self.advertisements.pop()
        await adapter.callRemote(
            "UnregisterAdvertisement", advertisement.path
        ).asFuture(self.loop)

    async def is_connected(self) -> bool:
        """
        Check if the application is connected
        This is not the same as if the adapter is connected to a device, but
        rather if there is a subscribed characteristic

        Returns
        -------
        bool
            Whether a central device is subscribed to one of our
            characteristics
        """
        return len(self.subscribed_characteristics) > 0

    async def _register_object(
        self, o: Union[BlueZGattService, BlueZGattCharacteristic]
    ):
        """
        Register a service or characteristic object on the bus

        Parameters
        ----------
        o : A service or characteristic to register
        """
        self.bus.exportObject(o)
        await self.bus.requestBusName(self.destination).asFuture(self.loop)
