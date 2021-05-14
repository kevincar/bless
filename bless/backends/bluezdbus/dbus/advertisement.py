from enum import Enum

from typing import List, Dict, TYPE_CHECKING

from txdbus.objects import DBusObject, DBusProperty, dbusMethod  # type: ignore
from txdbus.interface import DBusInterface, Method, Property  # type: ignore

if TYPE_CHECKING:
    from bless.backends.bluezdbus.dbus.application import (  # type: ignore
        BlueZGattApplication,
    )


class Type(Enum):
    BROADCAST = "broadcast"
    PERIPHERAL = "peripheral"


class BlueZLEAdvertisement(DBusObject):
    """
    org.bluez.LEAdvertisement1 interface implementation
    """

    interface_name: str = "org.bluez.LEAdvertisement1"

    iface: DBusInterface = DBusInterface(
        interface_name,
        Method("Release"),
        Property("Type", "s"),
        Property("ServiceUUIDs", "as"),
        Property("ManufacturerData", "a{qay}"),
        Property("SolicitUUIDs", "as"),
        Property("ServiceData", "a{sv}"),
        Property("IncludeTxPower", "b"),
    )

    dbusInterfaces: List[DBusInterface] = [iface]

    ad_type: DBusProperty = DBusProperty("Type")
    service_uuids: DBusProperty = DBusProperty("ServiceUUIDs")
    # manufacturer_data = DBusProperty("ManufacturerData")
    # solicit_uuids = DBusProperty("SolicitUUIDs")
    # service_data = DBusProperty("ServiceData")
    include_tx_power: DBusProperty = DBusProperty("IncludeTxPower")

    def __init__(
        self,
        advertising_type: Type,
        index: int,
        app: "BlueZGattApplication",  # noqa: F821
    ):
        """
        New Low Energy Advertisement

        Parameters
        ----------
        advertising_type : Type
            The type of advertisement
        index : int,
            The index of the advertisement
        app : BlueZGattApplication
            The Application that is responsible for this advertisement
        """
        self.ad_type: str = advertising_type.value
        self.path = app.base_path + "/advertisement" + str(index)

        self.service_uuids: List[str] = []
        self.manufacturer_data: Dict = {}
        self.solicit_uuids = [""]
        self.service_data = {"": 0}

        self.include_tx_power: bool = False

        self.data = None
        super(BlueZLEAdvertisement, self).__init__(self.path)

    @dbusMethod(interface_name, "Release")
    def Release(self):  # noqa: N802
        print("%s: Released!" % self.path)
