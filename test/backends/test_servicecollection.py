import uuid

from bless import BlessGATTService  # type: ignore
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
        observed_service: BlessGATTService = (
            service_collection.get_service(service_uuid)
        )

        # Test uuid equipvlance
        assert observed_service.uuid == service.uuid
