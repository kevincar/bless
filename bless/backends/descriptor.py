import abc

from enum import Flag
from uuid import UUID
from typing import Union, Optional, cast, TYPE_CHECKING

from bleak.backends.descriptor import BleakGATTDescriptor  # type: ignore

from .attribute import GATTAttributePermissions

if TYPE_CHECKING:
    from bless.backends.characteristic import BlessGATTCharacteristic


class GATTDescriptorProperties(Flag):
    read = 0x0001
    write = 0x0002
    # encrypt_read = 0x0004
    # encrypt_write = 0x0008
    # encrypt_authenticated_read = 0x0010
    # encrypt_authenticated_write = 0x0020
    # secure_read = 0x0040
    # secure_write = 0x0080
    # authorize = 0x0100


class BlessGATTDescriptor(BleakGATTDescriptor):
    """
    Extension of the BleakGATTDescriptor to allow for writeable values
    """

    def __init__(
        self,
        uuid: Union[str, UUID],
        properties: GATTDescriptorProperties,
        permissions: GATTAttributePermissions,
        value: Optional[bytearray]
    ):
        """
        Instantiates a new GATT Descriptor but is not yet assigned to any
        characteristic or application

        Parameters
        ----------
        uuid : Union[str, UUID]
            The string representation of the universal unique identifier for
            the descriptor or the actual UUID object
        properties : GATTDescriptorProperties
            The properties that define the descriptors behavior
        permissions : GATTAttributePermissions
            Permissions that define the protection levels of the properties
        value : Optional[bytearray]
            The binary value of the descriptor
        """
        if type(uuid) is str:
            uuid_str: str = cast(str, uuid)
            uuid = UUID(uuid_str)
        self._uuid: str = str(uuid)
        self._properties: GATTDescriptorProperties = properties
        self._permissions: GATTAttributePermissions = permissions
        self._initial_value: Optional[bytearray] = value

    def __str__(self):
        """
        String output of this descriptor
        """
        return f"{self.uuid}: {self.description}"

    @abc.abstractmethod
    async def init(self, characteristic: "BlessGATTCharacteristic"):
        """
        Initializes the backend-specific descriptor object and stores it in
        self.obj
        """
        raise NotImplementedError()

    @property  # type: ignore
    @abc.abstractmethod
    def value(self) -> bytearray:
        """Value of this descriptor"""
        raise NotImplementedError()

    @value.setter  # type: ignore
    @abc.abstractmethod
    def value(self, val: bytearray):
        """Set the value of this descriptor"""
        raise NotImplementedError()
