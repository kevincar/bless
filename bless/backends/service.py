from bleak.backends.service import BleakGATTServiceCollection, BleakGATTService

from bless.exceptions import BlessError
from bless.backends.characteristic import BlessGATTCharacteristic


class BlessGATTServiceCollection(BleakGATTServiceCollection):
    """
    Container for storing and accessing the server's services and characteristics
    """

    def __init__(self):
        super(BlessGATTServiceCollection, self).__init__()

    def add_service(self, service: BleakGATTService):
        """
        Adds a service to the collection

        Parameters
        ----------
        service : BleakGATTService
            The service to store
        """
        if service.uuid not in self._BleakGATTServiceCollection__services:
            self._BleakGATTServiceCollection__services[service.uuid] = service
        else:
            raise BlessError(
                "This service is already present in this BlessGATTServiceCollection"
            )

    def add_characteristic(self, characteristic: BlessGATTCharacteristic):
        """
        Adds a characteristic to the service collection

        Parameters
        ----------
        characteristic : BlessGATTCharacteristic
            The characteristic to add to the service collection
        """
        if characteristic.uuid not in self._BleakGATTServiceCollection__characteristics:
            self._BleakGATTServiceCollection__characteristics[
                characteristic.uuid
            ] = characteristic
        else:
            raise BlessError(
                "This characteristic is already ",
                "present in this BlessGATTServiceCollection",
            )
