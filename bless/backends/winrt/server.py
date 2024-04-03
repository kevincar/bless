import asyncio
import logging

import sys
from uuid import UUID
from threading import Event
from asyncio.events import AbstractEventLoop
from typing import Optional, List, Any, cast

from bless.backends.server import BaseBlessServer  # type: ignore
from bless.backends.characteristic import (  # type: ignore
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)
from bless.backends.winrt.service import BlessGATTServiceWinRT
from bless.backends.winrt.characteristic import (  # type: ignore
    BlessGATTCharacteristicWinRT,
)


from bless.backends.winrt.ble import BLEAdapter

# CLR imports
# Import of Bleak CLR->UWP Bridge.
# from BleakBridge import Bridge

# Import of other CLR components needed.
if sys.version_info >= (3, 12):
    from winrt.windows.foundation import Deferral  # type: ignore

    from winrt.windows.storage.streams import DataReader, DataWriter  # type: ignore

    from winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattWriteOption,
        GattServiceProvider,
        GattLocalCharacteristic,
        GattServiceProviderAdvertisingParameters,
        GattServiceProviderAdvertisementStatusChangedEventArgs as StatusChangeEvent,  # noqa: E501
        GattReadRequestedEventArgs,
        GattReadRequest,
        GattWriteRequestedEventArgs,
        GattWriteRequest,
        GattSubscribedClient,
    )
else:
    from bleak_winrt.windows.foundation import Deferral  # type: ignore

    from bleak_winrt.windows.storage.streams import DataReader, DataWriter  # type: ignore

    from bleak_winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattWriteOption,
        GattServiceProvider,
        GattLocalCharacteristic,
        GattServiceProviderAdvertisingParameters,
        GattServiceProviderAdvertisementStatusChangedEventArgs as StatusChangeEvent,  # noqa: E501
        GattReadRequestedEventArgs,
        GattReadRequest,
        GattWriteRequestedEventArgs,
        GattWriteRequest,
        GattSubscribedClient,
    )

logger = logging.getLogger(__name__)


class Request:
    def __init__(self):
        self._obj = None


