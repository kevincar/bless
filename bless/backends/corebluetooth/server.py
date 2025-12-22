import logging

from uuid import UUID
from typing import Optional, List, cast

from asyncio import TimeoutError
from asyncio.events import AbstractEventLoop

from CoreBluetooth import (  # type: ignore
    CBService,
    CBPeripheralManager,
    CBMutableCharacteristic,
    CBMutableDescriptor,
    CBAdvertisementDataLocalNameKey,
    CBAdvertisementDataServiceUUIDsKey,
)

from bleak.backends.service import BleakGATTService  # type: ignore

from .peripheral_manager_delegate import PeripheralManagerDelegate  # type: ignore
from bless.backends.server import BaseBlessServer  # type: ignore
from bless.backends.corebluetooth.service import BlessGATTServiceCoreBluetooth
from bless.backends.corebluetooth.characteristic import (  # type: ignore
    BlessGATTCharacteristicCoreBluetooth,
)
from bless.backends.corebluetooth.descriptor import (  # type: ignore
    BlessGATTDescriptorCoreBluetooth
)

from bless.backends.descriptor import (  # type: ignore
    GATTDescriptorProperties,
)

from bless.backends.attribute import (
    GATTAttributePermissions,
)
from bless.backends.characteristic import (
    GATTCharacteristicProperties,
)


logger = logging.getLogger(name=__name__)


class BlessServerCoreBluetooth(BaseBlessServer):
    """
    CoreBluetooth Implementation of BlessServer

    This implementation essentially wraps the PeripheralManagerDelegate Class
    from CoreBluetooth

    Attributes
    ----------
    name : str
        The name of the server to advertise
    services : BleakGATTServiceCollection
        A collection of services to be advertised by this server
    peripheral_manager_delegate : PeripheralManagerDelegate
        The delegated class to manage this peripheral device
    """

    def __init__(self, name: str, loop: Optional[AbstractEventLoop] = None, **kwargs):
        super(BlessServerCoreBluetooth, self).__init__(loop=loop, **kwargs)

        self.name: str = name

        self.peripheral_manager_delegate: PeripheralManagerDelegate = (
            PeripheralManagerDelegate.alloc().init()
        )
        self.peripheral_manager_delegate.read_request_func = self.read_request
        self.peripheral_manager_delegate.write_request_func = self.write_request

    async def start(
        self, timeout: float = 10, prioritize_local_name: bool = True, **kwargs
    ):
        """
        Start the server

        Parameters
        ----------
        timeout : float
            Floating point decimal in seconds for how long to wait for the
            on-board bluetooth module to power on
        prioritize_local_name : bool
            CoreBluetooth only allows a limited amount of 28 bytes of
            advertisement data, this makes it difficult to advertise long local
            names associated with BLE applications. When true, the name of the
            server is prioritized over service UUIDs, and will automatrically
            be truncated if longer than 28 bytes.
        """
        for service_uuid in self.services:
            bleak_service: BleakGATTService = self.services[service_uuid]
            service_obj: CBService = bleak_service.obj
            logger.debug("Adding service: {}".format(bleak_service.uuid))
            await self.peripheral_manager_delegate.add_service(service_obj)

        advertisement_uuids: List
        if (prioritize_local_name) and len(self.name) > 10:
            advertisement_uuids = []
        else:
            advertisement_uuids = list(
                map(lambda x: self.services[x].obj.UUID(), self.services)
            )

        advertisement_data = {
            CBAdvertisementDataLocalNameKey: self.name,
            CBAdvertisementDataServiceUUIDsKey: advertisement_uuids,
        }
        logger.debug("Advertisement Data: {}".format(advertisement_data))
        try:
            await self.peripheral_manager_delegate.start_advertising(advertisement_data)
        except TimeoutError:
            # If advertising fails as a result of bluetooth module power
            # cycling or advertisement failure, attempt to start again
            await self.start()

        logger.debug("Advertising...")

    async def stop(self):
        """
        Stop the server
        """
        await self.peripheral_manager_delegate.stop_advertising()

    async def is_connected(self) -> bool:
        """
        Determine whether there are any connected central devices

        Returns
        -------
        bool
            True if there are central devices that are connected
        """
        n_subscriptions = len(self.peripheral_manager_delegate._central_subscriptions)
        return n_subscriptions > 0

    async def is_advertising(self) -> bool:
        """
        Determine whether the service is advertising

        Returns
        -------
        bool
            True if advertising
        """
        return self.peripheral_manager_delegate.is_advertising() == 1

    async def add_new_service(self, uuid: str):
        """
        Add a service and all it's characteristics to be advertised

        Parameters
        ----------
        uuid : str
            The string representation of the UUID of the service to be added
        """
        logger.debug("Creating a new service with uuid: {}".format(uuid))
        service: BlessGATTServiceCoreBluetooth = BlessGATTServiceCoreBluetooth(uuid)
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
        service_uuid: str
            The string representation of the UUID for the service associated
            with the characteristic to be added
        char_uuid : str
            The string representation of the UUID for the characteristic to be
            added
        properties : GATTCharacteristicProperties
            The flags for the characteristic
        value : Optional[bytearray]
            The initial value for the characteristic
        permissions : GATTAttributePermissions
            The permissions for the characteristic
        """
        service_uuid = str(UUID(service_uuid))
        logger.debug("Creating a new characteristic with uuid: {}".format(char_uuid))
        characteristic: BlessGATTCharacteristicCoreBluetooth = (
            BlessGATTCharacteristicCoreBluetooth(
                char_uuid, properties, permissions, value
            )
        )

        service: BlessGATTServiceCoreBluetooth = cast(
            BlessGATTServiceCoreBluetooth, self.services[service_uuid]
        )
        await characteristic.init(service)

        service.add_characteristic(characteristic)
        characteristics: List[CBMutableCharacteristic] = [
            characteristic.obj for characteristic in service.characteristics
        ]
        service.obj.setCharacteristics_(characteristics)

    async def add_new_descriptor(
        self,
        service_uuid: str,
        char_uuid: str,
        descriptor_uuid: str,
        properties: GATTDescriptorProperties,
        value: Optional[bytearray],
        permissions: GATTAttributePermissions,
    ):
        logger.debug("Creating a new descriptor with uuid: {}".format(descriptor_uuid))
        descriptor: BlessGATTDescriptorCoreBluetooth = BlessGATTDescriptorCoreBluetooth(
            descriptor_uuid, properties, permissions, value
        )

        characteristic: BlessGATTCharacteristicCoreBluetooth = cast(
            BlessGATTCharacteristicCoreBluetooth, self.get_characteristic(char_uuid)
        )
        await descriptor.init(characteristic)

        characteristic.add_descriptor(descriptor)
        descriptors: List[CBMutableDescriptor] = [
            descriptor.obj for descriptor in characteristic.descriptors
        ]
        characteristic.obj.setDescriptors_(descriptors)

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
        characteristic: BlessGATTCharacteristicCoreBluetooth = cast(
            BlessGATTCharacteristicCoreBluetooth, self.get_characteristic(char_uuid)
        )

        value: bytes = characteristic.value
        value = value if value is not None else b"\x00"
        peripheral_manager: CBPeripheralManager = (
            self.peripheral_manager_delegate.peripheral_manager
        )
        result: bool = (
            peripheral_manager.updateValue_forCharacteristic_onSubscribedCentrals_(
                value, characteristic.obj, None
            )
        )

        return result
