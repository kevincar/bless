import asyncio

from uuid import UUID

from typing import Optional, Dict, Any, cast, List

from asyncio import AbstractEventLoop
from twisted.internet.asyncioreactor import AsyncioSelectorReactor  # type: ignore
from txdbus import client  # type: ignore
from txdbus.objects import RemoteDBusObject  # type: ignore

from bless.backends.server import BaseBlessServer  # type: ignore
from bless.backends.bluezdbus.characteristic import BlessGATTCharacteristicBlueZDBus
from bless.backends.bluezdbus.dbus.application import (  # type: ignore
    BlueZGattApplication,
)
from bless.backends.bluezdbus.dbus.utils import get_adapter  # type: ignore
from bless.backends.bluezdbus.dbus.characteristic import (  # type: ignore
    BlueZGattCharacteristic,
)

from bless.backends.bluezdbus.service import BlessGATTServiceBlueZDBus

from bless.backends.characteristic import (  # type: ignore
    GATTCharacteristicProperties,
    GATTAttributePermissions,
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
        self.reactor: AsyncioSelectorReactor = AsyncioSelectorReactor(
            cast(asyncio.unix_events._UnixSelectorEventLoop, loop)
        )

        self.services: Dict[str, BlessGATTServiceBlueZDBus] = {}

        self.setup_task: asyncio.Task = self.loop.create_task(self.setup())

    async def setup(self):
        """
        Asyncronous side of init
        """
        self.bus: client = await client.connect(self.reactor, "system").asFuture(
            self.loop
        )

        gatt_name: str = self.name.replace(" ", "")
        self.app: BlueZGattApplication = BlueZGattApplication(
            gatt_name, "org.bluez." + gatt_name, self.bus, self.loop
        )

        self.app.Read = self.read
        self.app.Write = self.write

        # We don't need to define these
        self.app.StartNotify = lambda x: None
        self.app.StopNotify = lambda x: None

        self.adapter: RemoteDBusObject = await get_adapter(self.bus, self.loop)

    async def start(self, **kwargs) -> bool:
        """
        Start the server

        Returns
        -------
        bool
            Whether the server started successfully
        """
        await self.setup_task

        # Make our app available
        self.bus.exportObject(self.app)
        await self.bus.requestBusName(self.app.destination).asFuture(self.loop)

        # Register
        await self.app.register(self.adapter)

        # advertise
        await self.app.start_advertising(self.adapter)

        return True

    async def stop(self) -> bool:
        """
        Stop the server

        Returns
        -------
        bool
            Whether the server stopped successfully
        """
        # Stop Advertising
        await self.app.stop_advertising(self.adapter)

        # Unregister
        await self.app.unregister(self.adapter)

        return True

    async def is_connected(self) -> bool:
        """
        Determine whether there are any connected peripheral devices

        Returns
        -------
        bool
            Whether any peripheral devices are connected
        """
        return await self.app.is_connected()

    async def is_advertising(self) -> bool:
        """
        Determine whether the server is advertising

        Returns
        -------
        bool
            True if the server is advertising
        """
        await self.setup_task
        return await self.app.is_advertising(self.adapter)

    async def add_new_service(self, uuid: str):
        """
        Add a new GATT service to be hosted by the server

        Parameters
        ----------
        uuid : str
            The UUID for the service to add
        """
        await self.setup_task
        service: BlessGATTServiceBlueZDBus = BlessGATTServiceBlueZDBus(uuid)
        await service.init(self)
        self.services[service.uuid] = service

    async def add_new_characteristic(
        self,
        service_uuid: str,
        char_uuid: str,
        properties: GATTCharacteristicProperties,
        value: Optional[bytearray],
        permissions: GATTAttributePermissions,
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
        properties : GATTCharacteristicProperties
            GATT Characteristic Flags that define the characteristic
        value : Optional[bytearray]
            A byterray representation of the value to be associated with the
            characteristic. Can be None if the characteristic is writable
        permissions : int
            GATT Characteristic flags that define the permissions for the
            characteristic
        """
        await self.setup_task
        service: BlessGATTServiceBlueZDBus = self.services[str(UUID(service_uuid))]
        characteristic: BlessGATTCharacteristicBlueZDBus = (
            BlessGATTCharacteristicBlueZDBus(char_uuid, properties, permissions, value)
        )
        await characteristic.init(service)

        # Add it to the service
        self.services[service.uuid].add_characteristic(characteristic)

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
        service_uuid = str(UUID(service_uuid))
        char_uuid = str(UUID(char_uuid))
        bless_service: Optional[BlessGATTServiceBlueZDBus] = self.get_service(
            service_uuid
        )
        if bless_service is None:
            return False

        bless_char: BlessGATTCharacteristicBlueZDBus = bless_service.get_characteristic(
            char_uuid
        )
        cur_value: Any = bless_char.value

        characteristic: BlueZGattCharacteristic = bless_char.gatt
        characteristic.value = cur_value
        return True

    def read(self, char: BlueZGattCharacteristic) -> List[int]:
        """
        Read request.
        This re-routes the the request incomming on the dbus to the server to
        be re-routed to the user defined handler

        Note: the BlueZ App handles the data as a list of ints

        Parameters
        ----------
        char : BlueZGattCharacteristic
            The characteristic passed from the app

        Returns
        -------
        List[int]
            The value of the characteristic
        """
        return list(self.read_request(char.uuid))

    def write(self, char: BlueZGattCharacteristic, value: bytearray):
        """
        Write request.
        This function re-routes the write request sent from the
        BlueZGattApplication to the server function for re-route to the user
        defined handler

        Parameters
        ----------
        char : BlueZGattCharacteristic
            The characteristic object involved in the request
        value : bytearray
            The value being requested to set
        """
        return self.write_request(char.uuid, value)
