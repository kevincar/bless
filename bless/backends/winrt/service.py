from uuid import UUID
from typing import List, Union, cast, TYPE_CHECKING

from bleak_winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore
    GattServiceProviderResult,
    GattServiceProvider,
    GattLocalService,
)
from bleak_winrt.windows.foundation import IAsyncOperation  # type: ignore

from bleak.backends.winrt.utils import wrap_IAsyncOperation  # type: ignore
from bleak.backends.winrt.service import BleakGATTServiceWinRT  # type: ignore

from bless.backends.service import BlessGATTService
from bless.backends.winrt.characteristic import BlessGATTCharacteristicWinRT

if TYPE_CHECKING:
    from bless.backends.server import BaseBlessServer
    from bless.backends.winrt.server import BlessServerWinRT


class BlessGATTServiceWinRT(BlessGATTService, BleakGATTServiceWinRT):
    """
    GATT Characteristic implementation for the WinRT backend
    """

    def __init__(self, uuid: Union[str, UUID]):
        """
        Initialize the Bless GATT Service object

        Parameters
        ----------
        uuid: Union[str, UUID]
            The UUID to assign to the service
        """
        super(BlessGATTServiceWinRT, self).__init__(uuid)
        self.__characteristics: List[BlessGATTCharacteristicWinRT] = []
        self.__handle = 0

    async def init(self, server: "BaseBlessServer"):
        """
        Initialize the GattLocalService Object

        Parameters
        ----------
        server: BlessServerWinRT
            The server to assign the service to
        """
        winrt_server: "BlessServerWinRT" = cast("BlessServerWinRT", server)
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
        self.service_provider.AdvertisementStatusChanged += winrt_server._status_update
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
    def characteristics(self) -> List[BlessGATTCharacteristicWinRT]:
        """List of characteristics for this service"""
        return self.__characteristics

    def add_characteristic(self, characteristic: BlessGATTCharacteristicWinRT):
        """
        Should not be used by end user, but rather by `bleak` itself.
        """
        self.__characteristics.append(characteristic)
