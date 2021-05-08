import abc

from enum import Flag
from uuid import UUID
from typing import Union, cast

from bleak.backends.characteristic import BleakGATTCharacteristic  # type: ignore

from bless.backends.service import BlessGATTService


class GATTCharacteristicProperties(Flag):
    broadcast = 0x0001
    read = 0x0002
    write_without_response = 0x0004
    write = 0x0008
    notify = 0x0010
    indicate = 0x0020
    authenticated_signed_writes = 0x0040
    extended_properties = 0x0080
    reliable_write = 0x0100
    writable_auxiliaries = 0x0200


class GATTAttributePermissions(Flag):
    readable = 0x1
    writeable = 0x2
    read_encryption_required = 0x4
    write_encryption_required = 0x8


class BlessGATTCharacteristic(BleakGATTCharacteristic):
    """
    Extension of the BleakGATTCharacteristic to allow for writeable values
    """

    def __init__(
        self,
        uuid: Union[str, UUID],
        properties: GATTCharacteristicProperties,
        permissions: GATTAttributePermissions,
    ):
        """
        Instantiates a new GATT Characteristic but is not yet assigned to any
        service or application

        Parameters
        ----------
        uuid : Union[str, UUID]
            The string representation of the universal unique identifier for
            the characteristic or the actual UUID object
        properties : GATTCharacteristicProperties
            The properties that define the characteristics behavior
        permissions : GATTAttributePermissions
            Permissions that define the protection levels of the properties
        """
        if type(uuid) is str:
            uuid_str: str = cast(str, uuid)
            uuid = UUID(uuid_str)
        self.__uuid: str = str(uuid)
        self.__properties: GATTCharacteristicProperties = properties
        self.__permissions: GATTAttributePermissions = permissions

    def __str__(self):
        """
        String output of this characteristic
        """
        return f"{self.uuid}: {self.description}"

    @abc.abstractmethod
    def init(service: BlessGATTService):
        """
        Initializes the backend-specific characteristic object and stores it in
        self.obj

        Parameters
        ----------
        service : BlessGATTService
        """

    @property  # type: ignore
    @abc.abstractmethod
    def value(self) -> bytearray:
        """Value of this characteristic"""
        raise NotImplementedError()

    @value.setter  # type: ignore
    @abc.abstractmethod
    def value(self, val: bytearray):
        """Set the value of this characteristic"""
        raise NotImplementedError
