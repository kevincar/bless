from typing import List, TYPE_CHECKING, Any, Dict

from dbus_next.aio import MessageBus  # type: ignore
from dbus_next.service import ServiceInterface, dbus_property  # type: ignore
from dbus_next.constants import PropertyAccess  # type: ignore
from dbus_next.signature import Variant  # type: ignore

from bleak.backends.bluezdbus import defs  # type: ignore

from .characteristic import BlueZGattCharacteristic, Flags  # type: ignore

if TYPE_CHECKING:
    from bless.backends.bluezdbus.dbus.application import (  # type: ignore
        BlueZGattApplication,
    )


class BlueZGattService(ServiceInterface):
    """
    org.bluez.GattService1 interface implementation
    """

    interface_name: str = defs.GATT_SERVICE_INTERFACE

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
        hex_index: str = hex(index)[2:].rjust(4, "0")
        self.path: str = app.base_path + "/service" + hex_index
        self.bus: MessageBus = app.bus
        self.destination: str = app.destination

        self._uuid: str = uuid
        self._primary: bool = primary

        self.app: "BlueZGattApplication" = app  # noqa: F821

        self.characteristics: List[BlueZGattCharacteristic] = []
        super(BlueZGattService, self).__init__(self.interface_name)

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":  # type: ignore # noqa: F821 N802
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> "b":  # type: ignore # noqa: F821 N802
        return self._primary

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
        characteristic._value = value  # type: ignore
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
        return {
            "Primary": Variant('b', self._primary),
            "UUID": Variant('s', self._uuid)
        }
