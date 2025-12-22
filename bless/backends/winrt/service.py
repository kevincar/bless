import sys
from uuid import UUID
from typing import Union, Optional, cast, TYPE_CHECKING, List, Dict

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

from bleak.backends.characteristic import BleakGATTCharacteristic  # type: ignore
from bleak.backends.service import BleakGATTService  # type: ignore
from bless.backends.service import BlessGATTService as BaseBlessGATTService

if TYPE_CHECKING:
    from bless.backends.server import BaseBlessServer
    from bless.backends.winrt.server import BlessServerWinRT


class BlessGATTServiceWinRT(BaseBlessGATTService, BleakGATTService):
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
        BaseBlessGATTService.__init__(self, uuid)
        self.service_provider: Optional[GattServiceProvider] = None
        self._local_service: Optional[GattLocalService] = None
        self.__characteristics: List[BleakGATTCharacteristic] = []
        self._characteristics: Dict[int, BleakGATTCharacteristic] = (
            {}
        )  # For Bleak compatibility

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
        service_provider = service_provider_result.service_provider
        if service_provider is None:
            raise RuntimeError("Failed to create GATT service provider")
        self.service_provider = service_provider
        service_provider.add_advertisement_status_changed(winrt_server._status_update)
        new_service: Optional[GattLocalService] = service_provider.service
        if new_service is None:
            raise RuntimeError("Failed to create local GATT service")
        self._local_service = new_service
        self.obj = new_service
        self._handle = 0

    @property
    def handle(self) -> int:
        """The integer handle of this service"""
        return self._handle

    @property
    def uuid(self) -> str:
        """UUID for this service"""
        return self._uuid

    @property
    def description(self) -> str:
        """Description of this service"""
        return f"Service {self._uuid}"

    @property
    def characteristics(self) -> List[BleakGATTCharacteristic]:
        """List of characteristics for this service"""
        return self.__characteristics

    def add_characteristic(self, characteristic: BleakGATTCharacteristic):
        """Add a characteristic to this service"""
        self.__characteristics.append(characteristic)
        # Also add to the dict for Bleak compatibility
        handle = len(self._characteristics)
        self._characteristics[handle] = characteristic

    def get_characteristic(self, uuid: Union[str, UUID]):
        """Get a characteristic by UUID"""
        uuid_str = str(uuid) if isinstance(uuid, UUID) else uuid
        for char in self.__characteristics:
            if char.uuid == uuid_str:
                return char
        return None
