import uuid
import pytest

from typing import Optional

from bleaks import BleakServer
from bleaks.backends.characteristic import (
        GattCharacteristicsFlags,
        GATTAttributePermissions
        )

hardware_only = pytest.mark.skipif("os.environ.get('TEST_HARDWARE') is None")


@hardware_only
class TestBleakServer:
    """
    Test specification for bleak server

    This is a hardware dependent test and will only run when the TEST_HARDWARE
    environment variable is set
    """

    @pytest.mark.asyncio
    async def test_server(self):
        # Initialize
        server: BleakServer = BleakServer("Test Server")

        # setup a service
        service_uuid: str = str(uuid.uuid4())
        await server.add_new_service(service_uuid)

        assert len(server.services) > 0
        print(server.services)

        # setup a characteristic for the service
        char_uuid: str = str(uuid.uuid4())
        char_flags: GattCharacteristicsFlags = (
                GattCharacteristicsFlags.read |
                GattCharacteristicsFlags.write |
                GattCharacteristicsFlags.notify
                )
        value: Optional[bytearray] = None
        permissions: GATTAttributePermissions = (
                GATTAttributePermissions.readable |
                GATTAttributePermissions.writeable
                )

        await server.add_new_characteristic(
                service_uuid,
                char_uuid,
                char_flags.value,
                value,
                permissions.value
                )

        assert server.services[service_uuid].get_characteristic(char_uuid)
