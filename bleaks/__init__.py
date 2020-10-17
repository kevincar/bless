import sys

if sys.platform == 'darwin':
    from bleaks.backends.corebluetooth.server import BleakServerCoreBluetooth as BleakServer  # noqa: F401 E501


def check_test() -> bool:
    """
    Verify that testing is functional

    Returns
    -------
    bool
        Default to true
    """
    return True
