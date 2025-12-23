# type: ignore
import sys

if sys.platform == "darwin":

    # Server
    from bless.backends.corebluetooth.server import (  # noqa: F401
        BlessServerCoreBluetooth as BlessServer,
    )

    # Service
    from bless.backends.corebluetooth.service import (  # noqa: F401
        BlessGATTServiceCoreBluetooth as BlessGATTService
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

    # Service
    from bless.backends.bluezdbus.service import (  # noqa: F401
        BlessGATTServiceBlueZDBus as BlessGATTService
    )

    # Characteristic Classes
    from bless.backends.bluezdbus.characteristic import (  # noqa: F401
        BlessGATTCharacteristicBlueZDBus as BlessGATTCharacteristic,
    )

    # Descriptor Classes
    from bless.backends.bluezdbus.descriptor import (  # noqa: F401
        BlessGATTDescriptorBlueZDBus as BlessGATTDescriptor,
    )

elif sys.platform == "win32":

    # Server
    from bless.backends.winrt.server import (  # noqa: F401
        BlessServerWinRT as BlessServer,
    )

    # Service
    from bless.backends.winrt.service import (  # noqa: F401
        BlessGATTServiceWinRT as BlessGATTService
    )

    # Characteristic Classes
    from bless.backends.winrt.characteristic import (  # noqa: F401
        BlessGATTCharacteristicWinRT as BlessGATTCharacteristic,
    )

# type: ignore
from bless.backends.attribute import (  # noqa: E402 F401
    GATTAttributePermissions,
)

# type: ignore
from bless.backends.characteristic import (  # noqa: E402 F401
    GATTCharacteristicProperties,
)

# type: ignore
from bless.backends.descriptor import (  # noqa: E402 F401
    GATTDescriptorProperties,
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
