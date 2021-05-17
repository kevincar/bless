import asyncio

from typing import List, TYPE_CHECKING, Any, Dict

from txdbus import client  # type: ignore
from txdbus.objects import (  # type: ignore
        DBusObject,
        DBusProperty,
        RemoteDBusObject
        )
from txdbus.interface import DBusInterface, Property  # type: ignore

from bleak.backends.bluezdbus import defs  # type: ignore

from .characteristic import BlueZGattCharacteristic, Flags  # type: ignore

if TYPE_CHECKING:
    from bless.backends.bluezdbus.dbus.application import (  # type: ignore
        BlueZGattApplication,
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
        app: "BlueZGattApplication",  # noqa: F821
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
        self.app: "BlueZGattApplication" = app  # noqa: F821

        self.characteristics: List[BlueZGattCharacteristic] = []
        super(BlueZGattService, self).__init__(self.path)

    async def add_characteristic(
        self, uuid: str, flags: List[Flags], value: Any
    ) -> BlueZGattCharacteristic:
        """
        Adds a BlueZGattCharacteristic to the service.

        Parameters
        ----------
        uuid : str
            The string representation of the UUID for the characteristic
        flags : List[Flags],
            A list of flags to apply to the characteristic
        value : Any
            The characteristic's value
        """
        index: int = len(self.characteristics) + 1
        characteristic: BlueZGattCharacteristic = BlueZGattCharacteristic(
            uuid, flags, index, self
        )
        characteristic.value = value
        self.characteristics.append(characteristic)
        await self.app._register_object(characteristic)
        return characteristic

    async def get_obj(self) -> Dict:
        """
        Obtain the underlying dictionary within the BlueZ API that describes
        the service

        Returns
        -------
        Dict
            The dictionary that describes the service
        """
        dbus_obj: RemoteDBusObject = await self.app.bus.getRemoteObject(
            self.app.destination, self.path
        ).asFuture(self.app.loop)
        dict_obj: Dict = await dbus_obj.callRemote(
            "GetAll",
            defs.GATT_SERVICE_INTERFACE,
            interface=defs.PROPERTIES_INTERFACE,
        ).asFuture(self.app.loop)
        return dict_obj
