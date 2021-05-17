# type: ignore
import sys

if sys.platform == "darwin":

    # Server
    from bless.backends.corebluetooth.server import (  # noqa: F401
        BlessServerCoreBluetooth as BlessServer,
    )

    # Characteristic Classes
    from bless.backends.corebluetooth.characteristic import (  # noqa: F401
        BlessGATTCharacteristicCoreBluetooth as BlessGATTCharacteristic,
    )
elif sys.platform == "linux":

    # Server
    from bless.backends.bluezdbus.server import (  # noqa: F401
        BlessServerBlueZDBus as BlessServer,
    )

    # Characteristic Classes
    from bless.backends.bluezdbus.characteristic import (  # noqa: F401
        BlessGATTCharacteristicBlueZDBus as BlessGATTCharacteristic,
    )

elif sys.platform == "win32":

    # Server
    from bless.backends.dotnet.server import (  # noqa: F401
        BlessServerDotNet as BlessServer,
    )

    # Characteristic Classes
    from bless.backends.dotnet.characteristic import (  # noqa: F401
        BlessGATTCharacteristicDotNet as BlessGATTCharacteristic,
    )


# type: ignore
from bless.backends.characteristic import (  # noqa: E402 F401
    GATTCharacteristicProperties,
    GATTAttributePermissions,
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
