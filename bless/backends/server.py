import abc
import asyncio
import logging

from uuid import UUID
from asyncio import AbstractEventLoop
from typing import Any, Optional, Dict, Callable, List
from bleak.backends.service import BleakGATTService  # type: ignore

from bless.backends.service import BlessGATTService
from bless.backends.characteristic import (  # type: ignore
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions
)

from bless.exceptions import BlessError

LOGGER = logging.getLogger(__name__)


class BaseBlessServer(abc.ABC):
    """
    The Server Interface for Bleak Backend

    Attributes
    ----------
    services : Optional[BleakGATTServiceCollection]
        Used to manage services and characteristics that this server advertises
    """

    def __init__(self, loop: AbstractEventLoop = None, **kwargs):
        self.loop: AbstractEventLoop = loop if loop else asyncio.get_event_loop()

        self._callbacks: Dict[str, Callable[[Any], Any]] = {}

        self.services: Dict[str, BleakGATTService] = {}

    # Async Context managers

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    # Abstract Methods

    @abc.abstractmethod
    async def start(self, **kwargs) -> bool:
        """
        Start the server

        Returns
        -------
        bool
            Whether the server started successfully
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def stop(self) -> bool:
        """
        Stop the server

        Returns
        -------
        bool
            Whether the server stopped successfully
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def is_connected(self) -> bool:
        """
        Determine whether there are any connected peripheral devices

        Returns
        -------
        bool
            Whether any peripheral devices are connected
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def is_advertising(self) -> bool:
        """
        Determine whether the server is advertising

        Returns
        -------
        bool
            True if the server is advertising
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def add_new_service(self, uuid: str):
        """
        Add a new GATT service to be hosted by the server

        Parameters
        ----------
        uuid : str
            The UUID for the service to add
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def add_new_characteristic(
        self,
        service_uuid: str,
        char_uuid: str,
        properties: GATTCharacteristicProperties,
        value: Optional[bytearray],
        permissions: GATTAttributePermissions,
    ):
        """
        Add a new characteristic to be associated with the server

        Parameters
        ----------
        service_uuid : str
            The string representation of the UUID of the GATT service to which
            this new characteristic should belong
        char_uuid : str
            The string representation of the UUID of the characteristic
        properties : GATTCharacteristicProperties
            GATT Characteristic Flags that define the characteristic
        value : Optional[bytearray]
            A byterray representation of the value to be associated with the
            characteristic. Can be None if the characteristic is writable
        permissions : GATTAttributePermissions
            GATT flags that define the permissions for the characteristic
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def update_value(self, service_uuid: str, char_uuid: str) -> bool:
        """
        Update the characteristic value. This is different than using
        characteristic.set_value. This method ensures that subscribed devices
        receive notifications, assuming the characteristic in question is
        notifyable

        Parameters
        ----------
        service_uuid : str
            The string representation of the UUID for the service associated
            with the characteristic whose value is to be updated
        char_uuid : str
            The string representation of the UUID for the characteristic whose
            value is to be updated

        Returns
        -------
        bool
            Whether the characteristic value was successfully updated
        """
        raise NotImplementedError()

    def get_service(self, uuid: str) -> Optional[BlessGATTService]:
        """
        Retrieves the service whose UUID matches the string given

        Parameters
        ----------
        uuid : str
            The String representation of the uuid for the service

        Returns
        -------
        Optional[BlessGATTService]
            The service that matches the UUID. None if not found
        """
        uuid = str(UUID(uuid))
        potential_services: List[BlessGATTService] = [
            service
            for uuid_str, service in self.services.items()
            if service.uuid == uuid
        ]

        return potential_services[0] if len(potential_services) > 0 else None

    def get_characteristic(self, uuid: str) -> Optional[BlessGATTCharacteristic]:
        """
        Retrieves the characteristic whose UUID matches the string given.

        Parameters
        ----------
        uuid : str
            The string representation of the UUID for the characteristic to
            retrieve

        Returns
        -------
        BlessGATTCharacteristic
            The characteristic object
        """
        uuid = str(UUID(uuid))
        potentials: List[BlessGATTCharacteristic] = [
            self.services[service_uuid].get_characteristic(uuid)
            for service_uuid in self.services
            if self.services[service_uuid].get_characteristic(uuid) is not None
        ]
        try:
            return potentials[0]
        except KeyError:
            return None

    async def add_gatt(self, gatt_tree: Dict):
        """
        Uses the provided dictionary add all the services and characteristics

        Parameters
        ----------
        gatt_tree : Dict
            A dictionary of services and characteristics where the keys are the
            uuids and the attributes are the properties
        """
        for service_uuid, service_info in gatt_tree.items():
            await self.add_new_service(service_uuid)
            for char_uuid, char_info in service_info.items():
                await self.add_new_characteristic(
                        service_uuid, char_uuid, char_info.get("Properties"),
                        char_info.get("value"), char_info.get("Permissions")
                        )

    def read_request(self, uuid: str) -> bytearray:
        """
        This function should be handed off to the subsequent backend bluetooth
        servers as a callback for incoming read requests on values for
        characteristics owned by our server. This function then hands off
        execution to the user-defiend callback functions

        Note: read_request_func must be defined on the class that inherits this
        base class

        Parameters
        ----------
        uuid : str
            The string representation of the UUID for the characteristic whose
            value is to be read

        Returns
        -------
        bytearray
            A bytearray value that represents the value for the characteristic
            requested
        """
        characteristic: Optional[BlessGATTCharacteristic] = self.get_characteristic(
            uuid
        )

        if not characteristic:
            raise BlessError("Invalid characteristic: {}".format(uuid))

        return self.read_request_func(characteristic)

    def write_request(self, uuid: str, value: Any):
        """
        Obtain the characteristic to write and pass on to the user-defined
        write_request_func

        Note: write_request_func must be defined on the child class
        """
        characteristic: Optional[BlessGATTCharacteristic] = self.get_characteristic(
            uuid
        )

        self.write_request_func(characteristic, value)

    @property
    def read_request_func(self) -> Callable[[Any], Any]:
        """
        Return an instance of the function to handle incoming read requests
        """
        func: Optional[Callable[[Any], Any]] = self._callbacks.get("read")
        if func is not None:
            return func
        else:
            raise BlessError("Server: Read Callback is undefined")

    @read_request_func.setter
    def read_request_func(self, func: Callable):
        """
        Set the function to handle incoming read requests
        """
        self._callbacks["read"] = func

    @property
    def write_request_func(self) -> Callable:
        """
        Return an instance of the function to handle incoming write requests
        """
        func: Optional[Callable[[Any], Any]] = self._callbacks.get("write")
        if func is not None:
            return func
        else:
            raise BlessError("Server: Write Callback is undefined")

    @write_request_func.setter
    def write_request_func(self, func: Callable):
        """
        Set the function to handle incoming write requests
        """
        self._callbacks["write"] = func

    @staticmethod
    def is_uuid(uuid: str) -> bool:
        """
        Check whether uuid is a valid uuid

        Parameters
        ----------
        uuid : str
            The string representation of the uuid to check

        Returns
        -------
        bool
            True if uuid is a valid UUID
        """
        try:
            UUID(uuid)
            return True
        except ValueError:
            return False
