from typing import List

from bleak.backends.bluezdbus.characteristic import (  # type: ignore
    _GattCharacteristicsFlagsEnum,
)

from bless.backends.characteristic import GATTCharacteristicProperties  # type: ignore

from bless.backends.bluezdbus.dbus.characteristic import Flags


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
