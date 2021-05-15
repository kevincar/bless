import asyncio

import bleak.backends.bluezdbus.defs as defs  # type: ignore

from typing import Dict, Optional

from txdbus import client  # type: ignore
from txdbus.objects import RemoteDBusObject  # type: ignore


async def find_adapter(bus: client, loop: asyncio.AbstractEventLoop) -> Optional[str]:
    """
    Returns the first object that the bluez service has that has a GattManager1
    interface
    """
    bluez_obj: RemoteDBusObject = await bus.getRemoteObject(
        defs.BLUEZ_SERVICE, "/"
    ).asFuture(loop)

    om_objects: Dict = await bluez_obj.callRemote(
        "GetManagedObjects", interface=defs.OBJECT_MANAGER_INTERFACE
    ).asFuture(loop)

    for o, props in om_objects.items():
        if defs.GATT_MANAGER_INTERFACE in props.keys():
            return o

    return None


async def get_adapter(bus: client, loop: asyncio.AbstractEventLoop) -> RemoteDBusObject:
    """
    Gets the bluetooth adapter

    Returns
    -------
    DBusObject
        The adapter object
    """
    adapter_path: Optional[str] = await find_adapter(bus, loop)
    adapter_obj: RemoteDBusObject = await bus.getRemoteObject(
        defs.BLUEZ_SERVICE, adapter_path
    ).asFuture(loop)
    return adapter_obj
