import uuid

from uuid import UUID
from bless import (  # type: ignore
        BlessGATTCharacteristic,
        GattCharacteristicsFlags,
        GATTAttributePermissions
        )


class TestCharacteristic:
    def test_new_characteristic(self):
        """
        Test that we can generate a new underlying characteristic
        """
        char_uuid: UUID = uuid.uuid4()
        properties: GattCharacteristicsFlags = GattCharacteristicsFlags.read
        value: bytearray = bytearray(b"\x05")
        permissions: int = GATTAttributePermissions.readable
        characteristic: BlessGATTCharacteristic = BlessGATTCharacteristic.new(
            char_uuid, properties.value, value, permissions.value
        )
        assert characteristic is not None
