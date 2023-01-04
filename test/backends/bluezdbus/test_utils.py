import sys
import pytest

from typing import List

if sys.platform.lower() != "linux":
    pytest.skip("Only for linux", allow_module_level=True)

from dbus_next.aio import MessageBus
from dbus_next.constants import BusType

from bless.backends.bluezdbus.dbus.utils import list_adapters

hardware_only = pytest.mark.skipif("os.environ.get('TEST_HARDWARE') is None")


@hardware_only
class TestUtils:

    @pytest.mark.asyncio
    async def test_list_adapters(self):
        bus: MessageBus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        adapters: List[str] = await list_adapters(bus)
        assert len(adapters) > 0
