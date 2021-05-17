import objc  # type: ignore
import logging
import asyncio

from typing import Any, Dict, List, Optional, Callable


from CoreBluetooth import (  # type: ignore
    CBManagerStateUnknown,
    CBManagerStateResetting,
    CBManagerStateUnsupported,
    CBManagerStateUnauthorized,
    CBManagerStatePoweredOff,
    CBManagerStatePoweredOn,
)

from Foundation import (  # type: ignore
    NSObject,
    CBPeripheralManager,
    CBCentral,
    CBMutableService,
    CBService,
    CBCharacteristic,
    CBATTRequest,
    NSError,
)

from libdispatch import dispatch_queue_create, DISPATCH_QUEUE_SERIAL  # type: ignore

from bless.exceptions import BlessError
from bless.backends.corebluetooth.error import CBATTError  # type: ignore


logger = logging.getLogger(name=__name__)


class PeripheralManagerDelegate(NSObject):
    """
    This class will conform to the CBPeripheralManagerDelegate protocol to
    manage messages passed from the owning PeripheralManager class

    Attributes
    ----------
    event_loop : asyncio.AbstractEventLoop
        The event loop on which this class handles its messaging
    peripheral_manager : CBPeripheralManager
        The class that handles the on-board bluetooth device in a peripheral
        role

    """

    CBPeripheralManagerDelegate = objc.protocolNamed("CBPeripheralManagerDelegate")
    ___pyobjc_protocols__ = [CBPeripheralManagerDelegate]

    def init(self):
        """macOS init function for NSObjects"""
        self = objc.super(PeripheralManagerDelegate, self).init()

        self.event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

        self.peripheral_manager: CBPeripheralManager = (
            CBPeripheralManager.alloc().initWithDelegate_queue_(
                self,
                dispatch_queue_create(b"bleak.corebluetooth", DISPATCH_QUEUE_SERIAL),
            )
        )

        self._callbacks: Dict[str, Callable] = {}

        # Events
        self._powered_on_event: asyncio.Event = asyncio.Event()
        self._advertisement_started_event: asyncio.Event = asyncio.Event()
        self._services_added_events: Dict[str, asyncio.Event] = {}

        self._central_subscriptions = {}

        if not self.compliant():
            logger.warning("PeripheralManagerDelegate is not compliant")

        return self

    # User defined functions

    def compliant(self) -> bool:
        """
        Determines whether the class adheres to the CBPeripheralManagerDelegate
        protocol

        Returns
        -------
        bool
            Whether the class is compliant with the CBPeripheralManagerDelegate
            Protocol
        """
        return PeripheralManagerDelegate.pyobjc_classMethods.conformsToProtocol_(
            self.CBPeripheralManagerDelegate
        )

    @objc.python_method
    async def wait_for_powered_on(self, timeout: float):
        """
        Wait for ready state of the peripheralManager

        Parameters
        ----------
        timeout : float
            How long to wait for the powered on event
        """
        await asyncio.wait_for(self._powered_on_event.wait(), timeout)

    def is_connected(self) -> bool:
        """
        Determin whether any centrals have subscribed

        Returns
        -------
        bool
            True if other devices have subscribed to services
        """

        n_subscriptions = len(self._central_subscriptions)
        return n_subscriptions > 0

    def is_advertising(self) -> bool:
        """
        Determin whether the server is advertising

        Returns
        -------
        bool
            True if advertising
        """
        return self.peripheral_manager.isAdvertising()

    @objc.python_method
    async def addService(self, service: CBMutableService):  # noqa
        """
        Add a service to the peripheral

        Parameters
        ----------
        service : CBMutableService
            The service to be added to the server
        """
        uuid: str = service.UUID().UUIDString()
        self._services_added_events[uuid] = asyncio.Event()

        self.peripheral_manager.addService_(service)

        await self._services_added_events[uuid].wait()

    async def startAdvertising_(
        self, advertisement_data: Dict[str, Any], timeout: float = 2.0
    ):  # noqa
        """
        Begin Advertising on the server

        Parameters
        ----------
        advertisement_data : Dict[str, Any]
            Dictionary of additional data to advertise. See Apple Documentation
            for more info
        timeout : float
            How long to wait before throwing an error if advertising doesn't
            start
        """

        self.peripheral_manager.startAdvertising_(advertisement_data)

        await asyncio.wait_for(self._advertisement_started_event.wait(), timeout)

        logger.debug(
            "Advertising started with the following data: {}".format(advertisement_data)
        )

    async def stopAdvertising(self):  # noqa
        """
        Stop Advertising
        """
        self.peripheral_manager.stopAdvertising()

    @property
    def read_request_func(self) -> Callable:
        """
        Returns an instance to the function for handing read requests
        """
        func: Optional[Callable[[Any], Any]] = self._callbacks.get("read")
        if func is not None:
            return func
        else:
            raise BlessError("read request function undefined")

    @read_request_func.setter
    def read_request_func(self, func: Callable):
        """
        Sets the callback to handle read requests
        """
        self._callbacks["read"] = func

    @property
    def write_request_func(self) -> Callable:
        """
        Returns an instance to the function for handling write requests
        """
        func: Optional[Callable[[Any], Any]] = self._callbacks.get("write")
        if func is not None:
            return func
        else:
            raise BlessError("write request func is undefined")

    @write_request_func.setter
    def write_request_func(self, func: Callable):
        """
        Sets the callback to handle write requests
        """
        self._callbacks["write"] = func

    # Protocol functions

    @objc.python_method
    def did_update_state(self, peripheral_manager: CBPeripheralManager):
        if peripheral_manager.state() == CBManagerStateUnknown:
            logger.debug("Cannot detect bluetooth device")
        elif peripheral_manager.state() == CBManagerStateResetting:
            logger.debug("Bluetooth is resetting")
        elif peripheral_manager.state() == CBManagerStateUnsupported:
            logger.debug("Bluetooth is unsupported")
        elif peripheral_manager.state() == CBManagerStateUnauthorized:
            logger.debug("Bluetooth is unauthorized")
        elif peripheral_manager.state() == CBManagerStatePoweredOff:
            logger.debug("Bluetooth powered off")
        elif peripheral_manager.state() == CBManagerStatePoweredOn:
            logger.debug("Bluetooth powered on")

        if peripheral_manager.state() == CBManagerStatePoweredOn:
            self._powered_on_event.set()
        else:
            self._powered_on_event.clear()
            self._advertisement_started_event.clear()

    def peripheralManagerDidUpdateState_(  # noqa: N802
        self, peripheral_manager: CBPeripheralManager
    ):
        self.event_loop.call_soon_threadsafe(self.did_update_state, peripheral_manager)

    def peripheralManager_willRestoreState_(  # noqa: N802
        self, peripheral: CBPeripheralManager, d: dict
    ):
        logger.debug("PeripheralManager restoring state: {}".format(d))

    @objc.python_method
    def peripheralManager_didAddService_error(  # noqa: N802
        self,
        peripheral_manager: CBPeripheralManager,
        service: CBService,
        error: NSError,
    ):
        uuid: str = service.UUID().UUIDString()
        if error:
            raise BlessError("Failed to add service {}: {}".format(uuid, error))

        logger.debug("Peripheral manager did add service: {}".format(uuid))
        logger.debug(
            "service added had characteristics: {}".format(service.characteristics())
        )
        self._services_added_events[uuid].set()

    def peripheralManager_didAddService_error_(  # noqa: N802
        self,
        peripheral_manager: CBPeripheralManager,
        service: CBService,
        error: NSError,
    ):
        self.event_loop.call_soon_threadsafe(
            self.peripheralManager_didAddService_error,
            peripheral_manager,
            service,
            error,
        )

    @objc.python_method
    def peripheralManagerDidStartAdvertising_error(  # noqa: N802
        self, peripheral_manager: CBPeripheralManager, error: NSError
    ):
        if error:
            raise BlessError("Failed to start advertising: {}".format(error))

        logger.debug("Peripheral manager did start advertising")
        self._advertisement_started_event.set()

    def peripheralManagerDidStartAdvertising_error_(  # noqa: N802
        self, peripheral_manager: CBPeripheralManager, error: NSError
    ):
        logger.debug("Received DidStartAdvertising Message")
        self.event_loop.call_soon_threadsafe(
            self.peripheralManagerDidStartAdvertising_error, peripheral_manager, error
        )

    def peripheralManager_central_didSubscribeToCharacteristic_(  # noqa: N802
        self,
        peripheral_manager: CBPeripheralManager,
        central: CBCentral,
        characteristic: CBCharacteristic,
    ):
        central_uuid: str = central.identifier().UUIDString()
        char_uuid: str = characteristic.UUID().UUIDString()
        logger.debug(
            "Central Device: {} is subscribing to characteristic {}".format(
                central_uuid, char_uuid
            )
        )
        if central_uuid in self._central_subscriptions:
            subscriptions = self._central_subscriptions[central_uuid]
            if char_uuid not in subscriptions:
                self._central_subscriptions[central_uuid].append(char_uuid)
            else:
                logger.debug(
                    (
                        "Central Device {} is already "
                        + "subscribed to characteristic {}"
                    ).format(central_uuid, char_uuid)
                )
        else:
            self._central_subscriptions[central_uuid] = [char_uuid]

    def peripheralManager_central_didUnsubscribeFromCharacteristic_(  # noqa: N802 E501
        self,
        peripheral_manager: CBPeripheralManager,
        central: CBCentral,
        characteristic: CBCharacteristic,
    ):
        central_uuid: str = central.identifier().UUIDString()
        char_uuid: str = characteristic.UUID().UUIDString()
        logger.debug(
            "Central device {} is unsubscribing from characteristic {}".format(
                central_uuid, char_uuid
            )
        )
        self._central_subscriptions[central_uuid].remove(char_uuid)
        if len(self._central_subscriptions[central_uuid]) < 1:
            del self._central_subscriptions[central_uuid]

    def peripheralManagerIsReadyToUpdateSubscribers_(  # noqa: N802
        self, peripheral_manager: CBPeripheralManager
    ):
        logger.debug("Peripheral is ready to update subscribers")

    def peripheralManager_didReceiveReadRequest_(  # noqa: N802
        self, peripheral_manager: CBPeripheralManager, request: CBATTRequest
    ):
        # This should probably be a callback to be handled by the user, to be
        # implemented or given to the BleakServer
        logger.debug(
            "Received read request from {} for characteristic {}".format(
                request.central().identifier().UUIDString(),
                request.characteristic().UUID().UUIDString(),
            )
        )
        request.setValue_(
            self.read_request_func(request.characteristic().UUID().UUIDString())
        )
        peripheral_manager.respondToRequest_withResult_(
            request, CBATTError.Success.value
        )

    def peripheralManager_didReceiveWriteRequests_(  # noqa: N802
        self, peripheral_manager: CBPeripheralManager, requests: List[CBATTRequest]
    ):
        # Again, this should likely be moved to a callback
        logger.debug("Receving write requests...")
        for request in requests:
            central: CBCentral = request.central()
            char: CBCharacteristic = request.characteristic()
            value: bytearray = request.value()
            logger.debug(
                "Write request from {} to {} with value {}".format(
                    central.identifier().UUIDString(), char.UUID().UUIDString(), value
                )
            )
            self.write_request_func(char.UUID().UUIDString(), value)

        peripheral_manager.respondToRequest_withResult_(
            requests[0], CBATTError.Success.value
        )
