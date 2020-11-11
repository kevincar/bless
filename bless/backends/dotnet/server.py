import logging
import asyncio

from asyncio.events import AbstractEventLoop
from typing import Union, Dict, Optional, List

from bleak.backends.dotnet.utils import (
        wrap_IAsyncOperation,
        BleakDataReader,
        BleakDataWriter
        )
from bleak.backends.dotnet.service import BleakGATTServiceDotNet

from bless.exceptions import BlessError
from bless.backends.server import BaseBlessServer
from bless.backends.characteristic import GattCharacteristicsFlags
from bless.backends.dotnet.characteristic import BleakGATTCharacteristicDotNet

# CLR imports
# Import of Bleak CLR->UWP Bridge.
# from BleakBridge import Bridge

# Import of other CLR components needed.
from Windows.Foundation import (
        IAsyncOperation,
        Deferral
        )

from Windows.Devices.Bluetooth.GenericAttributeProfile import (
    GattWriteOption,
    GattServiceProviderResult,
    GattServiceProvider,
    GattLocalService,
    GattLocalCharacteristicResult,
    GattLocalCharacteristic,
    GattLocalCharacteristicParameters,
    GattServiceProviderAdvertisingParameters,
    GattReadRequestedEventArgs,
    GattReadRequest,
    GattWriteRequestedEventArgs,
    GattWriteRequest,
    GattSubscribedClient
)

from System import (
        Guid,
        Object
        )

logger = logging.getLogger(__name__)


class Request():
    def __init__(self):
        self._obj = None


