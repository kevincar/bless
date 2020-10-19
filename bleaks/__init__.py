import sys

if sys.platform == 'darwin':
    # Server
    from bleaks.backends.corebluetooth.server import BleakServerCoreBluetooth as BleakServer  # noqa: F401 E501

    # Characteristic Classes
    from bleaks.backends.corebluetooth.characteristic import (  # noqa: F401
            BleaksGATTCharacteristicCoreBluetooth
            as BleaksGATTCharacteristic
            )

from bleaks.backends.characteristic import (  # noqa: E402 F401
        GattCharacteristicsFlags,
        GATTAttributePermissions
        )


def check_test() -> bool:
    """
    Verify that testing is functional

    Returns
    -------
    bool
        Default to true
    """
    return True
