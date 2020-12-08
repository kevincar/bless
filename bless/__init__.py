# type: ignore
import sys

if sys.platform == 'darwin':

    # Server
    from bless.backends.corebluetooth.server import (  # noqa: F401
            BlessServerCoreBluetooth as BlessServer
            )

    # Characteristic Classes
    from bless.backends.corebluetooth.characteristic import (  # noqa: F401
            BlessGATTCharacteristicCoreBluetooth
            as BlessGATTCharacteristic
            )
elif sys.platform == 'linux':

    # Server
    from bless.backends.bluezdbus.server import (  # noqa: F401
            BlessServerBlueZDBus as BlessServer
            )

# type: ignore
from bless.backends.characteristic import (  # noqa: E402 F401
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
