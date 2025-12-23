import re

import bleak.backends.bluezdbus.defs as defs  # type: ignore

from typing import List, Any, Callable, Optional, Union

from dbus_next.aio import MessageBus, ProxyObject, ProxyInterface  # type: ignore
from dbus_next.service import ServiceInterface  # type: ignore
from dbus_next.signature import Variant  # type: ignore

from bless.backends.bluezdbus.dbus.advertisement import (  # type: ignore
    Type,
    BlueZLEAdvertisement,
)
from bless.backends.bluezdbus.dbus.service import BlueZGattService  # type: ignore
from bless.backends.bluezdbus.dbus.characteristic import (  # type: ignore
    Flags,
    BlueZGattCharacteristic,
)
from bless.backends.bluezdbus.dbus.descriptor import BlueZGattDescriptor  # type: ignore


class BlueZGattApplication(ServiceInterface):
    """
    org.bluez.GattApplication1 interface implementation
    """

    def __init__(self, name: str, destination: str, bus: MessageBus):
        """
        Initialize a new GattApplication1

        Parameters
        ----------
        name : str
            The name of the Bluetooth Low Energy Application
        destination : str
            The destination interface to add the application to
        bus : MessageBus
            The dbus_next connection
        """
        self.path: str = "/"
        self.app_name: str = name
        self.destination: str = destination
        self.bus: MessageBus = bus

        # Valid path must be ASCII characters "[A-Z][a-z][0-9]_"
        # see https://dbus.freedesktop.org/doc/dbus-specification.html#message-protocol-marshaling-object-path  # noqa E501

        self.base_path: str = "/org/bluez/" + re.sub("[^A-Za-z0-9_]", "", self.app_name)
        self.advertisements: List[BlueZLEAdvertisement] = []
        self.services: List[BlueZGattService] = []

        self.Read: Optional[Callable[[BlueZGattCharacteristic], bytes]] = None
        self.Write: Optional[Callable[[BlueZGattCharacteristic, bytes], None]] = None
        self.StartNotify: Optional[Callable[[None], None]] = None
        self.StopNotify: Optional[Callable[[None], None]] = None

        self.subscribed_characteristics: List[str] = []

        super(BlueZGattApplication, self).__init__(self.destination)

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
        self.bus.export(service.path, service)
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
            iter([x for x in self.services if x._uuid == service_uuid])
        )
        return await service.add_characteristic(uuid, flags, value)

    async def set_name(self, adapter: ProxyObject, name: str):
        """
        Set's the alias of our bluetooth adapter to our application's name

        Parameters
        ----------
        adapter : ProxyObject
            The adapter whose alias name to set
        name : str
            The namem to set the adapter alias
        """
        iface: ProxyInterface = adapter.get_interface("org.freedesktop.DBus.Properties")
        await iface.call_set(  # type: ignore
            "org.bluez.Adapter1", "Alias", Variant("s", name)
        )

    async def register(self, adapter: ProxyObject):
        """
        Register the application with BlueZDBus

        Parameters
        ----------
        adapter : ProxyObject
            The adapter to register the application with
        """
        iface: ProxyInterface = adapter.get_interface(defs.GATT_MANAGER_INTERFACE)
        await iface.call_register_application(self.path, {})  # type: ignore

    async def unregister(self, adapter: ProxyObject):
        """
        Unregister the application with BlueZDBus

        Parameters
        ----------
        adapter : ProxyObject
            The adapter on which the current application is registered
        """
        iface: ProxyInterface = adapter.get_interface(defs.GATT_MANAGER_INTERFACE)
        await iface.call_unregister_application(self.path)  # type: ignore

    async def start_advertising(self, adapter: ProxyObject):
        """
        Start Advertising the application

        Parameters
        ----------
        adapter : ProxyObject
            The adapter object to start advertising on
        """
        await self.set_name(adapter, self.app_name)

        advertisement: BlueZLEAdvertisement = BlueZLEAdvertisement(
            Type.PERIPHERAL, len(self.advertisements) + 1, self
        )
        self.advertisements.append(advertisement)

        # Only add the first UUID
        advertisement._service_uuids.append(self.services[0].UUID)

        self.bus.export(advertisement.path, advertisement)

        iface: ProxyInterface = adapter.get_interface("org.bluez.LEAdvertisingManager1")
        await iface.call_register_advertisement(advertisement.path, {})  # type: ignore

    async def is_advertising(self, adapter: ProxyObject) -> bool:
        """
        Check if the adapter is advertising

        Parameters
        ----------
        adapter : ProxyObject
            The adapter object to check for advertising

        Returns
        -------
        bool
            Whether the adapter is advertising anything
        """
        iface: ProxyInterface = adapter.get_interface(defs.PROPERTIES_INTERFACE)
        instances: Variant = await iface.call_get(  # type: ignore
            "org.bluez.LEAdvertisingManager1", "ActiveInstances"
        )
        return instances.value > 0

    async def stop_advertising(self, adapter: ProxyObject):
        """
        Stop Advertising

        Parameters
        ----------
        adapter : ProxyObject
            The adapter object to stop advertising
        """
        await self.set_name(adapter, "")
        advertisement: BlueZLEAdvertisement = self.advertisements.pop()
        iface: ProxyInterface = adapter.get_interface("org.bluez.LEAdvertisingManager1")
        await iface.call_unregister_advertisement(advertisement.path)  # type: ignore
        self.bus.unexport(advertisement.path)

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
        self, o: Union[BlueZGattService, BlueZGattCharacteristic, BlueZGattDescriptor]
    ):
        """
        Register a service or characteristic object on the bus

        Parameters
        ----------
        o : A service or characteristic to register
        """
        self.bus.export(o.path, o)
