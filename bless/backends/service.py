import abc

from uuid import UUID
from typing import Union, cast
from bleak.backends.service import BleakGATTService  # type: ignore


class BlessGATTService(BleakGATTService):
    """
    GATT Service object for Bless
    """

    def __init__(self, uuid: Union[str, UUID]):
        """
        Instantiates a new GATT Service but is not yet assigned to any
        application

        Parameters
        ----------
        uuid : Union[str, UUID]
            The uuid of the service
        """
        if type(uuid) is str:
            uuid_str: str = cast(str, uuid)
            uuid = UUID(uuid_str)
        self._uuid: str = str(uuid)

    @abc.abstractmethod
    async def init(self):
        """
        Initialize the backend specific service object
        """
        raise NotImplementedError()
