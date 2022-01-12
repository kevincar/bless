import sys
import uuid
import pytest
import aioconsole  # type: ignore

import numpy as np  # type: ignore

if sys.platform.lower() != "linux":
    pytest.skip("Only for linux", allow_module_level=True)

from typing import List, Dict, Optional, cast  # noqa: E402

from dbus_next import Message
from dbus_next.aio import MessageBus, ProxyObject
from dbus_next.constants import BusType
from dbus_next.signature import Variant

from bless.backends.bluezdbus.dbus.characteristic import Flags  # type: ignore # noqa: E402 E501
from bless.backends.bluezdbus.dbus.utils import get_adapter  # type: ignore # noqa: E402 E501
from bless.backends.bluezdbus.dbus.application import BlueZGattApplication  # type: ignore # noqa: E402 E501
from bless.backends.bluezdbus.dbus.characteristic import BlueZGattCharacteristic  # type: ignore # noqa: E402 E501

hardware_only = pytest.mark.skipif("os.environ.get('TEST_HARDWARE') is None")


@hardware_only
class TestBlueZGattApplication:
    """
    Test
    """
    hex_words: List[str] = [
            'DEAD', 'FACE', 'BABE',
            'CAFE', 'FADE', 'BAD',
            'DAD', 'ACE', 'BED'
            ]

    val: bytearray = bytearray([0])

    @pytest.mark.asyncio
    async def test_init(self):

        def read(char: BlueZGattCharacteristic) -> bytes:
            return bytes(self.val)

        def write(char: BlueZGattCharacteristic, value: bytes):
            char.Value = bytes(value)  # type: ignore
            self.val = bytearray(value)

        def notify(char: BlueZGattCharacteristic):
            return

        def stop_notify(char: BlueZGattCharacteristic):
            return

        bus: MessageBus = await MessageBus(bus_type=BusType.SYSTEM).connect()

        # Create the app
        app: BlueZGattApplication = BlueZGattApplication(
                "ble", "org.bluez.testapp", bus
                )
        app.Read = read
        app.Write = write
        app.StartNotify = notify  # type: ignore
        app.StopNotify = stop_notify  # type: ignore

        # Add a service
        service_uuid: str = str(uuid.uuid4())
        await app.add_service(service_uuid)

        # Add a characteristic
        char_uuid: str = str(uuid.uuid4())
        flags: List[Flags] = [
            Flags.READ,
            Flags.WRITE,
            Flags.NOTIFY
        ]
        await app.add_characteristic(
            service_uuid, char_uuid, b'1', flags
        )

        # Validate the app
        bus.export(app.path, app)
        await bus.request_name(app.destination)

        msg: Message = Message(
            destination=app.destination,
            path=app.path,
            interface="org.freedesktop.DBus.ObjectManager",
            member="GetManagedObjects"
        )
        response: Optional[Message] = await bus.call(msg)

        observed: Dict = cast(Message, response).body[0]
        expected: Dict = {
            '/org/bluez/ble/service0001': {
                'org.bluez.GattService1': {
                    'Primary': Variant('b', True),
                    'UUID': Variant('s', service_uuid)
                }
            },
            '/org/bluez/ble/service0001/char0001': {
                'org.bluez.GattCharacteristic1': {
                    'Flags': Variant('as', ['read', 'write', 'notify']),
                    'Notifying': Variant('b', True),
                    'Service': Variant('o', '/org/bluez/ble/service0001'),
                    'UUID': Variant('s', char_uuid),
                    'Value': Variant('ay', b'1')
                }
            },
            '/': {
                'org.bluez.testapp': {}
            }
        }
        assert observed == expected

        # Register the Application
        oadapter: Optional[ProxyObject] = await get_adapter(bus)
        adapter: ProxyObject = cast(ProxyObject, oadapter)
        await app.register(adapter)

        # Ensure we're not advertising
        assert await app.is_advertising(adapter) is False

        # Advertise
        await app.start_advertising(adapter)

        # Check
        assert await app.is_advertising(adapter) is True

        # We shouldn't be connected
        assert await app.is_connected() is False

        print(
                "\nPlease connect now" +
                "and subscribe to the characteristic {}..."
                .format(char_uuid)
                )
        await aioconsole.ainput("Press enter when ready...")

        assert await app.is_connected() is True

        # Read test
        rng: np.random._generator.Generator = np.random.default_rng()
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

        app.services[0].characteristics[0].Value = bytes(self.val)

        new_value: str = await aioconsole.ainput("Enter the New value: ")
        assert new_value == hex_val

        # unsubscribe
        print("Unsubscribe from the characteristic")
        await aioconsole.ainput("Press enter when ready...")
        assert await app.is_connected() is False

        # Stop Advertising
        await app.stop_advertising(adapter)
        assert await app.is_advertising(adapter) is False
