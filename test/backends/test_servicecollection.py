import uuid

from bless import (  # type: ignore
    BlessGATTService,
    BlessGATTCharacteristic,
    GattCharacteristicsFlags,
    GATTAttributePermissions,
)

from bless.backends.service import BlessGATTServiceCollection


class TestBlessGATTServiceCollection:
    """
    Test specifications for the BlessGATTServiceCollection
    """

    def test_service(self):
        """
        Test that we can add and retreive a service
        """
        service_collection: BlessGATTServiceCollection = BlessGATTServiceCollection()
        service_uuid: str = str(uuid.uuid4())

        # Create a Service
        service: BlessGATTService = BlessGATTService.new(service_uuid)

        # Add the service
        service_collection.add_service(service)

        # Get the service
        observed_service: BlessGATTService = service_collection.get_service(
            service_uuid
        )

        # Test uuid equipvlance
        assert observed_service.uuid == service.uuid

    def test_characteristic(self):
        """
        Test that we can add and get a characteristic
        """
        service_collection: BlessGATTServiceCollection = BlessGATTServiceCollection()
        char_uuid: str = str(uuid.uuid4())

        # Create a characteristic
        characteristic: BlessGATTCharacteristic = BlessGATTCharacteristic.new(
            char_uuid,
            GattCharacteristicsFlags.read.value,
            bytearray(b"\x05"),
            GATTAttributePermissions.readable.value,
        )

        # Add the characteristic
        service_collection.add_characteristic(characteristic)

        # Get the characteristic
        observed_characteristic: BlessGATTCharacteristic = (
            service_collection.get_characteristic(char_uuid)
        )

        # Test uuid equivlance
        assert observed_characteristic.uuid == characteristic.uuid
