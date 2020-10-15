import sys
import uuid
import pytest
import logging
import asyncio
import aioconsole

from typing import Dict, Any

if sys.platform.lower() != "darwin":
    pytest.skip("Only for MacOS", allow_module_level=True)

from CoreBluetooth import (  # noqa: E402
        CBUUID,
        CBMutableCharacteristic
        )

from bleaks.backends.characteristic import (  # noqa: E402
        GattCharacteristicsFlags
        )

from bleaks.backends.corebluetooth.PeripheralManagerDelegate import (  # noqa: E402 E501
        PeripheralManagerDelegate,
        CBMutableService,
        )

from bleaks.backends.corebluetooth.characteristic import (  # noqa: E402
        CBAttributePermissions
        )

hardware_only = pytest.mark.skipif("os.environ.get('TEST_HARDWARE') is None")
logging.basicConfig(level=logging.DEBUG)


@hardware_only
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

        def read(char_id: str):
            print("READ")

        def write(char_id: str, value: bytearray):
            print("WRITE")

        pmd.read_request_func = read
        pmd.write_request_func = write

        service_id: str = str(uuid.uuid4())
        char_id: str = str(uuid.uuid4())

        async def setup():
            await pmd.wait_for_powered_on(5)
            # Setup Service
            cbid: CBUUID = CBUUID.alloc().initWithString_(service_id)
            service: CBMutableService = (
                    CBMutableService.alloc().initWithType_primary_(cbid, True)
                    )

            # Add a subscribable Characteristic
            props: GattCharacteristicsFlags = (
                    GattCharacteristicsFlags.read |
                    GattCharacteristicsFlags.write |
                    GattCharacteristicsFlags.notify
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

            # Verify that we're not yet advertising
            assert pmd.is_advertising() is False

            # Start Advertising
            advertisement_data: Dict[str, Any] = {
                    "kCBAdvDataServiceUUIDs": [cbid],
                    "kCBAdvDataLocalName": "TestPeripheral"
                    }

            try:
                await pmd.startAdvertising_(advertisement_data, timeout=5)
            except asyncio.exceptions.TimeoutError:
                await setup()

        await setup()

        assert pmd.is_advertising() is True

        # Test Connection

        assert pmd.is_connected() is False

        print(
                "Please connect now and subscribe to the characterisitc {}..."
                .format(char_id)
                )
        await aioconsole.ainput("Press entry when ready...")

        assert pmd.is_connected() is True
