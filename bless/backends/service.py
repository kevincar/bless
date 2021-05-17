import abc

from uuid import UUID
from typing import Union, cast, TYPE_CHECKING
from bleak.backends.service import BleakGATTService  # type: ignore

if TYPE_CHECKING:
    from bless.backends.server import BaseBlessServer


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
    async def init(self, server: "BaseBlessServer"):
        """
        Initialize the backend specific service object

        Parameteres
        -----------
        server: BlessServer
            The server to assign the service to
        """
        raise NotImplementedError()
