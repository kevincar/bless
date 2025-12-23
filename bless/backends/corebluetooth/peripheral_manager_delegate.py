import objc  # type: ignore
import asyncio
import logging
import threading

from typing import Callable, Dict, Any, List, Optional
from Foundation import NSObject, NSError  # type: ignore
from CoreBluetooth import (  # type: ignore
    CBService,
    CBCentral,
    CBATTRequest,
    CBCharacteristic,
    CBMutableService,
    CBPeripheralManager,
    CBATTErrorSuccess,
    CBManagerStateUnknown,
    CBManagerStateResetting,
    CBManagerStateUnsupported,
    CBManagerStateUnauthorized,
    CBManagerStatePoweredOff,
    CBManagerStatePoweredOn,
    CBAdvertisementDataLocalNameKey,
    CBAdvertisementDataServiceUUIDsKey,
)

from libdispatch import dispatch_queue_create, DISPATCH_QUEUE_SERIAL  # type: ignore

LOGGER = logging.getLogger(name=__name__)
CBPeripheralManagerDelegate = objc.protocolNamed("CBPeripheralManagerDelegate")


class PeripheralManagerDelegate(  # type: ignore
        NSObject,
        protocols=[CBPeripheralManagerDelegate]
        ):
    def init(self: "PeripheralManagerDelegate"):
        self = objc.super(PeripheralManagerDelegate, self).init()

        self.event_loop: Optional[asyncio.AbstractEventLoop] = None

        self.peripheral_manager: CBPeripheralManager = (
            CBPeripheralManager.alloc().initWithDelegate_queue_(
                self, dispatch_queue_create(b"BLE", DISPATCH_QUEUE_SERIAL)
            )
        )

        self._callbacks: Dict[str, Callable] = {}

        # Events
        self._powered_on_event: threading.Event = threading.Event()
        self._advertisement_started_event: asyncio.Event = asyncio.Event()
        self._services_added_events: Dict[str, asyncio.Event] = {}

        # Documentation requires that no calls be made until we can validate
        # that the bluetooth module is powered on
        self._powered_on_event.wait()

        self._central_subscriptions: Dict = {}

        if not self.compliant():
            LOGGER.warning("PeripheralManagerDelegate is not compliant")

        return self

    def _ensure_event_loop(self) -> None:
        if self.event_loop is None:
            self.event_loop = asyncio.get_running_loop()

    def _call_soon_threadsafe(self, func: Callable, *args) -> None:
        if self.event_loop is None:
            LOGGER.warning("Event loop not set; calling delegate directly")
            func(*args)
            return
        self.event_loop.call_soon_threadsafe(func, *args)

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
            CBPeripheralManagerDelegate
        )

    @objc.python_method
    async def start_advertising(
        self, advertisement_data: Dict[str, Any], timeout: float = 2.0
    ):
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

        len_local_name: int = len(
            advertisement_data.get(CBAdvertisementDataLocalNameKey, "")
        )
        num_uuids: int = len(
            advertisement_data.get(CBAdvertisementDataServiceUUIDsKey, [])
        )
        LOGGER.debug(f"len_local_name: {len_local_name}")
        LOGGER.debug(f"num_uuids: {num_uuids}")
        if len_local_name:
            if num_uuids > 0:
                if len_local_name >= 10:
                    LOGGER.warning(
                        "The local name of your BLE application "
                        + "may not be transmitted appropriately because it is longer "
                        + "than the available space. Either remove the UUIDs being "
                        + "advertised or shorten the local name to less than 10 "
                        + "characters."
                    )
            else:
                if len_local_name >= 28:
                    LOGGER.warning(
                        "The local name of your BLE application "
                        + "may not be transmitted appropriately because it is longer "
                        + "than the available space. Consider advertised shortening "
                        + "the local name to less than 28 characters."
                    )

        self._ensure_event_loop()
        self.peripheral_manager.startAdvertising_(advertisement_data)

        await asyncio.wait_for(self._advertisement_started_event.wait(), timeout)

        LOGGER.debug(
            "Advertising started with the following data: {}".format(advertisement_data)
        )

    @objc.python_method
    async def stop_advertising(self):
        """
        Stop Advertising
        """
        self.peripheral_manager.stopAdvertising()

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
    async def add_service(self, service: CBMutableService):
        """
        Add a service to the peripheral
        Parameters
        ----------
        service : CBMutableService
            The service to be added to the server
        """
        self._ensure_event_loop()
        uuid: str = service.UUID().UUIDString()
        self._services_added_events[uuid] = asyncio.Event()

        self.peripheral_manager.addService_(service)

        await self._services_added_events[uuid].wait()

    # Protocol Functions for CBPeripheralManagerDelegate

    @objc.python_method
    def peripheralManager_didAddService_error(  # noqa: N802
        self,
        peripheral_manager: CBPeripheralManager,
        service: CBService,
        error: NSError,
    ):
        uuid: str = service.UUID().UUIDString()
        if error:
            raise Exception("Failed to add service {}: {}".format(uuid, error))

        LOGGER.debug("Peripheral manager did add service: {}".format(uuid))
        LOGGER.debug(
            "service added had characteristics: {}".format(service.characteristics())
        )
        self._services_added_events[uuid].set()

    def peripheralManager_didAddService_error_(  # noqa: N802
        self,
        peripheral_manager: CBPeripheralManager,
        service: CBService,
        error: NSError,
    ):
        self._call_soon_threadsafe(
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
            raise Exception("Failed to start advertising: {}".format(error))

        LOGGER.debug("Peripheral manager did start advertising")
        self._advertisement_started_event.set()

    def peripheralManagerDidStartAdvertising_error_(  # noqa: N802
        self, peripheral_manager: CBPeripheralManager, error: NSError
    ):
        LOGGER.debug("Received DidStartAdvertising Message")
        self._call_soon_threadsafe(
            self.peripheralManagerDidStartAdvertising_error, peripheral_manager, error
        )

    def peripheralManagerDidUpdateState_(  # noqa: N802
        self, peripheral_manager: CBPeripheralManager
    ):
        if peripheral_manager.state() == CBManagerStateUnknown:
            LOGGER.debug("Cannot detect bluetooth device")
        elif peripheral_manager.state() == CBManagerStateResetting:
            LOGGER.debug("Bluetooth is resetting")
        elif peripheral_manager.state() == CBManagerStateUnsupported:
            LOGGER.debug("Bluetooth is unsupported")
        elif peripheral_manager.state() == CBManagerStateUnauthorized:
            LOGGER.debug("Bluetooth is unauthorized")
        elif peripheral_manager.state() == CBManagerStatePoweredOff:
            LOGGER.debug("Bluetooth powered off")
        elif peripheral_manager.state() == CBManagerStatePoweredOn:
            LOGGER.debug("Bluetooth powered on")

        if peripheral_manager.state() == CBManagerStatePoweredOn:
            self._powered_on_event.set()
        else:
            self._powered_on_event.clear()
            self._advertisement_started_event.clear()

    def peripheralManager_willRestoreState_(  # noqa: N802
        self, peripheral: CBPeripheralManager, d: dict
    ):
        LOGGER.debug("PeripheralManager restoring state: {}".format(d))

    def peripheralManager_central_didSubscribeToCharacteristic_(  # noqa: N802
        self,
        peripheral_manager: CBPeripheralManager,
        central: CBCentral,
        characteristic: CBCharacteristic,
    ):
        central_uuid: str = central.identifier().UUIDString()
        char_uuid: str = characteristic.UUID().UUIDString()
        LOGGER.debug(
            "Central Device: {} is subscribing to characteristic {}".format(
                central_uuid, char_uuid
            )
        )
        if central_uuid in self._central_subscriptions:
            subscriptions = self._central_subscriptions[central_uuid]
            if char_uuid not in subscriptions:
                self._central_subscriptions[central_uuid].append(char_uuid)
            else:
                LOGGER.debug(
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
        LOGGER.debug(
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
        LOGGER.debug("Peripheral is ready to update subscribers")

    def peripheralManager_didReceiveReadRequest_(  # noqa: N802
        self, peripheral_manager: CBPeripheralManager, request: CBATTRequest
    ):
        # This should probably be a callback to be handled by the user, to be
        # implemented or given to the BleakServer
        LOGGER.debug(
            "Received read request from {} for characteristic {}".format(
                request.central().identifier().UUIDString(),
                request.characteristic().UUID().UUIDString(),
            )
        )
        request.setValue_(
            self.read_request_func(request.characteristic().UUID().UUIDString())
        )
        peripheral_manager.respondToRequest_withResult_(request, CBATTErrorSuccess)

    def peripheralManager_didReceiveWriteRequests_(  # noqa: N802
        self, peripheral_manager: CBPeripheralManager, requests: List[CBATTRequest]
    ):
        # Again, this should likely be moved to a callback
        LOGGER.debug("Receving write requests...")
        for request in requests:
            central: CBCentral = request.central()
            char: CBCharacteristic = request.characteristic()
            value: bytearray = request.value()
            LOGGER.debug(
                "Write request from {} to {} with value {}".format(
                    central.identifier().UUIDString(), char.UUID().UUIDString(), value
                )
            )
            self.write_request_func(char.UUID().UUIDString(), value)

        peripheral_manager.respondToRequest_withResult_(requests[0], CBATTErrorSuccess)