class BlessServerDotNet(BaseBlessServer):
    """
    DotNet Implementation of BlessServer

    Attributes
    ----------
    name : str
        The name of the server to advertise
    services : Dict[str, BleakGATTServiceDotNet]
        A dictionary of services to be advertised by this server
    """

    def __init__(self, name: str, loop: AbstractEventLoop = None, **kwargs):
        super(BlessServerDotNet, self).__init__(loop=loop, **kwargs)

        self.name: str = name
        self.services: Dict[str, BleakGATTServiceDotNet] = {}

        self._service_provider: Optional[GattServiceProvider] = None
        self._subscribed_clients: List[GattSubscribedClient] = []

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

        self.service_provider.StartAdvertising(adv_parameters)

    async def stop(self):
        """
        Stop the server
        """

        self.service_provider.StopAdvertising()

    @property
    def service_provider(self) -> GattServiceProvider:
        if self._service_provider is not None:
            return self._service_provider

        raise BlessError("DotNet Service provider has not been initialized")

    @service_provider.setter
    def service_provider(self, value: GattServiceProvider):
        self._service_provider = value

    def is_connected(self) -> bool:
        """
        Determine whether there are any connected peripheral devices

        Returns
        -------
        bool
            True if there are any central devices that have subscribed to our
            characteristics
        """
        return len(self._subscribed_clients) > 0

    def is_advertising(self) -> bool:
        """
        Determine whether the server is advertising

        Returns
        -------
        bool
            True if advertising
        """
        return self.service_provider.AdvertisementStatus == 2

    async def add_new_service(self, uuid: str):
        """
        Generate a new service to be associated with the server

        Parameters
        ----------
        uuid : str
            The string representation of the UUID of the service to be added
        """
        logger.debug("Creating a new service with uuid: {}".format(uuid))
        guid: Guid = Guid.Parse(uuid)
        spr: GattServiceProviderResult = await wrap_IAsyncOperation(
                IAsyncOperation[GattServiceProviderResult](
                        GattServiceProvider.CreateAsync(guid)
                    ),
                return_type=GattServiceProviderResult)
        self.service_provider: GattServiceProvider = spr.ServiceProvider
        new_service: GattLocalService = self.service_provider.Service
        bleak_service = BleakGATTServiceDotNet(obj=new_service)
        logger.debug("Adding service to server with uuid {}".format(uuid))
        self.services[uuid] = bleak_service

    async def add_new_characteristic(self, service_uuid: str, char_uuid: str,
                                     properties: GattCharacteristicsFlags,
                                     value: Optional[bytearray],
                                     permissions: int):
        """
        Generate a new characteristic to be associated with the server

        Parameters
        ----------
        service_uuid : str
            The string representation of the uuid of the service to associate
            the new characteristic with
        char_uuid : str
            The string representation of the uuid of the new characteristic
        properties : GattCharacteristicsFlags
            The flags for the characteristic
        value : Optional[bytearray]
            The initial value for the characteristic
        permissions : int
            The permissions for the characteristic
        """
        charguid: Guid = Guid.Parse(char_uuid)
        serverguid: Guid = Guid.Parse(service_uuid)

        ReadParameters: GattLocalCharacteristicParameters = (
                GattLocalCharacteristicParameters()
                )
        ReadParameters.CharacteristicProperties = properties
        ReadParameters.ReadProtectionLevel = permissions

        characteristic_result: GattLocalCharacteristicResult = (
                await wrap_IAsyncOperation(
                    IAsyncOperation[GattLocalCharacteristicResult](
                        self.services.get(str(serverguid), None)
                        .obj.CreateCharacteristicAsync(
                            charguid, ReadParameters)
                        ),
                    return_type=GattLocalCharacteristicResult)
                )
        newChar: GattLocalCharacteristic = characteristic_result.Characteristic
        newChar.ReadRequested += self._read_characteristic
        newChar.WriteRequested += self._write_characteristic
        newChar.SubscribedClientsChanged += self._subscribe_characteristic
        bleak_characteristic: BleakGATTCharacteristicDotNet = (
                BleakGATTCharacteristicDotNet(obj=newChar)
                )

        service: BleakGATTServiceDotNet = self.services.get(str(serverguid))
        service.add_characteristic(bleak_characteristic)

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

        service: BleakGATTServiceDotNet = self.services[service_uuid.lower()]
        characteristic: BleakGATTCharacteristicDotNet = next(
                iter([
                    char
                    for char in service.characteristics
                    if char.uuid == char_uuid.lower()
                    ])
                )
        value: bytes = characteristic.value
        value = value if value is not None else b'\x00'
        with BleakDataWriter(value) as writer:
            characteristic.obj.NotifyValueAsync(
                    writer.detach_buffer()
                    )

        return True

    def _read_characteristic(self,
                             sender: GattLocalCharacteristic,
                             args: GattReadRequestedEventArgs):
        """
        This method, and the _write_characteristic method, both utilize the
        _get_request method.  The _get_request method, utilizes native thread
        modeling. The reason for this is that the methods used to obtain the
        GattCharacteristics require the use of coroutines.  But the service
        requires functions. We cannot give back coroutines, else these
        functions will never run. Thus, we start up a thread to temporarily get
        or set the characteristic in question.
        """

        logger.debug("Reading Characteristic")
        deferral: Deferral = args.GetDeferral()
        value: bytearray = self.read_request(str(sender.Uuid))
        value = value if value is not None else b'\x00'
        with BleakDataWriter(value) as writer:
            logger.debug(f"Current Characteristic value {value}")
            logger.debug("Getting request object {}".format(self))
            request: GattReadRequest = self._get_request(args)
            logger.debug("Got request object {}".format(request))
            request.RespondWithValue(writer.DetachBuffer())
        deferral.Complete()

    def _write_characteristic(self,
                              sender: GattLocalCharacteristic,
                              args: GattWriteRequestedEventArgs):

        deferral: Deferral = args.GetDeferral()
        request: GattWriteRequest = self._get_request(args)
        logger.debug("Request value: {}".format(request.Value))

        with BleakDataReader(request.Value) as reader:
            value: bytearray = bytearray(reader.read())
            logger.debug("Written Value: {}".format(value))
            self.write_request(str(sender.Uuid), value)

        if request.Option == GattWriteOption.WriteWithResponse:
            request.Respond()

        logger.debug("Write Complete")
        deferral.Complete()

    def _subscribe_characteristic(
            self,
            sender: GattLocalCharacteristic,
            args: Object
            ):
        self._subscribed_clients = list(sender.SubscribedClients)
        logger.info("New device subscribed")

    def _get_request(self,
                     args: Union[
                         GattReadRequestedEventArgs,
                         GattWriteRequestedEventArgs
                         ]) -> Union[
                                 GattReadRequest,
                                 GattWriteRequest
                                 ]:

        request: Request = Request()
        logger.debug("THREAD: Starting threaded event loop")
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._request_loop(args, request))
        logger.debug("THREAD: Completed request loop")
        return request._obj

    async def _request_loop(self,
                            args: Union[
                                GattReadRequestedEventArgs,
                                GattWriteRequestedEventArgs],
                            request: Request):

        loop = asyncio.get_event_loop()
        if isinstance(args, GattReadRequestedEventArgs):
            request._obj = await wrap_IAsyncOperation(
                        IAsyncOperation[GattReadRequest](
                            args.GetRequestAsync()),
                        return_type=GattReadRequest,
                        loop=loop)
        elif isinstance(args, GattWriteRequestedEventArgs):
            request._obj = await wrap_IAsyncOperation(
                        IAsyncOperation[GattWriteRequest](
                            args.GetRequestAsync()),
                        return_type=GattWriteRequest,
                        loop=loop)
