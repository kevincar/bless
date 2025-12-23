from uuid import UUID
from typing import List, Dict, Union, cast, TYPE_CHECKING

from bleak.backends.service import BleakGATTService  # type: ignore
from bleak.backends.characteristic import BleakGATTCharacteristic  # type: ignore
from bless.backends.bluezdbus.characteristic import BlessGATTCharacteristicBlueZDBus
from bless.backends.bluezdbus.dbus.service import BlueZGattService
from bless.backends.service import BlessGATTService as BaseBlessGATTService
from bless.backends.server import BaseBlessServer

if TYPE_CHECKING:
    from bless.backends.bluezdbus.server import BlessServerBlueZDBus


class BlessGATTServiceBlueZDBus(BaseBlessGATTService, BleakGATTService):
    """ "
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
        BaseBlessGATTService.__init__(self, uuid)
        self.__characteristics: List[BlessGATTCharacteristicBlueZDBus] = []
        self._characteristics: Dict[int, BleakGATTCharacteristic] = (
            {}
        )  # For Bleak compatibility
        self.__handle = 0
        self.__path = ""

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

        # Store the BlueZ GATT service
        self.gatt = gatt_service
        self.__path = gatt_service.path

        # Set attributes expected by BleakGATTService
        self.obj = gatt_service  # The backend-specific object
        self._handle = 0  # Handle will be assigned by BlueZ

    @property
    def handle(self) -> int:
        """The integer handle of the service"""
        return self.__handle

    @property
    def uuid(self) -> str:
        """UUID for this service"""
        return self._uuid

    @property
    def description(self) -> str:
        """Description of this service"""
        return f"Service {self._uuid}"

    @property
    def characteristics(self) -> List[BlessGATTCharacteristicBlueZDBus]:  # type: ignore
        """List of characteristics for this service"""
        return self.__characteristics

    def add_characteristic(  # type: ignore
        self, characteristic: BlessGATTCharacteristicBlueZDBus
    ):
        """
        Should not be used by end user, but rather by `bleak` itself.
        """
        self.__characteristics.append(characteristic)
        # Also add to the dict for Bleak compatibility (using handle as key)
        handle = len(self._characteristics)
        self._characteristics[handle] = characteristic

    @property
    def path(self):
        return self.__path
