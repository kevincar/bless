import uuid

from uuid import UUID
from bless import BlessGATTService  # type: ignore


class TestService:
    def test_new_service(self):
        """
        Tests that we can generate a new underlying service
        """
        service_uuid: UUID = uuid.uuid4()
        service: BlessGATTService = BlessGATTService.new(service_uuid)
        assert service is not None
