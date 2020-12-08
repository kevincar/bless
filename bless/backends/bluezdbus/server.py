from asyncio import AbstractEventLoop
from bless.backends.server import BaseBlessServer


class BlessServerBlueZDBus(BaseBlessServer):
    """
    The BlueZ DBus implementation of the Bless Server

    Attributes
    ----------
    name : str
        The name of the server that will be advertised]

    """

    def __init__(self, name: str, loop: AbstractEventLoop = None, **kwargs):
        super(BlessServerBlueZDBus, self).__init__(loop=loop, **kwargs)
