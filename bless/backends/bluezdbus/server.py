import asyncio

from uuid import UUID

from typing import Any, Optional, cast

from asyncio import AbstractEventLoop

from dbus_next.aio import MessageBus, ProxyObject  # type: ignore
from dbus_next.constants import BusType  # type: ignore

from bless.backends.server import BaseBlessServer  # type: ignore
from bless.backends.bluezdbus.characteristic import BlessGATTCharacteristicBlueZDBus
from bless.backends.bluezdbus.descriptor import BlessGATTDescriptorBlueZDBus
from bless.backends.bluezdbus.dbus.application import (  # type: ignore
    BlueZGattApplication,
)
from bless.backends.bluezdbus.dbus.utils import get_adapter  # type: ignore
from bless.backends.bluezdbus.dbus.characteristic import (  # type: ignore
    BlueZGattCharacteristic,
)

from bless.backends.bluezdbus.service import BlessGATTServiceBlueZDBus

from bless.backends.attribute import (  # type: ignore
    GATTAttributePermissions,
)

from bless.backends.characteristic import (  # type: ignore
    GATTCharacteristicProperties,
)

from bless.backends.descriptor import (  # type: ignore
    GATTDescriptorProperties,
)

from bleak.uuids import normalize_uuid_str


class BlessServerBlueZDBus(BaseBlessServer):
    """
    The BlueZ DBus implementation of the Bless Server

    Attributes
    ----------
    name : str
        The name of the server that will be advertised]

    """

    def __init__(self, name: str, loop: Optional[AbstractEventLoop] = None, **kwargs):
        super(BlessServerBlueZDBus, self).__init__(loop=loop, **kwargs)
        self.name: str = name
        self._adapter: Optional[str] = kwargs.get("adapter", None)

        self.setup_task: asyncio.Task = self.loop.create_task(self.setup())

    async def setup(self: "BlessServerBlueZDBus"):
        """
        Asyncronous side of init
        """
        self.bus: MessageBus = await MessageBus(bus_type=BusType.SYSTEM).connect()

        self.app: BlueZGattApplication = BlueZGattApplication(
            self.name, "org.bluez", self.bus
        )

        self.app.Read = self.read
        self.app.Write = self.write

        # We don't need to define these
        self.app.StartNotify = lambda x: None
        self.app.StopNotify = lambda x: None

        potential_adapter: Optional[ProxyObject] = await get_adapter(
            self.bus, self._adapter
        )
        if potential_adapter is None:
            raise Exception("Could not locate bluetooth adapter")
        self.adapter: ProxyObject = cast(ProxyObject, potential_adapter)

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
        self.bus.export(self.app.path, self.app)

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

        # Remove our App
        self.bus.unexport(self.app.path, self.app)

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
        service: BlessGATTServiceBlueZDBus = cast(
            BlessGATTServiceBlueZDBus, self.services[str(UUID(service_uuid))]
        )
        characteristic: BlessGATTCharacteristicBlueZDBus = (
            BlessGATTCharacteristicBlueZDBus(char_uuid, properties, permissions, value)
        )
        await characteristic.init(service)

        # Add it to the service
        self.services[service.uuid].add_characteristic(characteristic)

    async def add_new_descriptor(
        self,
        service_uuid: str,
        char_uuid: str,
        desc_uuid: str,
        properties: GATTDescriptorProperties,
        value: Optional[bytearray],
        permissions: GATTAttributePermissions,
    ):
        """
        Add a new characteristic to be associated with the server

        Parameters
        ----------
        service_uuid : str
            The string representation of the UUID of the GATT service to which
            this existing characteristic belongs
        char_uuid : str
            The string representation of the UUID of the GATT characteristic
            to which this new descriptor should belong
        desc_uuid : str
            The string representation of the UUID of the descriptor
        properties : GATTDescriptorProperties
            GATT Characteristic Flags that define the descriptor
        value : Optional[bytearray]
            A byterray representation of the value to be associated with the
            descriptor. Can be None if the descriptor is writable
        permissions : GATTAttributePermissions
            GATT flags that define the permissions for the descriptor
        """
        await self.setup_task
        std_service_uuid = normalize_uuid_str(service_uuid)
        service: BlessGATTServiceBlueZDBus = cast(
            BlessGATTServiceBlueZDBus, self.services[std_service_uuid]
        )
        std_char_uuid = normalize_uuid_str(char_uuid)
        characteristic: BlessGATTCharacteristicBlueZDBus = cast(
            BlessGATTCharacteristicBlueZDBus,
            service.get_characteristic(std_char_uuid),
        )
        std_desc_uuid = normalize_uuid_str(desc_uuid)
        descriptor: BlessGATTDescriptorBlueZDBus = (
            BlessGATTDescriptorBlueZDBus(std_desc_uuid, properties, permissions, value)
        )

        await descriptor.init(characteristic)

        # Add it to the characteristic
        service.get_characteristic(str(UUID(char_uuid))).add_descriptor(descriptor)

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
        bless_service: Optional[BlessGATTServiceBlueZDBus] = cast(
            Optional[BlessGATTServiceBlueZDBus], self.get_service(service_uuid)
        )
        if bless_service is None:
            return False

        bless_char: BlessGATTCharacteristicBlueZDBus = cast(
            BlessGATTCharacteristicBlueZDBus,
            bless_service.get_characteristic(char_uuid),
        )
        cur_value: Any = bless_char.value

        characteristic: BlueZGattCharacteristic = bless_char.gatt
        characteristic.Value = bytes(cur_value)  # type: ignore
        return True

    def read(self, char: BlueZGattCharacteristic) -> bytes:
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
        bytes
            The value of the characteristic
        """
        return bytes(self.read_request(char.UUID, {}))

    def write(self, char: BlueZGattCharacteristic, value: bytes):
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
        return self.write_request(char.UUID, bytearray(value))
