from uuid import UUID
from typing import List, Dict, Union, cast, TYPE_CHECKING

from bleak.backends.bluezdbus.service import BleakGATTServiceBlueZDBus  # type: ignore
from bless.backends.bluezdbus.characteristic import BlessGATTCharacteristicBlueZDBus
from bless.backends.bluezdbus.dbus.service import BlueZGattService
from bless.backends.service import BlessGATTService
from bless.backends.server import BaseBlessServer

if TYPE_CHECKING:
    from bless.backends.bluezdbus.server import BlessServerBlueZDBus


class BlessGATTServiceBlueZDBus(BlessGATTService, BleakGATTServiceBlueZDBus):
    """"
    GATT service implementation for the BlueZ backend
    """

    def __init__(self, uuid: Union[str, UUID]):
        """
        Initialize the Bless GATT Service

        Parameters
        ----------
        uuid : Union[str, UUID]
            The UUID to assign to the service
        """
        super(BlessGATTServiceBlueZDBus, self).__init__(uuid)
        self.__characteristics: List[BlessGATTCharacteristicBlueZDBus] = []
        self.__handle = 0

    async def init(self, server: "BaseBlessServer"):
        """
        Initialize the underlying bluez gatt service

        Parameters
        ----------
        server: BaseBlessServer
            The server to assign the service to
        """
        bluez_server: "BlessServerBlueZDBus" = cast("BlessServerBlueZDBus", server)
        gatt_service: BlueZGattService = await bluez_server.app.add_service(self._uuid)
        dict_obj: Dict = await gatt_service.get_obj()
        super(BlessGATTService, self).__init__(dict_obj, gatt_service.path)
        self.gatt = gatt_service

    @property
    def handle(self) -> int:
        """The integer handle of the service"""
        return self.__handle

    @property
    def uuid(self) -> str:
        """UUID for this service"""
        return self.obj["UUID"]

    @property
    def characteristics(self) -> List[BlessGATTCharacteristicBlueZDBus]:
        """List of characteristics for this service"""
        return self.__characteristics

    def add_characteristic(self, characteristic: BlessGATTCharacteristicBlueZDBus):
        """
        Should not be used by end user, but rather by `bleak` itself.
        """
        self.__characteristics.append(characteristic)

    @property
    def path(self):
        return self.__path
