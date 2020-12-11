import asyncio

from typing import Optional, Dict

from asyncio import AbstractEventLoop
from twisted.internet.asyncioreactor import AsyncioSelectorReactor
from txdbus import client

from bleak.backends.bluezdbus.service import BleakGATTServiceBlueZDBus

from bless.backends.server import BaseBlessServer
from bless.backends.bluezdbus.application import BlueZGattApplication
from bless.backends.bluezdbus.service import BlueZGattService

from bless.backends.characteristic import (
        GattCharacteristicsFlags
        )


class BlessServerBlueZDBus(BaseBlessServer):
    """
    The BlueZ DBus implementation of the Bless Server

    Attributes
    ----------
    name : str
        The name of the server that will be advertised]

    """

    def __init__(self, name: str, loop: AbstractEventLoop = None, **kwargs):
        super(BlessServerBlueZDBus, self).__init__(loop=loop, **kwargs)
        self.name: str = name
        self.reactor: AsyncioSelectorReactor = AsyncioSelectorReactor(loop)

        self.services: Dict[str, BleakGATTServiceBlueZDBus] = {}

        self.setup_task: asyncio.Task = self.loop.create_task(self.setup())

    async def setup(self):
        """
        Asyncronous side of init
        """
        self.bus: client = await client.connect(
                self.reactor, "system"
                ).asFuture(self.loop)

        gatt_name: str = self.name.replace(" ", "")
        self.app: BlueZGattApplication = BlueZGattApplication(
                gatt_name, "org.bluez."+gatt_name, self.bus, self.loop
                )

    async def start(self, **kwargs) -> bool:
        """
        Start the server

        Returns
        -------
        bool
            Whether the server started successfully
        """
        # Initialize advertising

        return True

    async def stop(self) -> bool:
        """
        Stop the server

        Returns
        -------
        bool
            Whether the server stopped successfully
        """
        raise NotImplementedError()

    def is_connected(self) -> bool:
        """
        Determine whether there are any connected peripheral devices

        Returns
        -------
        bool
            Whether any peripheral devices are connected
        """
        raise NotImplementedError()

    def is_advertising(self) -> bool:
        """
        Determine whether the server is advertising

        Returns
        -------
        bool
            True if the server is advertising
        """

    async def add_new_service(self, uuid: str):
        """
        Add a new GATT service to be hosted by the server

        Parameters
        ----------
        uuid : str
            The UUID for the service to add
        """
        print("Add Service 1")
        await self.setup_task
        print("Add Service 1")
        gatt_service: BlueZGattService = await self.app.add_service(uuid)
        print("Add Service 1")
        service: BleakGATTServiceBlueZDBus = BleakGATTServiceBlueZDBus(
                gatt_service,
                gatt_service.path
                )
        print("Add Service 1")
        self.services[uuid] = service
        print("Add Service 1")

    async def add_new_characteristic(
            self,
            service_uuid: str,
            char_uuid: str,
            properties: GattCharacteristicsFlags,
            value: Optional[bytearray],
            permissions: int
            ):
        """
        Add a new characteristic to be associated with the server

        Parameters
        ----------
        service_uuid : str
            The string representation of the UUID of the GATT service to which
            this new characteristic should belong
        char_uuid : str
            The string representation of the UUID of the characteristic
        properties : GattCharacteristicsFlags
            GATT Characteristic Flags that define the characteristic
        value : Optional[bytearray]
            A byterray representation of the value to be associated with the
            characteristic. Can be None if the characteristic is writable
        permissions : int
            GATT Characteristic flags that define the permissions for the
            characteristic
        """
        raise NotImplementedError()

    def update_value(self, service_uuid: str, char_uuid: str) -> bool:
        """
        Update the characteristic value. This is different than using
        characteristic.set_value. This method ensures that subscribed devices
        receive notifications, assuming the characteristic in question is
        notifyable

        Parameters
        ----------
        service_uuid : str
            The string representation of the UUID for the service associated
            with the characteristic whose value is to be updated
        char_uuid : str
            The string representation of the UUID for the characteristic whose
            value is to be updated

        Returns
        -------
        bool
            Whether the characteristic value was successfully updated
        """
        raise NotImplementedError()
