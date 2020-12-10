import sys
import uuid
import pytest
import asyncio
import aioconsole

if sys.platform.lower() != "linux":
    pytest.skip("Only for linux", allow_module_level=True)

from typing import List

from txdbus import client
from txdbus.objects import RemoteDBusObject

from bless.backends.bluezdbus.characteristic import Flags
from bless.backends.bluezdbus.utils import get_adapter
from bless.backends.bluezdbus.application import BlueZGattApplication

from twisted.internet.asyncioreactor import AsyncioSelectorReactor

hardware_only = pytest.mark.skipif("os.environ.get('TEST_HARDWARE') is None")


@hardware_only
class TestBlueZGattApplication:
    """
    Test
    """

    @pytest.mark.asyncio
    async def test_init(self):
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

        reactor: AsyncioSelectorReactor = AsyncioSelectorReactor(loop)
        bus: client = await client.connect(reactor, "system").asFuture(loop)

        # Create the app
        app: BlueZGattApplication = BlueZGattApplication(
                "ble", "org.bluez.testapp", bus, loop
                )

        # Add a service
        service_uuid: str = str(uuid.uuid4())
        await app.add_service(service_uuid)

        # Add a characteristic
        char_uuid: str = str(uuid.uuid4())
        flags: List[Flags] = [Flags.READ]
        await app.add_characteristic(
                service_uuid, char_uuid, bytearray(b'1'), flags
                )

        # Validate the app
        bus.exportObject(app)
        await bus.requestBusName(app.destination).asFuture(loop)

        response = await bus.callRemote(
                app.path,
                "GetManagedObjects",
                interface="org.freedesktop.DBus.ObjectManager",
                destination=app.destination
                ).asFuture(loop)

        assert response == {
                '/org/bluez/ble/service1': {
                    'org.bluez.GattService1': {
                        'Primary': True,
                        'UUID': service_uuid
                        },
                    'org.freedesktop.DBus.Properties': {}
                    },
                '/org/bluez/ble/service1/char1': {
                    'org.bluez.GattCharacteristic1': {
                        'Flags': ['read'],
                        'Service': '/org/bluez/ble/service1',
                        'UUID': char_uuid,
                        'Value': [49]
                        },
                    'org.freedesktop.DBus.Properties': {}
                    }
                }

        # Register the Application
        adapter: RemoteDBusObject = await get_adapter(bus, loop)
        await app.register(adapter)

        # Advertise
        await app.start_advertising(adapter)

        # Check
        # value: bool = await app.is_advertising(adapter)

        print(
                "\nPlease connect now" +
                "and subscribe to the characteristic {}..."
                .format(char_uuid)
                )
        await aioconsole.ainput("Press enter when ready...")

        # Stop Advertising
        await app.stop_advertising(adapter)
