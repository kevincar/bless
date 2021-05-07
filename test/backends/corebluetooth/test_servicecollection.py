import sys
import uuid
import pytest

if sys.platform.lower() != "darwin":
    pytest.skip("Only for MacOS", allow_module_level=True)

from CoreBluetooth import CBUUID, CBMutableService

from bless.backends.corebluetooth.service import (
    BlessGATTServiceCoreBluetooth,
    BlessGATTServiceCollectionCoreBluetooth,
)


class TestBlessGATTServiceCollection:
    """
    Test specifications for the BlessGATTServiceCollection
    """

    def test_service(self):
        """
        Test that we can add and retreive a service
        """
        service_collection: BlessGATTServiceCollectionCoreBluetooth = (
            BlessGATTServiceCollectionCoreBluetooth()
        )
        service_uuid: str = str(uuid.uuid4())

        # Create the CoreBluetooth Service
        service_cbuuid: CBUUID = CBUUID.alloc().initWithString_(service_uuid)
        cb_service: CBMutableService = CBMutableService.alloc().initWithType_primary_(
            service_cbuuid, True
        )

        # Create a Service
        service: BlessGATTServiceCoreBluetooth = BlessGATTServiceCoreBluetooth(
            cb_service
        )

        # Add the service
        service_collection.add_service(service)

        # Get the service
        observed_service: BlessGATTServiceCoreBluetooth = (
            service_collection.get_service(service_uuid)
        )

        # Test uuid equipvlance
        assert observed_service.uuid == service.uuid
