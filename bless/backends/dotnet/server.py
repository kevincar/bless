import logging

from uuid import UUID
from threading import Event
from asyncio.events import AbstractEventLoop
from typing import Dict, Optional, List

from bleak.backends.dotnet.utils import BleakDataWriter  # type: ignore

from bless.backends.server import BaseBlessServer  # type: ignore
from bless.backends.characteristic import (  # type: ignore
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)
from bless.backends.dotnet.service import BlessGATTServiceDotNet
from bless.backends.dotnet.characteristic import (  # type: ignore
    BlessGATTCharacteristicDotNet,
)
from bless.backends.dotnet.utils import sync_async_wrap  # type: ignore

# CLR imports
# Import of Bleak CLR->UWP Bridge.
# from BleakBridge import Bridge

# Import of other CLR components needed.
from Windows.Foundation import Deferral  # type: ignore

from Windows.Storage.Streams import DataReader, DataWriter  # type: ignore

from Windows.Devices.Bluetooth.GenericAttributeProfile import (  # type: ignore
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

from System import Guid, Object  # type: ignore

logger = logging.getLogger(__name__)


class Request:
    def __init__(self):
        self._obj = None


class BlessServerDotNet(BaseBlessServer):
    """
    DotNet Implementation of BlessServer

    Attributes
    ----------
    name : str
        The name of the server to advertise
    services : Dict[str, BlessGATTServiceDotNet]
        A dictionary of services to be advertised by this server
    """

    def __init__(self, name: str, loop: AbstractEventLoop = None, **kwargs):
        super(BlessServerDotNet, self).__init__(loop=loop, **kwargs)

        self.name: str = name
        self.services: Dict[str, BlessGATTServiceDotNet] = {}

        self._service_provider: Optional[GattServiceProvider] = None
        self._subscribed_clients: List[GattSubscribedClient] = []

        self._advertising: bool = False
        self._advertising_started: Event = Event()

    async def start(self, **kwargs):
        """
        Start the server

        Parameters
        ----------
        timeout : float
            Floating point decimal in seconds for how long to wait for the
            on-board bluetooth module to power on
        """

        adv_parameters: GattServiceProviderAdvertisingParameters = (
            GattServiceProviderAdvertisingParameters()
        )
        adv_parameters.IsDiscoverable = True
        adv_parameters.IsConnectable = True

        for uuid, service in self.services.items():
            service.service_provider.StartAdvertising(adv_parameters)
        self._advertising = True
        self._advertising_started.wait()

    async def stop(self):
        """
        Stop the server
        """
        for uuid, service in self.services.items():
            service.service_provider.StopAdvertising()
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
        all_services_advertising: bool = True
        for uuid, service in self.services.items():
            service_is_advertising: bool = (
                service.service_provider.AdvertisementStatus == 2
            )
            all_services_advertising = (
                all_services_advertising and service_is_advertising
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
        if args.Status == 2:
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
        service: BlessGATTServiceDotNet = BlessGATTServiceDotNet(uuid)
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

        serverguid: Guid = Guid.Parse(service_uuid)
        service: BlessGATTServiceDotNet = self.services[str(serverguid)]
        characteristic: BlessGATTCharacteristicDotNet = BlessGATTCharacteristicDotNet(
            char_uuid, properties, permissions, value
        )
        await characteristic.init(service)
        characteristic.obj.ReadRequested += self.read_characteristic
        characteristic.obj.WriteRequested += self.write_characteristic
        characteristic.obj.SubscribedClientsChanged += self.subscribe_characteristic
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
        service: Optional[BlessGATTServiceDotNet] = self.get_service(service_uuid)
        if service is None:
            return False
        characteristic: BlessGATTCharacteristicDotNet = service.get_characteristic(
            char_uuid
        )
        value: bytes = characteristic.value
        value = value if value is not None else b"\x00"
        with BleakDataWriter(value) as writer:
            characteristic.obj.NotifyValueAsync(writer.detach_buffer())

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
        deferral: Deferral = args.GetDeferral()
        value: bytearray = self.read_request(str(sender.Uuid))
        logger.debug(f"Current Characteristic value {value}")
        value = value if value is not None else b"\x00"
        writer: DataWriter = DataWriter()
        writer.WriteBytes(value)
        logger.debug("Getting request object {}".format(self))
        request: GattReadRequest = sync_async_wrap(
            GattReadRequest, args.GetRequestAsync
        )
        logger.debug("Got request object {}".format(request))
        request.RespondWithValue(writer.DetachBuffer())
        deferral.Complete()

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

        deferral: Deferral = args.GetDeferral()
        request: GattWriteRequest = sync_async_wrap(
            GattWriteRequest, args.GetRequestAsync
        )
        logger.debug("Request value: {}".format(request.Value))
        reader: DataReader = DataReader.FromBuffer(request.Value)
        n_bytes: int = reader.UnconsumedBufferLength
        value: bytearray = bytearray()
        for n in range(0, n_bytes):
            next_byte: int = reader.ReadByte()
            value.append(next_byte)

        logger.debug("Written Value: {}".format(value))
        self.write_request(str(sender.Uuid), value)

        if request.Option == GattWriteOption.WriteWithResponse:
            request.Respond()

        logger.debug("Write Complete")
        deferral.Complete()

    def subscribe_characteristic(self, sender: GattLocalCharacteristic, args: Object):
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
        self._subscribed_clients = list(sender.SubscribedClients)
        logger.info("New device subscribed")
