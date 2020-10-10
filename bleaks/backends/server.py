import abc
import asyncio
import logging

from asyncio import AbstractEventLoop
from typing import Any, Optional, cast
from bleak.backends.service import BleakGATTServiceCollection
from bleak.backends.characteristic import (
        BleakGATTCharacteristic,
        GattCharacteristicsFlags
        )

from bleaks.exceptions import BleaksError

LOGGER = logging.getLogger(__name__)


class BaseBleakServer(abc.ABC):
    """
    The Server Interface for Bleak Backend

    Attributes
    ----------
    services : Optional[BleakGATTServiceCollection]
        Used to manage services and characteristics that this server advertises
    """

    def __init__(self, loop: AbstractEventLoop = None, **kwargs):
        self.loop: AbstractEventLoop = (
                loop if loop else asyncio.get_event_loop()
                )

        self.services: Optional[BleakGATTServiceCollection] = None

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
    def is_connected(self) -> bool:
        """
        Determine whether there are any connected peripheral devices

        Returns
        -------
        bool
            Whether any peripheral devices are connected
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def is_advertising(self) -> bool:
        """
        Determine whether the server is advertising

        Returns
        -------
        bool
            True if the server is advertising
        """

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
            properties: GattCharacteristicsFlags,
            value: Optional[bytearray],
            permissions: int
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
        properties : GattCharacteristicsFlags
            GATT Characteristic Flags that define the characteristic
        value : Optional[bytearray]
            A byterray representation of the value to be associated with the
            characteristic. Can be None if the characteristic is writable
        permissions : int
            GATT Characteristic flags that define the permissions for the
            characteristic
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

    @abc.abstractmethod
    def read_request_func(
            self,
            characteristic: BleakGATTCharacteristic,
            ) -> bytearray:
        """
        The callback for read requests on characteristics

        Parameters
        ----------
        characteristic : BleakGATTCharacteristic
            The Characteristic object whose value is to be read

        Returns
        -------
        bytearray
            The value of the characteristic to be returned
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def write_request_func(
            self,
            characteristic: BleakGATTCharacteristic,
            value: bytearray
            ):
        """
        The callback for the write request on characteristics

        Parameters
        ----------
        characteristic : BleakGATTCharacteristic
            The charateristic object whose value is to be written
        value : bytearray
            The value to be assigned to the characteristic object
        """
        raise NotImplementedError()

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
        characteristic: BleakGATTCharacteristic = cast(
                BleakGATTServiceCollection,
                self.services
                ).get_characteristic(uuid)
        if not characteristic:
            raise BleaksError("Invalid characteristic: {}".format(uuid))

        return self.read_request_func(characteristic)

    def write_request(self, uuid: str, value: Any):
        """
        Obtain the characteristic to write and pass on to the user-defined
        write_request_func

        Note: write_request_func must be defined on the child class
        """
        characteristic: BleakGATTCharacteristic = cast(
                BleakGATTServiceCollection,
                self.services
                ).get_characteristic(uuid)
        if not characteristic:
            raise BleaksError("Invalid characteristic: {}".format(uuid))

        self.write_request_func(characteristic, value)
