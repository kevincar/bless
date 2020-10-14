import uuid
import pytest

from CoreBluetooth import (
        CBUUID,
        CBMutableCharacteristic
        )

from bleaks.backends.characteristic import GattCharacteristicsFlags

from bleaks.backends.corebluetooth.PeripheralManagerDelegate import (
        PeripheralManagerDelegate,
        CBMutableService,
        )

from bleaks.backends.corebluetooth.characteristic import CBAttributePermissions

hardware_only = pytest.mark.skipif("os.environ.get('TEST_HARDWARE') is None")
darwin_only = pytest.mark.skipif("'darwin' not in sys.platform")


@hardware_only
@darwin_only
class TestPeripheralManagerDelegate:
    """
    Test specification for CoreBluetooth PeripheralManagerDelegate

    This is a hardware specific test and cannot be automated. This test class
    exists to confirm that no breaking changes occur between updates. This test
    class will only be reached if the following environment variable is set:

    TEST_HARDWARE
    """

    peripheral_manager_delegate: PeripheralManagerDelegate

    @pytest.fixture
    def pmd(self) -> PeripheralManagerDelegate:
        return PeripheralManagerDelegate.alloc().init()

    def test_init(self, pmd: PeripheralManagerDelegate):
        # Initialization should not throw any errors
        assert pmd is not None

    @pytest.mark.asyncio
    async def test_is_advertising(self, pmd: PeripheralManagerDelegate):
        # Setup Service
        id: str = str(uuid.uuid4())
        cbid: CBUUID = CBUUID.alloc().initWithString_(id)
        service: CBMutableService = (
                CBMutableService.alloc().initWithType_primary_(cbid, True)
                )

        # Add Characteristic
        char_id: str = str(uuid.uuid4())
        props: GattCharacteristicsFlags = (
                GattCharacteristicsFlags.read |
                GattCharacteristicsFlags.write
                )
        permissions: CBAttributePermissions = (
                CBAttributePermissions.readable |
                CBAttributePermissions.writeable
                )
        cb_char_id: CBUUID = CBUUID.alloc().initWithString_(char_id)
        cb_char: CBMutableCharacteristic = (
                CBMutableCharacteristic.alloc()
                .initWithType_properties_value_permissions_(
                    cb_char_id,
                    props.value,
                    None,
                    permissions.value
                    )
                )
        service.setCharacteristics_([cb_char])

        await pmd.addService(service)
        assert pmd._services_added_events[cbid.UUIDString()].is_set()

    def test_is_connected(self, pmd: PeripheralManagerDelegate):
        # Verify that initially it should be disconnected
        assert pmd.is_connected() is False

        # Now wait for connection
        print("")
