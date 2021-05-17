from uuid import UUID
from typing import Union, Optional, List, Dict, TYPE_CHECKING

from bleak.backends.bluezdbus.characteristic import (  # type: ignore
    _GattCharacteristicsFlagsEnum,
    BleakGATTCharacteristicBlueZDBus,
)

if TYPE_CHECKING:
    from bless.backends.bluezdbus.service import BlessGATTServiceBlueZDBus

from bless.backends.characteristic import (
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)

from bless.backends.bluezdbus.dbus.characteristic import Flags, BlueZGattCharacteristic


class BlessGATTCharacteristicBlueZDBus(
    BlessGATTCharacteristic, BleakGATTCharacteristicBlueZDBus
):
    """
    BlueZ implementation of the BlessGATTCharacteristic
    """

    def __init__(
        self,
        uuid: Union[str, UUID],
        properties: GATTCharacteristicProperties,
        permissions: GATTAttributePermissions,
        value: Optional[bytearray],
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
        value : Optional[bytearray]
            The binary value of the characteristic
        """
        value = value if value is not None else bytearray(b"")
        super().__init__(uuid, properties, permissions, value)
        self.value = value

    async def init(self, service: "BlessGATTServiceBlueZDBus"):
        """
        Initialize the BlueZGattCharacteristic object

        Parameters
        ----------
        service : BlessGATTService
            The service to assign the characteristic to
        """
        flags: List[Flags] = flags_to_dbus(self._properties)

        # Add to our BlueZDBus app
        gatt_char: BlueZGattCharacteristic = await service.gatt.add_characteristic(
            self._uuid, flags, self.value
        )
        dict_obj: Dict = await gatt_char.get_obj()

        # Add a Bleak Characteristic properties
        self.gatt = gatt_char
        super(BlessGATTCharacteristic, self).__init__(
            dict_obj, gatt_char.path, service.uuid
        )

    @property
    def value(self) -> bytearray:
        """Get the value of the characteristic"""
        return bytearray(self._value)

    @value.setter
    def value(self, val: bytearray):
        """Set the value of the characteristic"""
        self._value = val


def flags_to_dbus(flags: GATTCharacteristicProperties) -> List[Flags]:
    """
    Convert Bleak/Bless flags

    Parameters
    ----------
    flags : GATTCharacteristicProperties
        The numerical enumeration for the combined flags

    Returns
    -------
    List[Flags]
        A list fo Flags for use in BlueZDBus
    """
    result: List[Flags] = []
    flag_value: int = flags.value
    for i, int_flag in enumerate(_GattCharacteristicsFlagsEnum.keys()):
        included: bool = int_flag & flag_value > 0
        if included:
            flag_enum_val: str = _GattCharacteristicsFlagsEnum[int_flag]
            flag: Flags = next(
                iter(
                    [
                        Flags.__members__[x]
                        for x in list(Flags.__members__)
                        if Flags.__members__[x].value == flag_enum_val
                    ]
                )
            )
            result.append(flag)

    return result
