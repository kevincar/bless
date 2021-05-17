from uuid import UUID
from typing import List, Union, cast, TYPE_CHECKING

from Windows.Devices.Bluetooth.GenericAttributeProfile import (  # type: ignore
    GattServiceProviderResult,
    GattServiceProvider,
    GattLocalService,
)
from Windows.Foundation import IAsyncOperation  # type: ignore
from System import Guid  # type: ignore

from bleak.backends.dotnet.utils import wrap_IAsyncOperation  # type: ignore
from bleak.backends.dotnet.service import BleakGATTServiceDotNet  # type: ignore

from bless.backends.service import BlessGATTService
from bless.backends.dotnet.characteristic import BlessGATTCharacteristicDotNet

if TYPE_CHECKING:
    from bless.backends.server import BaseBlessServer
    from bless.backends.dotnet.server import BlessServerDotNet


class BlessGATTServiceDotNet(BlessGATTService, BleakGATTServiceDotNet):
    """
    GATT Characteristic implementation for the DotNet backend
    """

    def __init__(self, uuid: Union[str, UUID]):
        """
        Initialize the Bless GATT Service object

        Parameters
        ----------
        uuid: Union[str, UUID]
            The UUID to assign to the service
        """
        super(BlessGATTServiceDotNet, self).__init__(uuid)
        self.__characteristics: List[BlessGATTCharacteristicDotNet] = []
        self.__handle = 0

    async def init(self, server: "BaseBlessServer"):
        """
        Initialize the GattLocalService Object

        Parameters
        ----------
        server: BlessServerDotNet
            The server to assign the service to
        """
        dotnet_server: "BlessServerDotNet" = cast("BlessServerDotNet", server)
        guid: Guid = Guid.Parse(self._uuid)

        service_provider_result: GattServiceProviderResult = await wrap_IAsyncOperation(
            IAsyncOperation[GattServiceProviderResult](
                GattServiceProvider.CreateAsync(guid)
            ),
            return_type=GattServiceProviderResult,
        )
        self.service_provider: GattServiceProvider = (
            service_provider_result.ServiceProvider
        )
        self.service_provider.AdvertisementStatusChanged += dotnet_server._status_update
        new_service: GattLocalService = self.service_provider.Service
        self.obj = new_service

    @property
    def handle(self) -> int:
        """The integer handle of the service"""
        return self.__handle

    @property
    def uuid(self) -> str:
        """UUID for this service"""
        return self.obj.Uuid.ToString()

    @property
    def characteristics(self) -> List[BlessGATTCharacteristicDotNet]:
        """List of characteristics for this service"""
        return self.__characteristics

    def add_characteristic(self, characteristic: BlessGATTCharacteristicDotNet):
        """
        Should not be used by end user, but rather by `bleak` itself.
        """
        self.__characteristics.append(characteristic)
