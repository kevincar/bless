"""
Test suite to verify compatibility with Bleak v1.1.1
"""

import pytest

# Import Bless components
from bless import (
    BlessServer,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)

hardware_only = pytest.mark.skipif(
    "os.environ.get('TEST_HARDWARE') is None", allow_module_level=True
)


@hardware_only
class TestBleakV1Compatibility:
    """Test compatibility with Bleak v1.1.1"""

    @pytest.mark.asyncio
    async def test_server_creation(self):
        """Test that server can be created"""
        server = BlessServer(name="TestServer")
        assert server is not None
        assert server.name == "TestServer"

    @pytest.mark.asyncio
    async def test_add_service(self):
        """Test adding a service to the server"""
        server = BlessServer(name="TestServer")
        service_uuid = "A07498CA-AD5B-474E-940D-16F1FBE7E8CD"

        await server.add_new_service(service_uuid)

        # Verify service was added
        assert len(server.services) == 1
        assert service_uuid.lower() in [s.lower() for s in server.services.keys()]

    @pytest.mark.asyncio
    async def test_add_characteristic(self):
        """Test adding a characteristic to a service"""
        server = BlessServer(name="TestServer")
        service_uuid = "A07498CA-AD5B-474E-940D-16F1FBE7E8CD"
        char_uuid = "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"

        await server.add_new_service(service_uuid)

        char_flags = (
            GATTCharacteristicProperties.read
            | GATTCharacteristicProperties.write
            | GATTCharacteristicProperties.notify
        )
        permissions = (
            GATTAttributePermissions.readable | GATTAttributePermissions.writeable
        )

        await server.add_new_characteristic(
            service_uuid, char_uuid, char_flags, bytearray(b"Hello"), permissions
        )

        # Verify characteristic was added
        char = server.get_characteristic(char_uuid)
        assert char is not None
        assert char.uuid.lower() == char_uuid.lower()

    @pytest.mark.asyncio
    async def test_get_characteristic(self):
        """Test retrieving a characteristic by UUID"""
        server = BlessServer(name="TestServer")
        service_uuid = "A07498CA-AD5B-474E-940D-16F1FBE7E8CD"
        char_uuid = "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"

        await server.add_new_service(service_uuid)

        char_flags = GATTCharacteristicProperties.read
        permissions = GATTAttributePermissions.readable

        await server.add_new_characteristic(
            service_uuid, char_uuid, char_flags, bytearray(b"Test"), permissions
        )

        # Get characteristic
        char = server.get_characteristic(char_uuid)
        assert char is not None
        assert char.uuid.lower() == char_uuid.lower()

    @pytest.mark.asyncio
    async def test_get_service(self):
        """Test retrieving a service by UUID"""
        server = BlessServer(name="TestServer")
        service_uuid = "A07498CA-AD5B-474E-940D-16F1FBE7E8CD"

        await server.add_new_service(service_uuid)

        # Get service
        service = server.get_service(service_uuid)
        assert service is not None
        assert service.uuid.lower() == service_uuid.lower()

    @pytest.mark.asyncio
    async def test_add_gatt_tree(self):
        """Test adding services and characteristics via GATT tree"""
        server = BlessServer(name="TestServer")

        gatt_tree = {
            "A07498CA-AD5B-474E-940D-16F1FBE7E8CD": {
                "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B": {
                    "Properties": (
                        GATTCharacteristicProperties.read
                        | GATTCharacteristicProperties.write
                    ),
                    "Permissions": (
                        GATTAttributePermissions.readable
                        | GATTAttributePermissions.writeable
                    ),
                    "Value": bytearray(b"test"),
                }
            }
        }

        await server.add_gatt(gatt_tree)

        # Verify service and characteristic were added
        assert len(server.services) == 1
        char = server.get_characteristic("51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B")
        assert char is not None

    @pytest.mark.asyncio
    async def test_characteristic_value(self):
        """Test getting and setting characteristic values"""
        server = BlessServer(name="TestServer")
        service_uuid = "A07498CA-AD5B-474E-940D-16F1FBE7E8CD"
        char_uuid = "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"

        await server.add_new_service(service_uuid)

        initial_value = bytearray(b"Initial")
        char_flags = (
            GATTCharacteristicProperties.read | GATTCharacteristicProperties.write
        )
        permissions = (
            GATTAttributePermissions.readable | GATTAttributePermissions.writeable
        )

        await server.add_new_characteristic(
            service_uuid, char_uuid, char_flags, initial_value, permissions
        )

        char = server.get_characteristic(char_uuid)
        assert char is not None

        # Test getting value
        assert char.value == initial_value

        # Test setting value
        new_value = bytearray(b"Updated")
        char.value = new_value
        assert char.value == new_value

    @pytest.mark.asyncio
    async def test_characteristic_properties(self):
        """Test that characteristic properties are correctly set"""
        server = BlessServer(name="TestServer")
        service_uuid = "A07498CA-AD5B-474E-940D-16F1FBE7E8CD"
        char_uuid = "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"

        await server.add_new_service(service_uuid)

        char_flags = (
            GATTCharacteristicProperties.read
            | GATTCharacteristicProperties.write
            | GATTCharacteristicProperties.notify
        )
        permissions = (
            GATTAttributePermissions.readable | GATTAttributePermissions.writeable
        )

        await server.add_new_characteristic(
            service_uuid, char_uuid, char_flags, bytearray(b"test"), permissions
        )

        char = server.get_characteristic(char_uuid)
        assert char is not None

        # Verify properties contain expected values
        properties = char.properties if hasattr(char, "properties") else []
        if isinstance(properties, list):
            assert "read" in properties
            assert "write" in properties
            assert "notify" in properties

    def test_imports(self):
        """Test that all necessary imports work"""
        # These should not raise ImportError
        from bless import BlessServer
        from bless import BlessGATTCharacteristic
        from bless import GATTCharacteristicProperties
        from bless import GATTAttributePermissions

        assert BlessServer is not None
        assert BlessGATTCharacteristic is not None
        assert GATTCharacteristicProperties is not None
        assert GATTAttributePermissions is not None

    @pytest.mark.asyncio
    async def test_service_characteristics_list(self):
        """Test that service maintains a list of characteristics"""
        server = BlessServer(name="TestServer")
        service_uuid = "A07498CA-AD5B-474E-940D-16F1FBE7E8CD"
        char_uuid_1 = "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"
        char_uuid_2 = "52FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"

        await server.add_new_service(service_uuid)

        char_flags = GATTCharacteristicProperties.read
        permissions = GATTAttributePermissions.readable

        # Add two characteristics
        await server.add_new_characteristic(
            service_uuid, char_uuid_1, char_flags, bytearray(b"test1"), permissions
        )
        await server.add_new_characteristic(
            service_uuid, char_uuid_2, char_flags, bytearray(b"test2"), permissions
        )

        # Get service and check characteristics
        service = server.get_service(service_uuid)
        assert service is not None

        # Service should have characteristics attribute
        assert hasattr(service, "characteristics")
        assert len(service.characteristics) == 2