class BlessServerWinRT(BaseBlessServer):
    """
    WinRT Implementation of BlessServer

    Attributes
    ----------
    name : str
        The name of the server to advertise
    services : Dict[str, BlessGATTServiceWinRT]
        A dictionary of services to be advertised by this server
    """

    def __init__(
        self,
        name: str,
        loop: Optional[AbstractEventLoop] = None,
        name_overwrite: bool = False,
        **kwargs,
    ):
        """
        Initialize a new instance of a Bless BLE peripheral (server) for WinRT

        Parameters
        ----------
        name : str
            The display name that central device uses when your service is
            identified. The `local_name`. By default, windows machines use the
            name of the computer. This can can be used instead if name_overwrite
            is set to True.
        loop : AbstractEventLoop
            An asyncio loop to run the server on
        name_overwrite : bool
            Defaults to false. If true, will cause the bluetooth system module
            to be renamed to self.name
        """
        super(BlessServerWinRT, self).__init__(loop=loop, **kwargs)

        self.name: str = name

        self._service_provider: Optional[GattServiceProvider] = None
        self._subscribed_clients: List[GattSubscribedClient] = []

        self._advertising: bool = False
        self._advertising_started: Event = Event()
        self._adapter: BLEAdapter = BLEAdapter()
        self._name_overwrite: bool = name_overwrite

    async def start(self: "BlessServerWinRT", **kwargs):
        """
        Start the server

        Parameters
        ----------
        timeout : float
            Floating point decimal in seconds for how long to wait for the
            on-board bluetooth module to power on
        """

        if self._name_overwrite:
            self._adapter.set_local_name(self.name)

        adv_parameters: GattServiceProviderAdvertisingParameters = (
            GattServiceProviderAdvertisingParameters()
        )
        adv_parameters.is_discoverable = True
        adv_parameters.is_connectable = True

        for uuid, service in self.services.items():
            winrt_service: BlessGATTServiceWinRT = cast(BlessGATTServiceWinRT, service)
            winrt_service.service_provider.start_advertising(adv_parameters)
        self._advertising = True
        self._advertising_started.wait()

    async def stop(self: "BlessServerWinRT"):
        """
        Stop the server
        """
        for uuid, service in self.services.items():
            winrt_service: BlessGATTServiceWinRT = cast(BlessGATTServiceWinRT, service)
            winrt_service.service_provider.stop_advertising()
        self._advertising = False

    async def is_connected(self) -> bool:
        """
        Determine whether there are any connected peripheral devices

        Returns
        -------
        bool
            True if there are any central devices that have subscribed to our
            characteristics
        """
        return len(self._subscribed_clients) > 0

    async def is_advertising(self) -> bool:
        """
        Determine whether the server is advertising

        Returns
        -------
        bool
            True if advertising
        """
        all_services_advertising: bool = False
        for uuid, service in self.services.items():
            winrt_service: BlessGATTServiceWinRT = cast(BlessGATTServiceWinRT, service)
            service_is_advertising: bool = (
                winrt_service.service_provider.advertisement_status == 2
            )
            all_services_advertising = (
                all_services_advertising or service_is_advertising
            )

        return self._advertising and all_services_advertising

    def _status_update(
        self, service_provider: GattServiceProvider, args: StatusChangeEvent
    ):
        """
        Callback function for the service provider to trigger when the
        advertizing status changes

        Parameters
        ----------
        service_provider : GattServiceProvider
            The service provider whose advertising status changed

        args : GattServiceProviderAdvertisementStatusChangedEventArgs
            The arguments associated with the status change
            See
            [here](https://docs.microsoft.com/en-us/uwp/api/windows.devices.bluetooth.genericattributeprofile.gattserviceprovideradvertisementstatuschangedeventargs.status?view=winrt-19041)
        """
        if args.status == 2:
            self._advertising_started.set()

    async def add_new_service(self, uuid: str):
        """
        Generate a new service to be associated with the server

        Parameters
        ----------
        uuid : str
            The string representation of the UUID of the service to be added
        """
        logger.debug("Creating a new service with uuid: {}".format(uuid))
        logger.debug("Adding service to server with uuid {}".format(uuid))
        service: BlessGATTServiceWinRT = BlessGATTServiceWinRT(uuid)
        await service.init(self)
        self.services[service.uuid] = service

    async def add_new_characteristic(
        self,
        service_uuid: str,
        char_uuid: str,
        properties: GATTCharacteristicProperties,
        value: Optional[bytearray],
        permissions: GATTAttributePermissions,
    ):
        """
        Generate a new characteristic to be associated with the server

        Parameters
        ----------
        service_uuid : str
            The string representation of the uuid of the service to associate
            the new characteristic with
        char_uuid : str
            The string representation of the uuid of the new characteristic
        properties : GATTCharacteristicProperties
            The flags for the characteristic
        value : Optional[bytearray]
            The initial value for the characteristic
        permissions : GATTAttributePermissions
            The permissions for the characteristic
        """

        service_uuid = str(UUID(service_uuid))
        char_uuid = str(UUID(char_uuid))
        service: BlessGATTServiceWinRT = cast(
            BlessGATTServiceWinRT, self.services[service_uuid]
        )
        characteristic: BlessGATTCharacteristicWinRT = BlessGATTCharacteristicWinRT(
            char_uuid, properties, permissions, value
        )
        await characteristic.init(service)
        characteristic.obj.add_read_requested(self.read_characteristic)
        characteristic.obj.add_write_requested(self.write_characteristic)
        characteristic.obj.add_subscribed_clients_changed(self.subscribe_characteristic)
        service.add_characteristic(characteristic)

    def update_value(self, service_uuid: str, char_uuid: str) -> bool:
        """
        Update the characteristic value. This is different than using
        characteristic.set_value. This send notifications to subscribed
        central devices.

        Parameters
        ----------
        service_uuid : str
            The string representation of the UUID for the service associated
            with the characteristic to be added
        char_uuid : str
            The string representation of the UUID for the characteristic to be
            added

        Returns
        -------
        bool
            Whether the value was successfully updated
        """
        service_uuid = str(UUID(service_uuid))
        char_uuid = str(UUID(char_uuid))
        service: Optional[BlessGATTServiceWinRT] = cast(
            Optional[BlessGATTServiceWinRT], self.get_service(service_uuid)
        )
        if service is None:
            return False
        characteristic: BlessGATTCharacteristicWinRT = cast(
            BlessGATTCharacteristicWinRT, service.get_characteristic(char_uuid)
        )
        value: bytes = characteristic.value
        value = value if value is not None else b"\x00"
        writer: DataWriter = DataWriter()
        writer.write_bytes(value)
        characteristic.obj.notify_value_async(writer.detach_buffer())

        return True

    def read_characteristic(
        self, sender: GattLocalCharacteristic, args: GattReadRequestedEventArgs
    ):
        """
        The is triggered by pythonnet when windows receives a read request for
        a given characteristic

        Parameters
        ----------
        sender : GattLocalCharacteristic
            The characteristic Gatt object whose value was requested
        args : GattReadRequestedEventArgs
            Arguments for the read request
        """
        logger.debug("Reading Characteristic")
        deferral: Deferral = args.get_deferral()
        value: bytearray = self.read_request(str(sender.uuid))
        logger.debug(f"Current Characteristic value {value}")
        value = value if value is not None else b"\x00"
        writer: DataWriter = DataWriter()
        writer.write_bytes(value)
        logger.debug("Getting request object {}".format(self))
        request: GattReadRequest

        async def f():
            nonlocal args
            nonlocal request
            request = await args.get_request_async()

        asyncio.new_event_loop().run_until_complete(f())
        logger.debug("Got request object {}".format(request))
        request.respond_with_value(writer.detach_buffer())
        deferral.complete()

    def write_characteristic(
        self, sender: GattLocalCharacteristic, args: GattWriteRequestedEventArgs
    ):
        """
        Called by pythonnet when a write request is submitted

        Parameters
        ----------
        sender : GattLocalCharacteristic
            The object representation of the gatt characteristic whose value we
            should write to
        args : GattWriteRequestedEventArgs
            The event arguments for the write request
        """

        deferral: Deferral = args.get_deferral()
        request: GattWriteRequest

        async def f():
            nonlocal args
            nonlocal request
            request = await args.get_request_async()

        asyncio.new_event_loop().run_until_complete(f())
        logger.debug("Request value: {}".format(request.value))
        reader: DataReader = DataReader.from_buffer(request.value)
        n_bytes: int = reader.unconsumed_buffer_length
        value: bytearray = bytearray()
        for n in range(0, n_bytes):
            next_byte: int = reader.read_byte()
            value.append(next_byte)

        logger.debug("Written Value: {}".format(value))
        self.write_request(str(sender.uuid), value)

        if request.option == GattWriteOption.WRITE_WITH_RESPONSE:
            request.respond()

        logger.debug("Write Complete")
        deferral.complete()

    def subscribe_characteristic(self, sender: GattLocalCharacteristic, args: Any):
        """
        Called when a characteristic is subscribed to

        Parameters
        ----------
        sender : GattLocalCharacteristic
            The characteristic object associated with the characteristic to
            which the device would like to subscribe
        args : Object
            Additional arguments to use for the subscription
        """
        self._subscribed_clients = list(sender.subscribed_clients)
        logger.info("New device subscribed")
