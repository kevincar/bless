import sys
import uuid
import pytest
import logging
import asyncio  # type: ignore
import aioconsole  # type: ignore

import numpy as np  # type: ignore

from typing import Dict, Any, List, Optional

if sys.platform.lower() != "darwin":
    pytest.skip("Only for MacOS", allow_module_level=True)

from CoreBluetooth import (  # type: ignore # noqa: E402
        CBUUID,
        CBMutableCharacteristic
        )

from bless.backends.characteristic import (  # type: ignore # noqa: E402
        GATTCharacteristicProperties
        )

from bless.backends.corebluetooth.PeripheralManagerDelegate import (  # type: ignore # noqa: E402 E501
        PeripheralManagerDelegate,
        CBMutableService,
        )

from bless.backends.corebluetooth.characteristic import (  # type: ignore # noqa: E402 E501
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

    hex_words: List[str] = [
            'DEAD', 'FACE', 'BABE',
            'CAFE', 'FADE', 'BAD',
            'DAD', 'ACE', 'BED'
            ]
    val: bytearray = bytearray([0])

    @pytest.fixture
    def pmd(self) -> PeripheralManagerDelegate:
        return PeripheralManagerDelegate.alloc().init()

    def test_init(self, pmd: PeripheralManagerDelegate):
        # Initialization should not throw any errors
        assert pmd is not None

    @pytest.mark.asyncio
    async def test_is_advertising(self, pmd: PeripheralManagerDelegate):

        def read(char_id: str) -> bytearray:
            return self.val

        def write(char_id: str, value: bytearray):
            self.val = value

        pmd.read_request_func = read
        pmd.write_request_func = write

        service_id: str = str(uuid.uuid4())
        char_id: str = str(uuid.uuid4())
        cb_char: Optional[CBMutableCharacteristic] = None

        async def setup():
            nonlocal cb_char
            await pmd.wait_for_powered_on(5)
            # Setup Service
            cbid: CBUUID = CBUUID.alloc().initWithString_(service_id)
            service: CBMutableService = (
                    CBMutableService.alloc().initWithType_primary_(cbid, True)
                    )

            # Add a subscribable Characteristic
            props: GATTCharacteristicProperties = (
                    GATTCharacteristicProperties.read |
                    GATTCharacteristicProperties.write |
                    GATTCharacteristicProperties.notify
                    )
            permissions: CBAttributePermissions = (
                    CBAttributePermissions.readable |
                    CBAttributePermissions.writeable
                    )
            cb_char_id: CBUUID = CBUUID.alloc().initWithString_(char_id)
            cb_char = (
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
                "\nPlease connect now" +
                "and subscribe to the characterisitc {}..."
                .format(char_id)
                )
        await aioconsole.ainput("Press entry when ready...")

        assert pmd.is_connected() is True

        # Read Test
        rng: np.random._generator.Generator = np.random.default_rng()  # type: ignore # noqa E501
        hex_val: str = ''.join(rng.choice(self.hex_words, 2, replace=False))
        self.val = bytearray(
                int(f"0x{hex_val}", 16).to_bytes(
                    length=int(np.ceil(len(hex_val)/2)),
                    byteorder='big'
                    )
                )
        print("Trigger a read and enter the hex value you see below")
        entered_value = await aioconsole.ainput("Value: ")
        assert entered_value == hex_val

        # Write test
        hex_val = ''.join(rng.choice(self.hex_words, 2, replace=False))
        print(f"Set the characteristic to the following: {hex_val}")
        await aioconsole.ainput("Press enter when ready...")
        str_val: str = ''.join([hex(x)[2:] for x in self.val]).upper()
        assert str_val == hex_val

        # Notify test
        hex_val = ''.join(rng.choice(self.hex_words, 2, replace=False))
        self.val = bytearray(
                int(f"0x{hex_val}", 16).to_bytes(
                    length=int(np.ceil(len(hex_val)/2)),
                    byteorder='big'
                    )
                )

        print("A new value will be sent")
        await aioconsole.ainput("Press enter to receive the new value...")

        (pmd.peripheral_manager
            .updateValue_forCharacteristic_onSubscribedCentrals_(
                    self.val,
                    cb_char,
                    None
                    ))
        new_value: str = await aioconsole.ainput("Enter the New value: ")
        assert new_value == hex_val

        # unsubscribe
        print("Unsubscribe from the characteristic")
        await aioconsole.ainput("Press enter when ready...")
        assert pmd.is_connected() is False

        # Stop Advertising
        await pmd.stopAdvertising()
        await asyncio.sleep(2)
        assert pmd.is_advertising() is False
