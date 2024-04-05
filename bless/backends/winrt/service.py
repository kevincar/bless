import sys
from uuid import UUID
from typing import Union, cast, TYPE_CHECKING
if sys.version_info >= (3, 12):
    from winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattServiceProviderResult,
        GattServiceProvider,
        GattLocalService,
    )
else:
    from bleak_winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattServiceProviderResult,
        GattServiceProvider,
        GattLocalService,
    )

from bleak.backends.winrt.service import BleakGATTServiceWinRT  # type: ignore
from bless.backends.service import BlessGATTService

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
        super(BlessGATTService, self).__init__(uuid)
        # self.__characteristics: List[BlessGATTCharacteristicWinRT] = []
        # self.__handle = 0

    async def init(self, server: "BaseBlessServer"):
        """
        Initialize the GattLocalService Object

        Parameters
        ----------
        server: BlessServerWinRT
            The server to assign the service to
        """
        winrt_server: "BlessServerWinRT" = cast("BlessServerWinRT", server)
        service_provider_result: GattServiceProviderResult = (
            await GattServiceProvider.create_async(UUID(self._uuid))
        )
        self.service_provider: GattServiceProvider = (
            service_provider_result.service_provider
        )
        self.service_provider.add_advertisement_status_changed(
            winrt_server._status_update
        )
        new_service: GattLocalService = self.service_provider.service
        self.obj = new_service
