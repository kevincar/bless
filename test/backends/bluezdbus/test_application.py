import pytest
import asyncio

from txdbus import client

from bless.backends.bluezdbus.application import BlueZGattApplication

from twisted.internet.asyncioreactor import AsyncioSelectorReactor


class TestBlueZGattApplication:
    """
    Test
    """

    @pytest.mark.asyncio
    async def test_init(self):
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

        reactor: AsyncioSelectorReactor = AsyncioSelectorReactor(loop)
        bus: client = await client.connect(reactor, "system").asFuture(loop)

        app: BlueZGattApplication = BlueZGattApplication(
                "ble", "org.bluez.testapp", bus, loop
                )

        bus.exportObject(app)
        await bus.requestBusName(app.destination).asFuture(loop)

        response = await bus.callRemote(
                app.path,
                "GetManagedObjects",
                interface="org.freedesktop.DBus.ObjectManager",
                destination=app.destination
                ).asFuture(loop)

        assert response == {}
